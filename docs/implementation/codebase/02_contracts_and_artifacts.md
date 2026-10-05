# 02 — Contracts, Artifact Graph và Invalidation

## 1. Contract files

```text
contracts/schemas/
├── common.schema.json
├── validation-report.schema.json
├── error.schema.json
├── project.schema.json
├── script-document.schema.json
├── timing-document.schema.json
├── voice-config.schema.json
├── asset.schema.json
├── scene-plan.schema.json
├── asset-map.schema.json
├── timeline-document.schema.json
├── postprocess-config.schema.json
├── render-profile.schema.json
├── render-snapshot.schema.json
├── job.schema.json
├── domain-event.schema.json
├── webhook.schema.json
├── share-link.schema.json
└── publish-result.schema.json
```

Mọi schema dùng JSON Schema 2020-12, `camelCase`, `additionalProperties: false` trừ metadata extension được khai báo rõ.

`contracts/api/` chứa request/response DTO không phải domain artifact; OpenAPI sinh từ FastAPI phải reference hoặc round-trip được với các DTO này. Không copy lại domain fields bằng model viết tay.

## 2. Generation tools

### `contracts/scripts/generate.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `load_schemas` | `(schema_dir: Path) -> SchemaRegistry` | Load và resolve `$ref` |
| `validate_schema_set` | `(registry) -> list[Issue]` | Kiểm tra schema, duplicate IDs, cycles không hợp lệ |
| `generate_python_models` | `(registry, output_dir) -> list[Path]` | Sinh Pydantic models |
| `generate_typescript_models` | `(registry, output_dir) -> list[Path]` | Sinh TS types và runtime validators |
| `verify_generated_clean` | `(repo_root) -> None` | Fail nếu generated output khác committed files |

Generation toolchain production phải được pin trong lockfiles. Python models sinh bằng một generator đã chốt version; TypeScript types/runtime validators sinh trong cùng CI job. Không cho phép hai generator tự suy diễn default/nullability khác nhau mà không có round-trip fixtures.

## 3. Canonical JSON và hashing

Mọi `documentHash`, input fingerprint, idempotency request hash và chữ ký JSON dùng:

1. Validate document thuộc I-JSON và schema hiện hành.
2. Serialize bằng RFC 8785 JSON Canonicalization Scheme.
3. Hash canonical UTF-8 bytes bằng SHA-256.
4. Encode lowercase hexadecimal 64 ký tự.

`compute_input_fingerprint` hash một envelope cố định:

```json
{
  "kind": "TimelineDocument",
  "schemaVersion": "1.0",
  "inputs": [
    { "kind": "ScriptDocument", "id": "scr_...", "revision": 4, "documentHash": "..." }
  ],
  "config": {},
  "generator": { "name": "timeline-compiler", "version": "1.0.0" }
}
```

`inputs` sort theo `(kind, id, revision)` trước canonicalization. Không hash signed URL, timestamp quan sát, request ID hoặc field volatile.

## 4. Canonical time conversion

### `backend/app/domain/timebase.py`

| Hàm | Signature | Quy tắc |
|---|---|---|
| `ms_to_start_frame` | `(ms: int, fps: int) -> int` | `floor(ms × fps / 1000)` |
| `ms_to_end_frame` | `(ms: int, fps: int) -> int` | `ceil(ms × fps / 1000)` |
| `quantize_partition` | `(boundariesMs: Sequence[int], fps: int) -> list[int]` | Round boundary gần nhất, ép monotonic, giữ first=0 và last=totalFrames |
| `frames_to_ms` | `(frames: int, fps: int) -> int` | Round half-up để hiển thị/diagnostic |
| `validate_frame_range` | `(startFrame, endFrame, totalFrames) -> list[Issue]` | Kiểm tra half-open range |

`quantize_partition` dùng cho sentence/scene spans liền nhau để không sinh gap/overlap do làm tròn. `floor/ceil` dùng cho event độc lập cần bao phủ toàn timestamp.

## 5. Canonical geometry

Timeline object dùng:

- `box.x`, `box.y`: tọa độ normalized của anchor trên full composition.
- `box.width`, `box.height`: bounding box normalized sau fit, trước rotation.
- `anchor`: enum.
- `rotationDeg`: mặc định 0.
- `fit`: `contain | cover | fill`.
- Không lưu `scale` trong TimelineDocument; editor/compiler resolve scale thành box.
- Crop dùng `crop` normalized theo source asset, không thay đổi box semantics.

### `backend/app/domain/geometry.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `resolve_slot` | `(slot, template, profile) -> NormalizedBox` | Slot hint → box |
| `fit_asset` | `(assetSize, targetBox, fitMode, anchor) -> ResolvedTransform` | Giữ/crop aspect ratio |
| `normalized_to_pixels` | `(box, width, height) -> PixelBox` | Chuyển cho renderer |
| `validate_safe_area` | `(box, safeArea) -> list[Issue]` | Kiểm tra content bắt buộc |

## 6. Artifact record

Mỗi artifact persisted có:

- `id`, `projectId`, `kind`, `schemaVersion`.
- `revision` theo kind/project.
- `documentHash`.
- `status`: `candidate | current | stale | superseded | failed`.
- `createdBy`, `createdAt`.
- `generatorName`, `generatorVersion`.
- `inputFingerprint`.

`artifact_inputs` lưu dependency edge: output artifact → input artifact/revision/hash.

`candidate` là artifact đã hợp lệ nhưng chưa thay đổi current ref của project. Approval phải promote candidate thành `current`, supersede current artifact cũ và invalidate toàn bộ descendants chịu ảnh hưởng trong cùng transaction.

Project current ref là selection source of truth. Khi upstream thay đổi, selected downstream artifact vẫn được project tham chiếu để UI giải thích/history nhưng status chuyển `current → stale`; `get_current` phải follow project ref và trả cả stale status, không query riêng `status='current'`. Approval khóa row Project, kiểm tra precondition, đổi artifact cũ khỏi `current` trước, promote candidate, cập nhật ref và tăng project revision trong cùng transaction để không vi phạm partial unique index.

## 7. Dependency graph

```text
ScriptDocument ─┬─→ TimingDocument ─┐
                └─→ ScenePlan ──────┼─→ TimelineDocument ─→ RenderSnapshot ─→ RenderOutput
Assets ─────────────→ AssetMap ──────┘            ↑
PostprocessConfig ────────────────────────────────┘
RenderProfile ───────────────────────────────────┘
```

Timing có thể phụ thuộc Script + VoiceConfig + VoiceAsset. AssetMap phụ thuộc ScenePlan và Asset revisions.

## 8. Invalidation functions

### `backend/app/application/artifacts/invalidation.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `compute_input_fingerprint` | `(inputs: Sequence[ArtifactRef], config: Mapping, generatorVersion: str) -> str` | Hash canonical dependency set |
| `find_descendants` | `async (uow, artifactId) -> list[ArtifactRef]` | Traverse dependency graph |
| `mark_descendants_stale` | `async (uow, artifactId, reason) -> InvalidationResult` | CAS current→stale trong transaction |
| `is_artifact_current` | `async (uow, artifactId) -> bool` | So fingerprint và project current refs |
| `reuse_or_create_artifact` | `async (uow, kind, fingerprint, createFn) -> ArtifactRef` | Deduplicate deterministic output |

Quy tắc:

- Edit Script làm stale Timing, ScenePlan, AssetMap mappings liên quan, Timeline và render readiness.
- Thay Asset chỉ làm stale AssetMap/Timeline sử dụng asset đó; không làm stale Script.
- Đổi Postprocess chỉ làm stale Timeline/RenderSnapshot.
- RenderOutput không bị xóa khi upstream đổi; nó giữ project revision cũ và bị đánh `superseded` cho UI.
- Stale artifact không được dùng để tạo final render.

## 9. Structural và semantic validation

### `backend/app/domain/validation/`

| File | Hàm chính | Input |
|---|---|---|
| `schema_validator.py` | `validate_schema(document, schemaId)` | Raw JSON |
| `script_validator.py` | `validate_script(script)` | ScriptDocument |
| `timing_validator.py` | `validate_timing(timing, script)` | Timing + Script |
| `scene_validator.py` | `validate_scene_plan(scenePlan, script)` | ScenePlan |
| `timeline_validator.py` | `validate_timeline(timeline, dependencies)` | Timeline + refs |
| `render_readiness.py` | `validate_render_readiness(snapshot)` | RenderSnapshot |

Validator trả `ValidationReport {errors, warnings, infos}`; không throw cho lỗi dữ liệu dự kiến. Throw chỉ dành cho programming/infrastructure errors.

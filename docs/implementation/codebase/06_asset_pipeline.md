# 06 — Asset Ingest, Processing và Generation Pipeline

## 1. Asset states

```text
uploading → quarantined → inspecting → processing → ready
                                  ↘ rejected
processing → failed
ready → archived
```

Asset chưa `ready` không được dùng cho final render. Placeholder system asset là `ready` ngay nhưng được đánh `origin=systemPlaceholder`.

Mỗi Asset còn có rights metadata: source URL/provider, license identifier, attribution text,
commercial-use status, expiration và proof reference. Workspace policy có thể chặn final render
nếu quyền sử dụng là `unknown`, `expired` hoặc không phù hợp publish destination.

## 2. Files

```text
backend/app/application/assets/
├── ingest.py
├── inspect.py
├── process.py
├── derivatives.py
├── playback.py
├── assignment.py
├── remote_import.py
└── generation.py
backend/app/providers/image/
├── base.py
├── registry.py
└── adapters/
```

## 3. Ingest functions

### `assets/ingest.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `create_upload_session` | `async (projectId, UploadIntent, actor) -> UploadSession` | Quota, extension hint, presigned multipart |
| `complete_upload` | `async (uploadId, parts, actor) -> Asset` | Verify ownership, storage HEAD, checksum, enqueue inspect |
| `register_generated_blob` | `async (jobId, blob, provenance) -> Asset` | Ingest provider output qua cùng security path |
| `reject_asset` | `async (assetId, code, detail) -> Asset` | Terminal rejected state + cleanup policy |

## 4. Inspection

### `assets/inspect.py`

- `sniff_media_type(streamHead) -> DetectedMediaType`.
- `probe_media(blob) -> MediaMetadata`: width, height, frames, duration, codec, alpha, color profile.
- `verify_declared_size_checksum(intent, blob) -> None`.
- `scan_malware(blob) -> ScanResult`.
- `inspect_svg(blob) -> SvgInspection`: scripts, event handlers, external refs, foreignObject, animation.
- `inspect_rights_metadata(asset, policy) -> RightsReport`.
- `enforce_media_limits(metadata, workspacePolicy) -> list[Issue]`.

## 5. SVG policy

Upload SVG không bao giờ render trực tiếp trong DOM hoặc Remotion.

### `assets/process.py`

- `sanitize_svg(svgBytes, allowlistPolicy) -> SanitizedSvg` loại script, event handlers, external URLs, foreignObject và unsafe CSS.
- `rasterize_svg(sanitizedSvg, targetSizes) -> list[Derivative]`.
- Original SVG giữ private để audit/download có quyền; editor/render dùng PNG/WebP derivative.

SMIL/CSS SVG animation từ upload bị reject. Animation vector production dùng Lottie qua validator riêng.

## 6. Image processing

- `normalize_orientation(image) -> Image`.
- `convert_color_profile(image, target='sRGB') -> Image`.
- `remove_background(image, provider, options) -> Derivative`.
- `trim_transparent_bounds(image, padding) -> Image`.
- `create_thumbnail(image, size) -> Derivative`.
- `create_render_derivative(image, maxDimension, format) -> Derivative`.

### `assets/derivatives.py`

- `find_or_create_derivative(assetId, role, transformConfig, processorVersion) -> Derivative`: khóa theo input checksum + canonical config + processor version.
- `create_thumbnail(assetId, profile) -> Derivative`.
- `create_render_derivative(assetId, profile) -> Derivative`.

Original immutable. Derivative key gồm original checksum + transform config/version để dedupe.

## 7. Animated media

### GIF/video

- `transcode_video(input, profile) -> Derivative` tạo codec/browser-compatible proxy và render master.
- `analyze_loop_points(media) -> LoopMetadata`.
- `validate_playback_config(config, metadata) -> ValidationReport`.
- `extract_poster_frame(media, frame/time) -> Derivative`.

Playback modes canonical: once, loop, pingPong, count. Timeline compiler resolve thành frame mapping; renderer không tự đoán.

### Lottie

- `validate_lottie(document, policy) -> LottieReport`.
- Reject external images/fonts/scripts/expressions không hỗ trợ.
- Bundle referenced safe assets thành derivatives.
- Pin renderer version trong composition version.

## 8. Image generation

### `assets/generation.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `submit_generation_job` | `async (projectId, ImageGenRequest, actor, key) -> Job` | Capability/quota/cost consent |
| `execute_generation_job` | `async (jobId, context) -> GenerationResult` | Provider call, ingest outputs, provenance |
| `resolve_reference_assets` | `async (ids, actor, providerCaps) -> list[ProviderInput]` | Ownership, derivative, size |
| `build_generation_prompt` | `(entity, styleGuide, pose, references) -> PromptPackage` | Prompt + negative constraints |

### Provider interface

- `generate(request: ProviderImageRequest) -> ProviderImageResult`.
- `capabilities() -> ImageCapabilities`.
- `moderate(request) -> ModerationResult` nếu provider/policy yêu cầu.

Không giả lập reference support bằng cách silently bỏ ảnh. Nếu provider không support, request fail capability validation hoặc yêu cầu user chọn provider khác.

### `assets/remote_import.py`

- `submit_remote_import(projectId, url, intent, actor, idempotencyKey) -> Job`: validate URL shape/quota và tạo job.
- `execute_remote_import(jobId, context) -> Asset`: áp dụng SSRF policy, stream/download limits rồi ingest qua cùng inspection pipeline.

## 9. Assignment

### `assets/assignment.py`

- `assign_asset(projectId, instanceId, visualState, assetId, expectedRevision, actor) -> CommitResult`.
- `auto_assign(scenePlan, assets, scoringConfig) -> AssignmentProposal`.
- `validate_asset_map(assetMap, scenePlan, assets) -> ValidationReport`.
- `find_unassigned_requirements(scenePlan, assetMap) -> list[AssetRequirement]`.

Một assignment tham chiếu asset derivative role, không local path. Thay asset invalidates Timeline phụ thuộc mapping đó.

## 10. Tests bắt buộc

- MIME spoof, path traversal filename, oversized input.
- SVG script/external URL/foreignObject.
- SSRF redirects và DNS rebinding policy cho remote import.
- Animated media duration/frame limits.
- Provider returns wrong MIME/size.
- Retry/dedupe derivative và generated outputs.
- Unauthorized cross-workspace reference asset.
- Missing/expired license và required attribution manifest.

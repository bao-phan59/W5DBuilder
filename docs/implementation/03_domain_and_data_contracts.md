# 03 — Domain và Data Contracts

## 1. Nguyên tắc chung

Mọi document canonical PHẢI có:

- `schemaVersion`, bắt đầu từ `1.0`.
- Stable ID với prefix theo loại.
- `projectId` hoặc quan hệ rõ về project.
- `createdAt`/`updatedAt` theo UTC ISO-8601 ở resource persisted.
- `revision` ở aggregate có thể chỉnh sửa.
- Không chứa local absolute path hoặc provider SDK object.

Contract executable sẽ được đặt tại `contracts/` trong M0. File này định nghĩa semantics mà schema phải thể hiện.

## 2. ID conventions

| Resource | Prefix | Ví dụ |
|---|---|---|
| Project | `prj_` | `prj_elephants` |
| Script | `scr_` | `scr_main` |
| Sentence | `sen_` | `sen_001` |
| Entity definition | `ent_` | `ent_elephant` |
| Entity instance | `ins_` | `ins_elephant_2` |
| Scene | `scn_` | `scn_003` |
| Asset | `ast_` | `ast_elephant_happy` |
| Timeline object | `obj_` | `obj_elephant_2` |
| Job | `job_` | `job_render_01` |

IDs không được mang database implementation detail. Một ID không được tái sử dụng cho resource đã xóa.

## 3. Project aggregate

Project lưu reference đến revision hiện hành của các artifact:

- Metadata: name, locale, render profile.
- Current script/timing/scene plan/asset map/timeline revision.
- Project revision.
- Lifecycle status: `draft`, `ready_for_preview`, `ready_for_render`, `archived`.
- Validation summary.

Không nhúng binary hoặc base64 media vào Project document.

## 4. ScriptDocument

ScriptDocument canonical đã bao gồm annotation keyword. Không duy trì một `script_annotated.json` riêng.

### Sentence

- Stable sentence ID và order.
- Narration text.
- Scene hint mang tính gợi ý, không phải scene ID.
- Estimated duration milliseconds.
- `emphasisRanges` dựa trên character offsets hoặc token IDs; không chỉ lưu text dễ mơ hồ.
- Optional visual text.
- Danh sách entity instructions cho câu.

### Entity definition và instance

Entity definition mô tả loại, label và visual identity chung. Entity instance đại diện một cá thể xuyên timeline.

Quy tắc:

- “Ba chú voi” tạo ba instance riêng; không dùng đồng thời một instance và `count: 3`.
- Instance phải `enter` trước khi `idle`, `move`, `emphasize` hoặc `exit`.
- Sau `exit`, instance chỉ xuất hiện lại bằng enter mới.
- `connectTo` phải tham chiếu instance tồn tại.
- Label occurrence phải khớp definition.
- Background location có thể persist qua nhiều sentence mà không lặp instruction.

## 5. TimingDocument

TimingDocument chứa:

- Audio asset ID và duration milliseconds.
- Sentence spans `[startMs, endMs)`.
- Word/token spans nếu có alignment.
- Confidence và alignment provider metadata.
- Source mode: `estimated`, `tts_native`, `forced_alignment`, `manual`.

Spans phải tăng đơn điệu, không âm và không vượt audio duration. TimingDocument không chứa animation frame; composer thực hiện chuyển đổi theo FPS.

## 6. ScenePlan

ScenePlan mô tả intent bố cục:

- Scene ID và sentence coverage.
- Active instances đầu/cuối scene.
- Background intent.
- Layout template và normalized slots.
- Object role, anchor, z-order group.
- Enter/idle/exit semantic action.
- Transition intent.

ScenePlan không chứa keyframe chi tiết và không chứa file path.

## 7. Asset và AssetMap

Asset resource gồm:

- Media type và MIME type xác thực từ content.
- Original blob reference và immutable checksum.
- Width/height/duration metadata.
- Processing status và derivatives.
- Origin: upload, generated, library, system placeholder.
- Provider provenance và prompt nếu được phép lưu.
- Ownership/project scope.

AssetMap liên kết entity instance/visual state với asset ID. Một entity có thể có nhiều pose asset nhưng mỗi mapping phải explicit.

## 8. TimelineDocument

TimelineDocument là render-ready và immutable theo revision:

- Render profile: width, height, FPS, total frames.
- Composition version.
- Background, object, text, camera, audio và effect tracks.
- Mỗi item có `[startFrame, endFrame)`.
- Position/bounding box normalized, anchor, rotation và z-index.
- Animation preset ID cùng tham số đã validate.
- Asset IDs, không phải path/URL tùy ý.

Khoảng thời gian half-open tránh một frame thuộc đồng thời hai state ngoài ý muốn. `endFrame` phải lớn hơn `startFrame`.

## 9. Coordinate contract

- `x`, `y`, `width`, `height`: normalized `0..1` trong content area.
- TimelineDocument không lưu `scale` như geometry độc lập; editor/compiler resolve authoring scale thành normalized `box.width`/`box.height`. Animation preset có thể dùng scale tương đối nội bộ nhưng output layout vẫn tuân theo box contract.
- Anchor enum: `top_left`, `top_center`, `top_right`, `center`, `bottom_left`, `bottom_center`, `bottom_right`.
- Safe-area thuộc render profile.
- Text layout dùng normalized bounding box, không chỉ named position.

Named slots như `left` hoặc `top_center` chỉ là authoring hint; ScenePlan phải resolve thành normalized placement trước TimelineDocument.

## 10. RenderJob

Job status:

```text
queued → running → succeeded
                 ↘ failed
queued/running → cancelling → cancelled
```

Job có project revision, timeline revision, render profile, progress, attempt, timestamps, structured error và output asset ID. Progress không được giảm. Retry tạo attempt mới nhưng giữ idempotency relationship.

## 11. Validation layers

1. **Structural**: type, required fields, enum, bounds.
2. **Referential**: ID references tồn tại và đúng project.
3. **Semantic**: entity lifecycle, duration totals, active scene objects.
4. **Render readiness**: asset complete, no invalid frame range, supported preset.
5. **Quality warnings**: crowding, long static span, text overflow risk.

Errors chặn bước tiếp theo; warnings vẫn cho preview nhưng phải hiển thị cho user.

## 12. Versioning và migration

- Minor additive change giữ cùng major và reader phải bỏ qua field chưa biết chỉ khi contract cho phép.
- Breaking rename/removal/semantic change tăng major.
- Persisted document luôn lưu schema version.
- Migration phải idempotent, có fixture trước/sau và không xóa artifact cũ cho đến khi verify.

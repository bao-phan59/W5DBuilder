# 01 — Scope và Quyết Định Baseline

## 1. Mục tiêu vertical slice

MVP phải chứng minh rằng một project có thể đi qua cùng một data contract từ backend đến browser preview và MP4 output:

```text
ScriptDocument
  → validate
  → ScenePlan
  → placeholder AssetMap
  → TimelineDocument
  → Remotion Player
  → Remotion render MP4
```

Golden project “Ba Chú Voi” là acceptance fixture bắt buộc. Luồng này PHẢI chạy offline, không cần API key và không phụ thuộc provider bên ngoài.

## 2. In scope cho MVP

- Project CRUD local-first.
- Import/edit/validate ScriptDocument.
- Scene planner và timeline composer deterministic cho tập preset giới hạn.
- Placeholder hoặc PNG/SVG asset.
- Canvas 16:9 và timeline playback cơ bản.
- Enter/idle/exit animation tối thiểu.
- Preview và final render dùng chung composition.
- MP4 1920×1080, 30 FPS.
- Job status cho render.
- Automated tests từ unit đến một E2E happy path.

## 3. Out of scope cho MVP

- TTS/alignment production.
- Multi-provider AI image production.
- GIF/video/Lottie đầy đủ.
- Collaboration thời gian thực.
- Template marketplace và analytics.
- Scale-out workers, multi-region hoặc Kubernetes.
- Postprocess nâng cao như LUT, green screen, particle library lớn.
- 9:16/1:1 là profile thiết kế sẵn nhưng không phải acceptance output đầu tiên.

## 4. Quyết định đã chốt

### D-01 — Contract-first

Backend, frontend và renderer PHẢI chia sẻ cùng khái niệm và version. Không module nào được tự tạo biến thể schema riêng.

### D-02 — Single render path

Remotion composition là implementation hình ảnh chuẩn. Browser preview dùng Remotion Player trên cùng component tree; không viết lại animation bằng một engine khác.

Framer Motion chỉ dùng cho UI/editor chrome. Một interaction library như Konva chỉ được thêm nếu DOM overlay không đáp ứng drag/resize.

### D-03 — Time model

- Animation canonical: integer frame.
- Audio alignment canonical: integer millisecond.
- UI có thể hiển thị giây nhưng không lưu float seconds làm nguồn sự thật.
- Mỗi TimelineDocument gắn một FPS bất biến.

### D-04 — Coordinate model

- Vị trí và kích thước logic lưu normalized theo canvas `0..1`.
- Render profile chuyển normalized coordinates sang pixel.
- Asset giữ aspect ratio theo mặc định.
- Anchor là field bắt buộc để nhân vật không “trượt chân” khi đổi profile.

### D-05 — Local-first, replaceable adapters

MVP dùng local filesystem và persistence nhẹ. Storage, database, provider và job runner đều nằm sau interface để có thể đổi sang S3/PostgreSQL/durable queue mà không đổi domain contract.

### D-06 — Mock-first external services

LLM, image generation, TTS và background removal PHẢI có mock/fixture adapter. CI không gọi dịch vụ tốn phí.

### D-07 — Scene không đồng nghĩa sentence

Sentence là narration unit. Scene là layout state. Scene planner có thể group nhiều sentence hoặc tạo nhiều event trong một scene.

### D-08 — Optimistic concurrency

Project có `revision`. Transport PHẢI gửi strong opaque ETag do server cấp qua
`If-Match`; không gửi revision thô và không dùng weak ETag. API parse ETag thành
`expectedRevision` nội bộ, trả `428 PRECONDITION_REQUIRED` khi thiếu điều kiện và
`412 REVISION_PRECONDITION_FAILED` khi stale thay vì âm thầm ghi đè.

## 5. Lựa chọn chỉ áp dụng cho MVP/local

Các lựa chọn sau chỉ là phương án cho vertical slice cũ; không phải kiến trúc production:

- SQLite hay JSON repository cho local MVP.
- DOM interaction layer hay Konva cho editor.
- Render runner là subprocess trực tiếp hay local worker process.
- TTS/alignment provider đầu tiên.
- Ngưỡng chuyển từ local runner sang hạ tầng production.

Khi triển khai bản cuối, dùng trực tiếp các quyết định đã chốt ở mục 6 và bộ `codebase/`.

## 6. Production target đã chốt

Các lựa chọn ở mục 5 chỉ còn áp dụng cho giai đoạn MVP/local. Kiến trúc bản cuối đã được chốt trong
[codebase/README.md](./codebase/README.md): PostgreSQL, Redis/Celery, S3-compatible storage,
OIDC/JWT, Remotion Player/server render và JSON Schema-generated contracts.

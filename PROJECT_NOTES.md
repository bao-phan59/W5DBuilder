# W5D Builder — Project Notes

> Cập nhật: 2026-10-05  
> Giai đoạn: Design baseline 0.2  
> Trạng thái code: Prototype/scaffolding, chưa có MVP chạy end-to-end

## 1. Mục tiêu

W5D Builder hướng tới việc rút ngắn quy trình tạo video explainer/whiteboard từ ý tưởng đến video xuất bản được. Đặc trưng chính là:

- Voiceover dẫn dắt timeline.
- Entity, keyword text và camera chuyển động liên tục.
- Scene chuyển tiếp có overlap, tránh khung hình trống.
- Người dùng có thể sửa mọi quyết định tự động.
- Mọi thao tác quan trọng có contract để UI và AI agent dùng chung.

## 2. Hiện trạng xác thực

| Thành phần | Trạng thái | Bằng chứng |
|---|---|---|
| Product/design docs | Đã có, đang chuẩn hóa | `docs/01–12` |
| Implementation docs | Đã định nghĩa baseline | `docs/implementation/*` |
| Production codebase specs | Đã mô tả chi tiết | `docs/implementation/codebase/*` |
| Skill tạo kịch bản | Contract 1.0 đã chuẩn hóa, chưa integration | `.agents/skills/w5d-script` |
| Image generator abstraction | Prototype, chưa integration-test | `backend/app/services/image_gen/generators.py` |
| FastAPI application | Chưa có | Chưa có `backend/app/main.py` |
| Database/storage layer | Chưa có | Chưa có models, migrations, repository |
| Scene/timeline engine | Chưa có | Chỉ có design docs |
| Render engine | Chưa có | Chưa có Remotion project |
| Frontend editor | Chưa có | Frontend vẫn là Vite starter |
| Automated tests/CI | Chưa có | Chưa có test suite/workflow |

Không xem một tính năng là hoàn thành chỉ vì đã có mô tả, dependency hoặc class prototype.

## 3. Quyết định baseline

1. **Làm vertical slice trước**: sample script → placeholder preview → MP4.
2. **Một contract dữ liệu có version** dùng chung cho backend, frontend và renderer.
3. **Một đường render**: preview và final dùng cùng composition; editor chỉ thêm lớp tương tác.
4. **Frame là đơn vị animation chuẩn**; millisecond dùng cho audio alignment; giây chỉ dùng khi hiển thị.
5. **MVP 16:9, 30 FPS**; 9:16 và 60 FPS là profile mở rộng.
6. **Local-first chỉ ở MVP/dev**: bản production cuối bắt buộc PostgreSQL, Redis/Celery và S3-compatible storage theo production codebase specs.
7. **Mock-first cho tích hợp tốn phí**: mọi luồng E2E phải chạy được mà không cần API key.
8. **Docs design và docs implementation tách riêng**; implementation docs là chuẩn kỹ thuật.

Chi tiết quyết định nằm tại [docs/implementation/01_scope_and_decisions.md](./docs/implementation/01_scope_and_decisions.md).
Blueprint production ở mức file/hàm nằm tại [docs/implementation/codebase/README.md](./docs/implementation/codebase/README.md).

## 4. Phạm vi MVP

### Có trong MVP

- Import hoặc nhập một `ScriptDocument` hợp lệ.
- Scene planning deterministic từ fixture.
- Placeholder asset cho từng entity.
- Canvas preview, play/pause/scrub và timeline cơ bản.
- Enter/idle/exit presets tối thiểu.
- Preview và render dùng chung timeline.
- Render MP4 16:9, 30 FPS.
- Validation cấu trúc và validation ngữ nghĩa.
- Một golden project “Ba Chú Voi” chạy end-to-end.

### Không có trong MVP đầu tiên

- Nhiều AI image provider hoạt động production.
- TTS và forced alignment production.
- GIF/video/Lottie playback đầy đủ.
- PostgreSQL, Redis, Celery và S3 bắt buộc.
- Collaboration, marketplace, analytics.
- Postprocess nâng cao, color grade, green-screen removal.

## 5. Thứ tự triển khai

1. Contract và golden fixture.
2. Backend foundation và validation.
3. Scene/timeline composer deterministic.
4. Browser preview/editor tối thiểu.
5. Remotion render.
6. Test E2E và quality gate.
7. Tích hợp TTS/AI/assets nâng cao sau MVP.

Roadmap chi tiết: [docs/12_roadmap.md](./docs/12_roadmap.md).

## 6. Definition of Done chung

Một hạng mục chỉ được đánh dấu `DONE` khi:

- Code đã merge vào cấu trúc chính thức.
- Có test phù hợp với mức rủi ro.
- Contract và docs đã cập nhật.
- Chạy được từ môi trường sạch theo hướng dẫn.
- Không cần thao tác bí mật ngoài các biến môi trường đã mô tả.
- Có bằng chứng đầu ra hoặc acceptance test tương ứng.

## 7. Điểm cần xử lý khi bắt đầu code

- Adapter image hiện import config chưa tồn tại, dùng provider/model cũ và chưa thể chạy độc lập; không dùng làm production adapter.
- Contract executable đầy đủ cho các artifact ngoài ScriptDocument vẫn phải được tạo trong `contracts/` ở M0.
- Ví dụ “Ba Chú Voi” đã khớp schema/duration/ranges; semantic validator runtime vẫn phải triển khai ở M0.
- Tech stack cũ liệt kê đồng thời GSAP, Framer Motion, Konva và Remotion; baseline mới giảm còn Remotion cho playback/render, Framer Motion cho UI, và chỉ thêm interaction layer khi cần.
- Strong ETag, RFC 8785 hashing, S3 database-visibility protocol và provider lock là invariant production bắt buộc.

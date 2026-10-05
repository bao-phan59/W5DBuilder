# W5D Builder

W5D Builder là dự án xây dựng công cụ tạo video explainer/whiteboard theo luồng chuyển động liên tục, với editor trên web và backend có thể được điều khiển bởi người dùng hoặc AI agent.

## Trạng thái hiện tại

**Giai đoạn: thiết kế/contract đã chuẩn hóa; core application chưa được implement.**

Repository hiện có:

- Bộ đặc tả sản phẩm và thiết kế tại [`docs/`](./docs/README.md).
- Bộ hướng dẫn triển khai chuẩn tại [`docs/implementation/`](./docs/implementation/README.md).
- Bộ đặc tả production chi tiết theo file/module/function tại [`docs/implementation/codebase/`](./docs/implementation/codebase/README.md).
- Skill tạo ScriptDocument 1.0 tại [`.agents/skills/w5d-script/`](./.agents/skills/w5d-script/SKILL.md); schema/example đã migrate, application integration chưa có.
- Một prototype adapter sinh ảnh tại [`backend/app/services/image_gen/generators.py`](./backend/app/services/image_gen/generators.py). Prototype này chưa có FastAPI app bao quanh và chưa được xác nhận hoạt động với provider thật.
- Frontend Vite/React mặc định. Chưa có editor, canvas hay timeline của W5D Builder.

Những thành phần như FastAPI routes, project persistence, scene planner, timeline composer, Remotion renderer, TTS, job queue và editor UI mới nằm trong tài liệu thiết kế; chưa được xem là đã hoàn thành.

## Bắt đầu đọc

1. [PROJECT_NOTES.md](./PROJECT_NOTES.md) — snapshot ngắn về hiện trạng và quyết định hiện hành.
2. [docs/01_overview.md](./docs/01_overview.md) — mục tiêu sản phẩm và nguyên tắc thiết kế.
3. [docs/02_pipeline.md](./docs/02_pipeline.md) — pipeline nghiệp vụ từ ý tưởng đến video.
4. [docs/implementation/README.md](./docs/implementation/README.md) — thứ tự đọc tài liệu triển khai.
5. [docs/implementation/codebase/README.md](./docs/implementation/codebase/README.md) — blueprint codebase production.
6. [docs/12_roadmap.md](./docs/12_roadmap.md) — lộ trình và trạng thái công việc thực tế.

## Quy ước tài liệu

- `docs/01–12`: mô tả sản phẩm, UX và hành vi mong muốn; mang tính **design specification**.
- `docs/implementation/*`: quyết định kiến trúc, contract, Definition of Done và thứ tự triển khai; mang tính **normative** khi viết code.
- Khi hai lớp tài liệu khác nhau, tài liệu trong `docs/implementation/` được ưu tiên cho quyết định kỹ thuật.
- Dấu hoàn thành chỉ được dùng khi chức năng có code, test và bằng chứng chạy được theo Definition of Done.

## Mục tiêu MVP

MVP đầu tiên chỉ cần chứng minh một vertical slice:

```text
kịch bản mẫu → validate → ScenePlan → placeholder AssetMap
→ TimelineDocument → preview trong browser → render MP4
```

AI image, TTS, GIF/video/Lottie, postprocess nâng cao, collaboration và scale-out jobs được triển khai sau khi vertical slice này ổn định.

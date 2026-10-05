# W5D Builder — Documentation

> Phiên bản tài liệu: 0.2-design-baseline  
> Cập nhật: 2026-10-05  
> Trạng thái: đã chuẩn hóa phạm vi và kiến trúc; implementation chưa bắt đầu

## Cách dùng bộ tài liệu

Tài liệu được chia thành hai lớp:

### Design specifications

Các tài liệu này mô tả sản phẩm và hành vi mong muốn. Ví dụ JSON trong nhóm này mang tính minh họa, không thay thế schema chuẩn.

| File | Nội dung |
|---|---|
| [01_overview.md](./01_overview.md) | Mục tiêu, thuật ngữ và nguyên tắc sản phẩm |
| [02_pipeline.md](./02_pipeline.md) | Pipeline nghiệp vụ tổng thể |
| [03_script_engine.md](./03_script_engine.md) | Script Engine và skill thử nghiệm |
| [04_sentence_keyword.md](./04_sentence_keyword.md) | Keyword, voice và timing |
| [05_asset_manager.md](./05_asset_manager.md) | Asset library và playback mong muốn |
| [06_scene_layout.md](./06_scene_layout.md) | Scene planning và layout |
| [07_animation_system.md](./07_animation_system.md) | Animation grammar |
| [08_postprocess.md](./08_postprocess.md) | One-shot flow, transition và hậu kỳ |
| [09_render_engine.md](./09_render_engine.md) | Chiến lược preview/render |
| [10_agent_api.md](./10_agent_api.md) | Bề mặt API mong muốn cho UI/agent |
| [11_tech_stack.md](./11_tech_stack.md) | Hiện trạng và target stack |
| [12_roadmap.md](./12_roadmap.md) | Trạng thái và thứ tự triển khai |

### Implementation specifications

Nhóm này là chuẩn kỹ thuật khi triển khai:

| File | Nội dung |
|---|---|
| [implementation/README.md](./implementation/README.md) | Mục lục và quy tắc ưu tiên |
| [implementation/01_scope_and_decisions.md](./implementation/01_scope_and_decisions.md) | Scope MVP và quyết định đã chốt |
| [implementation/02_system_architecture.md](./implementation/02_system_architecture.md) | Kiến trúc runtime và boundary |
| [implementation/03_domain_and_data_contracts.md](./implementation/03_domain_and_data_contracts.md) | Domain model, artifact và versioning |
| [implementation/04_backend_implementation.md](./implementation/04_backend_implementation.md) | Cấu trúc backend và service boundary |
| [implementation/05_frontend_editor.md](./implementation/05_frontend_editor.md) | Editor state, canvas và timeline |
| [implementation/06_render_pipeline.md](./implementation/06_render_pipeline.md) | Preview/render dùng chung composition |
| [implementation/07_api_and_jobs.md](./implementation/07_api_and_jobs.md) | REST contract, jobs và errors |
| [implementation/08_testing_and_quality.md](./implementation/08_testing_and_quality.md) | Test pyramid, fixtures và quality gates |
| [implementation/09_security_and_operations.md](./implementation/09_security_and_operations.md) | Security, storage và vận hành |
| [implementation/10_delivery_plan.md](./implementation/10_delivery_plan.md) | Work packages và acceptance criteria |
| [implementation/codebase/README.md](./implementation/codebase/README.md) | Bộ đặc tả production ở mức file, module, hàm và tham số |
| [implementation/codebase/14_production_configuration.md](./implementation/codebase/14_production_configuration.md) | Cấu hình production, provider lock, limits, SLO và recovery |

## Thứ tự ưu tiên khi có mâu thuẫn

1. Contract executable trong `contracts/` khi đã được tạo.
2. Low-level specs trong `docs/implementation/codebase/`.
3. Quyết định kiến trúc trong `docs/implementation/`.
4. `PROJECT_NOTES.md` và `docs/12_roadmap.md` về trạng thái hiện tại.
5. Design specs `docs/01–11` về intent sản phẩm.
6. Ví dụ JSON và sơ đồ ASCII chỉ để minh họa.

Mọi schema executable trong tương lai phải được sinh hoặc kiểm tra từ data contract, không copy thủ công giữa nhiều tài liệu.

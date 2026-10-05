# W5D Builder — Implementation Specifications

> Phiên bản: 0.2  
> Trạng thái: Baseline để bắt đầu implementation  
> Phạm vi: MVP vertical slice đến production-readiness roadmap

## 1. Vai trò

Thư mục này định nghĩa cách W5D Builder phải được triển khai. Các design docs ở thư mục cha mô tả trải nghiệm và capability mong muốn; bộ implementation specs này chốt boundary, contract, quality gate và thứ tự delivery.

Khi có mâu thuẫn kỹ thuật, ưu tiên tài liệu trong thư mục này. Không suy ra trạng thái hoàn thành từ tài liệu: trạng thái thực tế nằm trong [`../12_roadmap.md`](../12_roadmap.md).

Đặc tả ở mức file/module/function cho hệ thống production nằm tại
[`codebase/README.md`](./codebase/README.md). Khi có khác biệt low-level,
`codebase/` được ưu tiên hơn các mô tả kiến trúc tổng quan trong thư mục này.

## 2. Từ khóa quy chuẩn

- **MUST / PHẢI**: bắt buộc để tương thích hoặc đạt Definition of Done.
- **SHOULD / NÊN**: mặc định nên làm; thay đổi cần ghi lý do.
- **MAY / CÓ THỂ**: tùy chọn, không phải điều kiện hoàn thành.
- **DEFERRED**: chủ động nằm ngoài scope hiện tại.

## 3. Thứ tự đọc

1. [01_scope_and_decisions.md](./01_scope_and_decisions.md)
2. [02_system_architecture.md](./02_system_architecture.md)
3. [03_domain_and_data_contracts.md](./03_domain_and_data_contracts.md)
4. [04_backend_implementation.md](./04_backend_implementation.md)
5. [05_frontend_editor.md](./05_frontend_editor.md)
6. [06_render_pipeline.md](./06_render_pipeline.md)
7. [07_api_and_jobs.md](./07_api_and_jobs.md)
8. [08_testing_and_quality.md](./08_testing_and_quality.md)
9. [09_security_and_operations.md](./09_security_and_operations.md)
10. [10_delivery_plan.md](./10_delivery_plan.md)
11. [codebase/README.md](./codebase/README.md) — production codebase specification chi tiết
12. [codebase/14_production_configuration.md](./codebase/14_production_configuration.md) — provider lock, operational limits, SLO và recovery defaults

## 4. Thuật ngữ chuẩn

| Thuật ngữ | Nghĩa |
|---|---|
| Project | Aggregate gốc chứa metadata và revision của các artifact |
| ScriptDocument | Kịch bản đã annotate, gồm sentences và entity definitions |
| Entity | Khái niệm dùng chung, ví dụ “voi” |
| Entity instance | Cá thể xuyên timeline, ví dụ `elephant_2` |
| Scene | Một trạng thái bố cục ổn định của canvas; không đồng nghĩa sentence |
| ScenePlan | Quyết định scene, object, slot, transition ở mức ý nghĩa |
| TimelineDocument | Dữ liệu render-ready theo frame |
| Composition | React/Remotion implementation render TimelineDocument |
| Asset | Media có metadata, ownership và processing state |
| Job | Tác vụ dài có trạng thái, progress, error và output |
| Golden project | Fixture chuẩn chạy xuyên toàn pipeline để chống regression |

Không dùng lẫn `sentence`, `scene`, `slide` và `frame`. W5D không có slide; một scene có thể chứa nhiều sentence và một sentence có thể tạo nhiều event.

## 5. Quản lý thay đổi

- Thay đổi breaking data contract PHẢI tăng major `schemaVersion` và có migration plan.
- Thay đổi kiến trúc ảnh hưởng từ hai module trở lên PHẢI có ADR ngắn trong `docs/implementation/decisions/` khi implementation bắt đầu.
- Ví dụ JSON trong design docs không phải contract executable.
- Contract executable tương lai PHẢI nằm trong `contracts/` và được CI kiểm tra với fixtures.
- Mỗi milestone chỉ đổi sang `DONE` khi đạt acceptance criteria trong [10_delivery_plan.md](./10_delivery_plan.md).

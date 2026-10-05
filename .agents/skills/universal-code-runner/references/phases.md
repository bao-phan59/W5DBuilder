# Universal Phase Decomposition & Delivery Strategies

Tài liệu hướng dẫn phân chia giai đoạn (Phases) và lập kế hoạch thực thi (Execution Batches) cho **mọi loại bài toán kỹ thuật phần mềm**.

---

## 1. Nguyên tắc cốt lõi: Vertical Slicing

Thay vì làm toàn bộ database ở tuần 1, toàn bộ API ở tuần 2 và toàn bộ UI ở tuần 3 (horizontal slicing - dễ tắc nghẽn và khó test):
**Universal Code Runner áp dụng Vertical Slicing**:
- Mỗi batch hoặc phase giải quyết một lát cắt hoàn chỉnh từ Contract/Data -> Business Logic -> Endpoint/UI -> Test.
- Mã nguồn sinh ra ở mỗi bước luôn có thể chạy được, biên dịch được và kiểm thử được ngay lập tức.

---

## 2. Chiến lược phân rã Phase theo dạng dự án

### Loại A: Greenfield Projects (Dự án xây mới từ đầu)

| Phase | Mục tiêu chính | Deliverables tiêu chuẩn | Quality Gate |
|---|---|---|---|
| **P0: Baseline & Toolchain** | Thiết lập cấu trúc repo, package manager, test runner, linter | Manifests (`package.json`, `pyproject.toml`...), configs, 1 smoke test | Lệnh test và linter chạy exit code 0 |
| **P1: Core Models & Contracts** | Định nghĩa schemas, data models, entities, DTOs, migrations | Type definitions, Pydantic/Zod schemas, DB migrations ban đầu | Schemas validate được golden fixtures và reject invalid fixtures |
| **P2: Business Logic & Storage** | Triển khai services, repositories, algorithms cốt lõi | Service classes, interfaces, in-memory/mock storage adapters | Unit tests độ phủ cao cho logic nghiệp vụ, xử lý biên |
| **P3: API & Presentation** | Endpoints HTTP, CLI commands, hoặc UI components cơ bản | Routers, controllers, handlers, views, CLI parser | Integration tests cho các endpoints/commands; status code đúng |
| **P4: Full Flow & Integration** | Ghép nối toàn bộ luồng nghiệp vụ end-to-end | Wiring các tầng, error boundary, logging, authentication | E2E happy path test; kịch bản lỗi trả về đúng định dạng |
| **P5: Production Hardening** | Cấu hình môi trường, container hóa, CI/CD, tối ưu | Dockerfile, compose, CI workflow, health check, security scan | Build image thành công, security scan không có critical CVE |

---

### Loại B: Feature Additions (Thêm tính năng vào codebase sẵn có)

| Phase | Mục tiêu chính | Deliverables tiêu chuẩn | Quality Gate |
|---|---|---|---|
| **P0: Contract & Test Fixtures** | Xác định API spec, data schemas, dữ liệu mẫu | Specs/schemas mới, golden input/output fixtures | Schemas validate độc lập |
| **P1: Logic & Tests (Test-First)** | Viết unit tests mô tả tính năng mới và triển khai logic | Service functions mới, unit test suite mới | Mọi unit test mới PASS; coverage đạt yêu cầu |
| **P2: Wiring & Exposure** | Gắn service vào Router/Controller/UI, cấu hình routes | Endpoint mới, controller action, UI hook | API test / component test PASS |
| **P3: Regression Verification** | Đảm bảo tính năng mới không làm hỏng tính năng cũ | Cập nhật documentation, chạy regression test suite | Toàn bộ existing test suite của dự án vẫn PASS |

---

### Loại C: Refactoring / Architecture Migration (Tái cấu trúc mã nguồn)

| Phase | Mục tiêu chính | Deliverables tiêu chuẩn | Quality Gate |
|---|---|---|---|
| **P0: Golden Baseline Tests** | Viết tests bao phủ hành vi hiện tại (characterization tests) | Test fixtures ghi lại output thực tế của code cũ | Baseline tests PASS trên mã nguồn cũ |
| **P1: Interface & Adapter** | Tạo interface/abstraction mới, bọc code cũ bằng adapter | Interfaces mới, adapter layer | Code cũ chạy qua adapter vẫn pass baseline tests |
| **P2: New Implementation** | Triển khai logic mới thỏa mãn interface mới | Module mới sạch sẽ, tuân thủ kiến trúc | Chạy switch implementation, toàn bộ baseline tests vẫn PASS |
| **P3: Deprecate & Clean Up** | Xóa bỏ code cũ, dọn dẹp adapter thừa | Dỡ bỏ legacy files, refactor imports | Build sạch, không còn dead code |

---

### Loại D: Bug Fixing & RCA (Điều tra & Sửa lỗi)

| Phase | Mục tiêu chính | Deliverables tiêu chuẩn | Quality Gate |
|---|---|---|---|
| **P0: Reproduce Test** | Viết 1 test tự động tái hiện chính xác lỗi (Failing Test) | File test mới trong test suite | Test FAIL đúng với triệu chứng lỗi được báo cáo |
| **P1: Root Cause Fix** | Phân tích nguyên nhân gốc và sửa đổi mã nguồn tối thiểu | Code fix trong logic module | Failing test ở P0 chuyển sang PASS |
| **P2: Regression Check** | Chạy kiểm tra toàn bộ các tính năng lân cận | Chạy full test suite của module liên quan | Không xuất hiện regression mới |

---

## 3. Quy chuẩn chia nhỏ Batch (Batch Sizing Rules)

- **Số lượng task**: 1–3 tasks có liên quan chặt chẽ trong mỗi batch.
- **Thời lượng thực thi**: Hoàn tất trong 1 lượt prompt/response để đảm bảo không bị quá tải context token.
- **Mã định danh (ID) chuẩn**:
  - Phase: `P0`, `P1`, ... (hoặc tên theo epic).
  - Batch: `P0-B01`, `P0-B02`, ...
  - Task: `P0-T01`, `P0-T02`, ...
  - Requirement: `P0-AC01`, `P0-AC02`, ...
  - Check: `CHK-P0-01`, `CHK-P0-02`, ...

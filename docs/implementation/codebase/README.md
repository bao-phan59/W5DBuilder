# W5D Builder — Production Codebase Specification

> Cấp độ: Low-level implementation specification  
> Mục tiêu: hệ thống production hoàn chỉnh, không chỉ MVP  
> Trạng thái: normative cho cấu trúc code, module boundary và function contract

## 1. Vai trò

Bộ tài liệu này chuyển kiến trúc trong `docs/implementation/` thành blueprint gần với code. Mỗi tài liệu mô tả:

- Cây thư mục và file cần có.
- Class/function cần triển khai.
- Tham số, kiểu trả về, lỗi và side effect.
- Transaction boundary và job boundary.
- Quan hệ gọi giữa các module.
- Điều kiện test và vận hành production.

Không copy nguyên code vào docs. Signature trong bảng là contract định hướng; source code và contract executable vẫn là nguồn kiểm chứng cuối cùng.

## 2. Thứ tự ưu tiên

Khi có khác biệt kỹ thuật:

1. Contract executable trong `contracts/` khi đã được tạo.
2. Bộ `docs/implementation/codebase/` này.
3. Bộ `docs/implementation/` cấp kiến trúc.
4. Design docs `docs/01–12`.

## 3. Kiến trúc production đã chốt

| Vùng | Lựa chọn |
|---|---|
| API | Python 3.12+, FastAPI, Pydantic |
| Database | PostgreSQL, SQLAlchemy async, Alembic |
| Queue | Celery với Redis broker; PostgreSQL giữ Job state chuẩn |
| Blob storage | S3-compatible; local adapter chỉ cho dev/test |
| Frontend | React, TypeScript, Vite, TanStack Query, Zustand, Radix UI |
| Video | Remotion Player + cùng Remotion composition cho server render |
| Render execution | Celery render queue gọi Node render runner bằng argument array |
| Contracts | JSON Schema 2020-12 là nguồn gốc; sinh Python/TypeScript types |
| Authentication | OIDC/JWT; workspace RBAC |
| Events | Polling + SSE cho job/project updates; webhook outbound có ký HMAC |
| Observability | Structured logs, OpenTelemetry traces, Prometheus-compatible metrics |

Heavy work không chạy bằng FastAPI `BackgroundTasks`; FastAPI cũng khuyến nghị công cụ queue như Celery cho tính toán nặng. Remotion packages phải pin cùng exact version.

## 4. Mục lục

1. [01_repository_and_runtime.md](./01_repository_and_runtime.md)
2. [02_contracts_and_artifacts.md](./02_contracts_and_artifacts.md)
3. [03_database_storage_and_jobs.md](./03_database_storage_and_jobs.md)
4. [04_backend_api_and_services.md](./04_backend_api_and_services.md)
5. [05_script_voice_pipeline.md](./05_script_voice_pipeline.md)
6. [06_asset_pipeline.md](./06_asset_pipeline.md)
7. [07_scene_timeline_pipeline.md](./07_scene_timeline_pipeline.md)
8. [08_render_and_publish_pipeline.md](./08_render_and_publish_pipeline.md)
9. [09_frontend_editor.md](./09_frontend_editor.md)
10. [10_security_and_observability.md](./10_security_and_observability.md)
11. [11_testing_ci_and_release.md](./11_testing_ci_and_release.md)
12. [12_end_to_end_execution.md](./12_end_to_end_execution.md)
13. [13_function_index.md](./13_function_index.md)
14. [14_production_configuration.md](./14_production_configuration.md)

## 5. Quy ước signature

- Python async: `function(arg: Type) -> Awaitable[Result]` được viết rút gọn `async function(...) -> Result`.
- TypeScript: `function(args: Args): Promise<Result>`.
- `Command` thay đổi state; `Query` chỉ đọc.
- Repository không commit; application service sở hữu transaction.
- Worker task mở session riêng, không reuse session của API request.
- Hàm domain thuần không đọc database, storage, clock hay network.

## 6. Definition of Done cho codebase cuối

Hệ thống chỉ được coi là production-complete khi:

- Pipeline từ idea đến publish chạy được bằng ít nhất một provider thật và bằng mock.
- Mọi artifact có provenance, input fingerprint và invalidation đúng.
- Preview/render parity được kiểm tra tự động.
- Job retry/cancel/restart không tạo output trùng hoặc corrupt state.
- Upload, remote fetch, SVG và subprocess qua security gates.
- Multi-user authorization, quota, audit, backup/restore và observability hoạt động.
- Runbook triển khai và recovery đã được diễn tập.

## 7. Tham chiếu kỹ thuật đã kiểm chứng

- [FastAPI — Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/): tác vụ tính toán nặng nên dùng queue/worker như Celery.
- [SQLAlchemy — AsyncIO](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html): `AsyncSession` không được dùng chung giữa concurrent tasks.
- [Remotion — Player](https://www.remotion.dev/docs/player): embed composition React trong editor.
- [Remotion — Renderer](https://www.remotion.dev/docs/renderer): server-side render và yêu cầu đồng bộ version packages.
- [Remotion — Building a timeline](https://www.remotion.dev/docs/building-a-timeline): Player và renderer dùng cùng component/props model.

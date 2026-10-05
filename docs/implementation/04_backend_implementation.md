# 04 — Backend Implementation

## 1. Mục tiêu

Backend cung cấp contract ổn định cho web editor và agent, đồng thời cô lập persistence, media storage và provider bên ngoài. Backend MVP phải chạy hoàn toàn bằng local/mock adapters.

## 2. Cấu trúc target

```text
backend/
├── app/
│   ├── api/              # HTTP routing, auth context, response mapping
│   ├── application/      # use cases và orchestration
│   ├── domain/           # models, invariants, validators, interfaces
│   ├── repositories/     # project/job persistence adapters
│   ├── services/         # scene, timeline, asset, provider adapters
│   ├── config.py
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── fixtures/
└── migrations/           # chỉ thêm khi dùng relational DB
```

Router không chứa business logic. Domain không import FastAPI, ORM hoặc SDK của provider.

## 3. Configuration

Configuration PHẢI:

- Đọc từ environment với typed settings.
- Fail fast nếu production thiếu secret hoặc storage config.
- Có safe defaults cho local mock mode.
- Không log API keys.
- Phân biệt `development`, `test`, `production`.
- Resolve path tương đối từ một application root xác định, không phụ thuộc current working directory.

## 4. Application services

Các use case tối thiểu:

- Create/get/update project.
- Import, validate và update script.
- Generate scene plan.
- Register/upload/inspect asset.
- Assign asset.
- Compose timeline.
- Create/cancel/get render job.

Mỗi use case nhận command/query typed và trả domain result. Transaction boundary nằm ở application service.

## 5. Repositories

Repository interface tối thiểu:

- Project repository với optimistic concurrency.
- Artifact repository cho immutable revisions.
- Asset metadata repository.
- Job repository.
- Blob storage adapter.

Local implementation phải dùng atomic write: ghi file tạm, flush, rồi rename. Không ghi trực tiếp lên artifact hiện hành.

## 6. Validation

- HTTP validation chỉ xử lý shape cơ bản.
- Domain validator xử lý lifecycle, reference và totals.
- Render-readiness validator chạy trước khi tạo render job.
- Error phải có code ổn định; không buộc client parse message.
- Validation response trả toàn bộ issue có thể thu thập an toàn trong một lần.

## 7. Provider adapters

Image/TTS/LLM provider interface phải thống nhất:

- Capability declaration: reference image, dimensions, variations, timestamps.
- Typed request/result độc lập SDK.
- Timeout, retry policy và retryable classification.
- Provider/model/version metadata.
- Cost/usage metadata nếu provider cung cấp.
- Mock adapter deterministic.

Không tuyên bố capability nếu adapter chỉ bỏ qua input. Ví dụ provider không hỗ trợ reference image phải trả capability false hoặc từ chối rõ ràng.

Live providers mặc định disabled trong local/test. Bật provider thật cần explicit configuration.

## 8. Media handling

- Upload stream ra storage; không giữ toàn file lớn trong memory.
- MIME được xác minh từ content, không tin extension.
- Tính checksum khi ingest.
- Probe dimension/duration trước khi asset chuyển sang `ready`.
- Original immutable; processing sinh derivative.
- API chỉ trả asset ID và controlled URL, không lộ local path.

## 9. Jobs

MVP có thể dùng local runner nhưng interface phải hỗ trợ durable implementation sau này.

- Job creation idempotent.
- Worker nhận immutable input snapshot.
- Cancellation cooperative.
- Retry chỉ cho lỗi retryable.
- Progress update có throttle để tránh write storm.
- Worker crash không được để job giả `running` vô hạn; cần heartbeat/timeout khi production.

## 10. Observability

Mỗi request/job có correlation ID. Structured logs tối thiểu gồm:

- timestamp, level, environment;
- request/job/project ID;
- operation và duration;
- result/error code;
- provider name, không chứa prompt/media nhạy cảm theo mặc định.

## 11. Backend Definition of Done

- OpenAPI sinh từ implementation và không có undocumented endpoint.
- Golden fixture validate được.
- Project update chống lost update bằng revision.
- Mock flow chạy không cần internet/API key.
- Unit, integration và contract tests pass.
- Error/secret/path handling đạt checklist security.

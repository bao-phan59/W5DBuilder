# 01 — Repository và Runtime Topology

## 1. Target repository

```text
W5DBuilder/
├── contracts/
│   ├── schemas/                 # JSON Schema canonical
│   ├── examples/                # valid contract fixtures
│   ├── generated/python/        # generated Pydantic models
│   ├── generated/typescript/    # generated TS types/validators
│   └── scripts/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   ├── providers/
│   │   ├── workers/
│   │   ├── config.py
│   │   └── main.py
│   ├── migrations/
│   └── tests/
├── frontend/
│   ├── src/app/
│   ├── src/api/
│   ├── src/features/
│   ├── src/editor/
│   └── src/test/
├── packages/
│   └── video/
│       ├── src/compositions/
│       ├── src/tracks/
│       ├── src/presets/
│       ├── src/validation/
│       └── src/runner/
├── infra/
│   ├── docker/
│   ├── compose/
│   ├── nginx/
│   └── monitoring/
├── docs/
├── package.json                 # npm workspaces
└── docker-compose.yml
```

Generated files không được sửa tay. CI sinh lại và fail nếu diff.

## 2. Production services

| Service | Process | Trách nhiệm |
|---|---|---|
| `web` | Static frontend/Nginx | Editor và asset delivery policy |
| `api` | Uvicorn workers | REST, SSE, auth, orchestration |
| `worker-default` | Celery worker | Script, TTS, image, asset jobs |
| `worker-render` | Celery worker riêng | Remotion/FFmpeg render jobs |
| `postgres` | PostgreSQL | Source of truth |
| `redis` | Redis | Broker, cache, rate-limit, ephemeral locks |
| `object-storage` | S3/MinIO | Original, derivative, audio, render output |
| `scheduler` | Một active Celery beat + PostgreSQL advisory lock | Cleanup, reconciliation, retry scans không chạy trùng |

API không trực tiếp chạy TTS, AI generation, FFmpeg hoặc Remotion.

## 3. Environment modules

### `backend/app/config.py`

| Symbol | Signature | Trách nhiệm |
|---|---|---|
| `Settings` | Pydantic settings model | Parse/validate toàn bộ environment |
| `load_settings` | `() -> Settings` | Cache immutable settings theo process |
| `validate_production_settings` | `(settings) -> None` | Fail fast nếu thiếu secret, TLS/storage/auth config |

Settings groups: app, database, redis, storage, auth, providers, render, limits, telemetry.

### `backend/app/main.py`

| Hàm | Tham số | Trả về | Việc làm |
|---|---|---|---|
| `create_app` | `settings: Settings | None` | `FastAPI` | Tạo app, middleware, routers, exception handlers, lifespan |
| `lifespan` | `app: FastAPI` | async context | Khởi tạo engine, telemetry, provider registry; đóng resource |

Không tạo DB session hoặc provider client ở module import time.

## 4. Dependency rules

- `domain` không import `api`, SQLAlchemy, Celery, FastAPI hoặc provider SDK.
- `application` import domain protocols và Unit of Work.
- `infrastructure` implement domain/application protocols.
- `api` chỉ map transport ↔ command/query/result.
- `workers` gọi cùng application services, không duplicate pipeline logic.
- `packages/video` chỉ nhận JSON-serializable render snapshot.

CI dùng import-boundary test để ngăn dependency đảo chiều.

## 5. Runtime IDs và clock

### `backend/app/domain/common.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `new_id` | `(kind: ResourceKind) -> str` | Tạo prefixed UUIDv7 |
| `parse_id` | `(value: str, expected: ResourceKind) -> ResourceId` | Validate prefix/UUID |
| `utc_now` | `() -> datetime` | Clock injectable qua protocol trong tests |
| `canonical_json_hash` | `(document: Mapping) -> str` | SHA-256 lowercase hex của RFC 8785 JCS bytes |

ID và time generator được inject ở application layer để tests deterministic.

Canonical documents phải thuộc I-JSON: không duplicate key, không `NaN`/infinity và số cần độ chính xác ngoài IEEE-754 phải biểu diễn bằng string theo schema. JCS giữ nguyên Unicode code points; text normalization phải chạy trước khi tạo document. Python và TypeScript dùng cùng RFC 8785 test vectors để hash không drift.

## 6. Process health

### API endpoints

- `/health/live`: process event loop hoạt động; không gọi dependency.
- `/health/ready`: kiểm tra PostgreSQL, Redis và storage metadata operation với timeout ngắn.
- `/health/version`: build SHA, schema versions, composition version; không lộ secret.

### Worker health

- Heartbeat vào Redis và database worker registry.
- Scheduler đánh dấu job `running` quá heartbeat timeout thành `orphaned`, sau đó reconciliation quyết định retry/fail.

## 7. Shutdown

- API ngừng nhận request, hoàn thành request đang xử lý, đóng clients.
- Worker ngừng nhận task mới; task render nhận cancellation deadline rồi kill process tree an toàn.
- Temp workspace được cleanup bằng job finalizer và periodic sweeper.
- Job chưa terminal không được tự đánh dấu succeeded khi process bị dừng.

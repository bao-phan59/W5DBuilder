# 07 — API và Job Contracts

> Tài liệu này giữ contract kiến trúc/MVP. Route catalog và semantics production chuẩn nằm tại [codebase/04_backend_api_and_services.md](./codebase/04_backend_api_and_services.md).

## 1. Conventions

- Base path: `/api/v1`.
- JSON dùng `camelCase`; domain/internal language có thể khác nhưng boundary phải nhất quán.
- Timestamp: UTC ISO-8601.
- ID là opaque string.
- Mutation trả resource/revision mới hoặc job.
- OpenAPI sinh từ code là API reference executable.

## 2. Resource endpoints MVP-compatible

MVP phải dùng cùng route shape với production để client không phải migrate. Nó có
thể chạy adapter local phía sau các route này.

### Projects

```text
POST   /api/v1/projects
GET    /api/v1/projects
GET    /api/v1/projects/{projectId}
PATCH  /api/v1/projects/{projectId}
```

### Script và planning

```text
PUT    /api/v1/projects/{projectId}/script
POST   /api/v1/projects/{projectId}/script-jobs
POST   /api/v1/projects/{projectId}/script-candidates/{artifactId}:approve
POST   /api/v1/projects/{projectId}/voice-jobs
POST   /api/v1/projects/{projectId}/scene-plan-jobs
POST   /api/v1/projects/{projectId}/timeline-jobs
```

### Assets

```text
POST   /api/v1/projects/{projectId}/uploads
POST   /api/v1/projects/{projectId}/uploads/{uploadId}:complete
GET    /api/v1/projects/{projectId}/assets
GET    /api/v1/assets/{assetId}
PATCH  /api/v1/assets/{assetId}
PUT    /api/v1/projects/{projectId}/asset-map
```

### Render/jobs

```text
POST   /api/v1/projects/{projectId}/render-jobs
GET    /api/v1/jobs/{jobId}
POST   /api/v1/jobs/{jobId}:cancel
GET    /api/v1/assets/{assetId}/content
```

Colon action được dùng cho operation không phải CRUD và không tạo resource độc lập rõ ràng.

## 3. Request metadata

Mutation production PHẢI hỗ trợ:

- `Idempotency-Key` cho create/job commands.
- Strong `If-Match` cho mutation có revision; weak ETag không hợp lệ.
  `expectedRevision` chỉ là tham số nội bộ sau khi parse opaque ETag.
- Correlation/request ID từ client nếu hợp lệ, nếu không server tạo.

Idempotency key được scope theo caller + endpoint + project và có TTL policy.

## 4. Response envelope

Success trả resource trực tiếp; list trả `{items, nextCursor}`. Request ID nằm trong `X-Request-ID`; không bọc binary content endpoint.

Error chuẩn:

```json
{
  "error": {
    "code": "REVISION_PRECONDITION_FAILED",
    "message": "Project was updated by another client.",
    "details": { "currentRevision": 12 },
    "requestId": "req_...",
    "retryable": false
  }
}
```

`code` ổn định cho client; `message` dành cho con người; `details` không lộ stack trace/secret.

## 5. HTTP status mapping

| Status | Dùng cho |
|---|---|
| 200/201 | Read/create/update thành công |
| 202 | Job đã được chấp nhận |
| 400 | Request semantics không hợp lệ |
| 401/403 | Authentication/authorization |
| 404 | Resource không tồn tại hoặc không visible |
| 409 | Idempotency key dùng lại với body khác hoặc state/semantic conflict |
| 412 | `If-Match` không còn khớp revision/ETag hiện tại |
| 428 | Thiếu `If-Match` bắt buộc |
| 413/415 | Upload quá lớn/sai media type |
| 422 | Structured validation issues nếu chọn convention FastAPI |
| 429 | Quota/rate limit |
| 502/503 | Provider/downstream unavailable |

## 6. Validation response

Validation issue gồm:

- `severity`: error/warning.
- `code`.
- `path` theo JSON Pointer.
- Human-readable message.
- Optional suggested fix.

API trả nhiều issues trong một lần nếu việc tiếp tục validation không gây sai lệch.

## 7. Job representation

Job có:

- ID, type, status, progress `0..1`.
- Project ID/revision.
- Created/started/completed timestamps.
- Attempt và cancellation state.
- Structured error.
- Output asset IDs.
- Optional stage như `validating`, `rendering`, `encoding`.

Job status terminal là `succeeded`, `failed`, `cancelled`. Terminal state bất biến.

## 8. Polling và events

MVP có thể dùng polling có backoff và phải dừng ở terminal state hoặc khi view bị
unmount. Production cung cấp durable SSE tại `/api/v1/events/stream`; SSE chỉ báo
thay đổi và không thay Job resource. Webhook production phải signed, retryable và
chống replay.

## 9. Agent usage

Agent dùng cùng REST operations như UI. Tool definitions phải được sinh hoặc review theo OpenAPI và:

- Không mặc định publish/final render nếu user chưa yêu cầu.
- Trả validation warnings rõ ràng.
- Dùng idempotency key cho retry.
- Không gửi local file path hoặc secret trong JSON.

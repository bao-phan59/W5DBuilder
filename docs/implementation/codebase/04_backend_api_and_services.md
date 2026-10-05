# 04 — Backend API và Application Services

## 1. API file tree

```text
backend/app/api/
├── dependencies.py
├── errors.py
├── middleware.py
├── pagination.py
└── v1/
    ├── router.py
    ├── identity.py
    ├── workspaces.py
    ├── projects.py
    ├── scripts.py
    ├── voice.py
    ├── assets.py
    ├── scenes.py
    ├── timelines.py
    ├── renders.py
    ├── jobs.py
    ├── events.py
    ├── webhooks.py
    ├── publish.py
    └── share_links.py
```

API JSON dùng `camelCase`. Success trả resource trực tiếp; list trả `{items, nextCursor}`. `X-Request-ID` nằm ở header. Error dùng envelope `{error:{code,message,details,requestId,retryable}}`.

Mutation update resource bắt buộc strong ETag, ví dụ `If-Match: "prj-20-7f3a9c"`. Không dùng weak ETag `W/` và không dùng `expectedRevision` trong body. Project/artifact mutations dùng Project ETag; cập nhật metadata asset dùng Asset ETag. Response GET/mutation trả ETag mới của resource tương ứng.

ETag là opaque token được tạo từ resource kind, revision và hash của writable
representation. Representation chứa field volatile như active job/progress phải
tách khỏi resource body có ETag hoặc tham gia hash. `If-Match` dùng strong
comparison và hỗ trợ danh sách tag hoặc `*` theo HTTP semantics. Header sai cú pháp
trả `400 INVALID_REQUEST`; không tag nào khớp trả
`412 REVISION_PRECONDITION_FAILED`.

## 2. Shared dependencies

### `dependencies.py`

| Hàm | Tham số | Trả về |
|---|---|---|
| `get_current_actor` | Bearer token | `ActorContext` |
| `require_workspace_role` | workspace ID, minimum role | authorized actor |
| `get_uow` | request scope | UnitOfWork |
| `get_services` | app state | ServiceContainer |
| `parse_if_match` | header | `VersionPrecondition {opaqueTags[], wildcard}` |
| `require_idempotency_key` | header | normalized key |

### `errors.py`

- `DomainError`: base có code/status/retryable/details.
- `map_domain_error(error) -> JSONResponse`.
- `validation_exception_handler` map Pydantic errors sang JSON Pointer issues.
- Unknown exception trả `INTERNAL_ERROR`, request ID; không trả stack.

## 3. Workspace và project services

### `backend/app/application/workspaces/service.py`

- `get_me(actor) -> IdentityView`.
- `list_workspaces(actor, cursor) -> Page[WorkspaceView]`.
- `get_workspace(workspaceId, actor) -> WorkspaceView`.
- `update_workspace(workspaceId, precondition, patch, actor) -> WorkspaceView`.
- `invite_member(workspaceId, email, role, actor, key) -> InvitationView`.
- `update_member_role(workspaceId, userId, role, precondition, actor) -> MembershipView`.
- `remove_member(workspaceId, userId, precondition, actor) -> None`.
- `get_workspace_usage(workspaceId, period, actor) -> QuotaUsageView`.
- `update_provider_config(workspaceId, command, precondition, actor) -> ProviderConfigView`.

Provider config read trả metadata/capabilities/last-four hoặc trạng thái credential, không bao giờ trả secret. Invitation token chỉ lưu hash và có single-use expiry.

### `backend/app/application/projects/service.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `create_project` | `async (CreateProjectCommand, ActorContext) -> ProjectView` | Tạo project và default profile/config |
| `get_project` | `async (projectId, ActorContext) -> ProjectView` | Authorization + current artifact refs |
| `update_project` | `async (projectId, revision, ProjectPatch, actor) -> ProjectView` | CAS update + audit |
| `archive_project` | `async (projectId, revision, actor) -> ProjectView` | Soft archive, cancel queued jobs |
| `restore_project` | `async (projectId, revision, actor) -> ProjectView` | Restore nếu retention cho phép |
| `clone_project` | `async (projectId, options, actor, idempotencyKey) -> ProjectView` | Copy refs/assets theo ownership policy |

## 4. Artifact service

### `backend/app/application/artifacts/service.py`

- `get_artifact(projectId, kind, revision?, actor) -> ArtifactView`.
- `commit_artifact(projectId, kind, document, inputs, generator, projectRevision, actor) -> CommitResult`.
- `compare_artifacts(leftId, rightId, actor) -> ArtifactDiff`.
- `list_artifact_history(projectId, kind, cursor, actor) -> Page`.
- `restore_artifact(projectId, kind, artifactId, projectRevision, actor) -> ProjectView`.

`commit_artifact` chạy schema + semantic validation, hash, insert immutable artifact, set current ref và invalidate descendants trong một transaction.

## 5. Route catalog production

Route handler names:

| File | Handlers |
|---|---|
| `identity.py` | `get_me_route` |
| `workspaces.py` | `list_workspaces_route`, `get_workspace_route`, `patch_workspace_route`, `list_members_route`, `create_invitation_route`, `patch_member_route`, `delete_member_route`, `get_usage_route`, `get_provider_config_route`, `put_provider_config_route` |
| `projects.py` | `list_projects_route`, `create_project_route`, `get_project_route`, `patch_project_route`, `clone_project_route`, `archive_project_route`, `restore_project_route` |
| `scripts.py` | `create_script_job_route`, `put_script_route`, `approve_script_route` |
| `voice.py` | `create_voice_job_route`, `get_voice_config_route` |
| `assets.py` | `create_upload_route`, `complete_upload_route`, `create_remote_import_job_route`, `list_assets_route`, `get_asset_route`, `patch_asset_route`, `archive_asset_route`, `create_processing_job_route`, `get_asset_content_route` |
| `scenes.py` | `create_scene_plan_job_route`, `get_scene_plan_route` |
| `timelines.py` | `create_timeline_job_route`, `get_timeline_route`, `put_postprocess_config_route` |
| `renders.py` | `create_render_job_route`, `list_render_outputs_route` |
| `jobs.py` | `get_job_route`, `cancel_job_route`, `retry_job_route` |
| `events.py` | `stream_events_route` |
| `webhooks.py` | `list_webhooks_route`, `create_webhook_route`, `patch_webhook_route`, `delete_webhook_route`, `rotate_webhook_secret_route`, `test_webhook_route` |
| `publish.py` | `create_export_job_route`, `get_publish_result_route` |
| `share_links.py` | `create_share_link_route`, `revoke_share_link_route` |

Handler chỉ parse dependencies/headers/body, gọi application service và map response; không mở provider/storage/subprocess trực tiếp.

### Projects/artifacts

```text
GET    /api/v1/me
GET    /api/v1/workspaces
GET    /api/v1/workspaces/{workspaceId}
PATCH  /api/v1/workspaces/{workspaceId}
GET    /api/v1/workspaces/{workspaceId}/members
POST   /api/v1/workspaces/{workspaceId}/invitations
PATCH  /api/v1/workspaces/{workspaceId}/members/{userId}
DELETE /api/v1/workspaces/{workspaceId}/members/{userId}
GET    /api/v1/workspaces/{workspaceId}/usage
GET    /api/v1/workspaces/{workspaceId}/provider-config
PUT    /api/v1/workspaces/{workspaceId}/provider-config
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/{projectId}
PATCH  /api/v1/projects/{projectId}
POST   /api/v1/projects/{projectId}:clone
POST   /api/v1/projects/{projectId}:archive
POST   /api/v1/projects/{projectId}:restore
GET    /api/v1/projects/{projectId}/artifacts/{kind}
GET    /api/v1/projects/{projectId}/artifacts/{kind}/history
POST   /api/v1/projects/{projectId}/artifacts/{kind}:restore
```

### Pipeline

Các path từ đây trở xuống đều tương đối với base path `/api/v1`.

```text
POST   /projects/{projectId}/script-jobs
PUT    /projects/{projectId}/script
POST   /projects/{projectId}/script-candidates/{artifactId}:approve
POST   /projects/{projectId}/voice-jobs
POST   /projects/{projectId}/scene-plan-jobs
POST   /projects/{projectId}/asset-generation-jobs
PUT    /projects/{projectId}/asset-map
POST   /projects/{projectId}/timeline-jobs
PUT    /projects/{projectId}/postprocess-config
POST   /projects/{projectId}/render-jobs
```

Mọi job POST yêu cầu `Idempotency-Key`. PUT artifact và approval yêu cầu `If-Match` project revision. Cùng idempotency key và cùng canonical body trả lại kết quả trước đó; cùng key nhưng body khác trả `409 IDEMPOTENCY_KEY_REUSED`.

### Assets/uploads

```text
POST   /projects/{projectId}/uploads
POST   /projects/{projectId}/uploads/{uploadId}:complete
POST   /projects/{projectId}/remote-import-jobs
GET    /projects/{projectId}/assets
GET    /assets/{assetId}
PATCH  /assets/{assetId}
POST   /assets/{assetId}:archive
POST   /assets/{assetId}/processing-jobs
GET    /assets/{assetId}/content
```

### Jobs/events

```text
GET    /jobs/{jobId}
POST   /jobs/{jobId}:cancel
POST   /jobs/{jobId}:retry
GET    /events/stream?projectId=...
```

### Webhook, export và share

```text
GET    /workspaces/{workspaceId}/webhooks
POST   /workspaces/{workspaceId}/webhooks
PATCH  /webhooks/{webhookId}
DELETE /webhooks/{webhookId}
POST   /webhooks/{webhookId}:rotate-secret
POST   /webhooks/{webhookId}:test
POST   /projects/{projectId}/export-jobs
GET    /publish-results/{publishResultId}
POST   /assets/{assetId}/share-links
POST   /share-links/{shareLinkId}:revoke
```

Baseline production publish là export asset + signed/revocable share link. Adapter publish ngoài hệ thống chỉ được bật khi có provider lock, OAuth scope, contract tests và destination-specific rights policy.

## 6. Transport contract matrix

| Operation | Success | Request contract | Concurrency/idempotency |
|---|---:|---|---|
| Create resource | `201` | Typed create command | `Idempotency-Key` khi retry có side effect |
| Read resource | `200` | Path/query | Trả strong `ETag` nếu resource mutable |
| List resource | `200` | cursor + bounded limit/filter | `{items,nextCursor}` |
| Update mutable resource | `200` | Typed patch/replace | Bắt buộc `If-Match` |
| Archive/revoke | `200` hoặc `204` theo declared response | Action command | Bắt buộc `If-Match`; key nếu retryable POST |
| Submit job | `202` | Typed job command | Bắt buộc `Idempotency-Key`; trả Job + `Location` |
| Binary content | `302` signed download hoặc `200` proxy stream | Không JSON envelope | Ownership check trước khi cấp URL |
| SSE | `200 text/event-stream` | filters + `Last-Event-ID` | Resume từ durable event sequence |

Missing required precondition trả `428 PRECONDITION_REQUIRED`; stale strong ETag trả `412 REVISION_PRECONDITION_FAILED`. Idempotent replay cùng canonical request trả lại status/body/resource location gốc và header `Idempotent-Replayed: true`.

### Stable error catalog

| HTTP | Error code | Khi dùng |
|---:|---|---|
| 400 | `INVALID_REQUEST` | Request semantics/parameter sai |
| 401 | `AUTHENTICATION_REQUIRED` | Token thiếu/không hợp lệ |
| 403 | `PERMISSION_DENIED` | Actor đã xác thực nhưng thiếu quyền |
| 404 | `RESOURCE_NOT_FOUND` | Không tồn tại hoặc policy intentionally hides existence |
| 409 | `IDEMPOTENCY_KEY_REUSED` | Cùng key nhưng canonical request khác |
| 409 | `STATE_CONFLICT` | State machine không cho operation |
| 412 | `REVISION_PRECONDITION_FAILED` | Strong ETag stale |
| 413 | `PAYLOAD_TOO_LARGE` | Vượt media/request limit |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | Detected media không hỗ trợ |
| 422 | `VALIDATION_FAILED` | Structural/referential/semantic issues |
| 428 | `PRECONDITION_REQUIRED` | Thiếu `If-Match` bắt buộc |
| 429 | `RATE_LIMITED` / `QUOTA_EXCEEDED` | Rate hoặc quota policy |
| 502 | `PROVIDER_INVALID_RESPONSE` | Downstream trả response không hợp lệ |
| 503 | `DEPENDENCY_UNAVAILABLE` | Provider/storage/broker tạm unavailable |
| 500 | `INTERNAL_ERROR` | Lỗi không dự kiến, chỉ trả diagnostic reference an toàn |

Mỗi endpoint phải khai báo request schema, response schema, permissions, side effects, event/audit output và error subset trong generated OpenAPI. CI fail nếu operation ID trùng, response thiếu schema hoặc generated client diff.

## 7. Upload protocol

`POST /uploads` nhận metadata JSON: filename display-only, size, MIME hint, SHA-256, intended use. Server trả multipart/presigned UploadSession.

Client upload trực tiếp storage rồi gọi `:complete`. Complete service xác minh object size/checksum/server MIME, tạo Asset `quarantined`, sau đó enqueue inspect/sanitize job. Asset chỉ thành `ready` sau security/media checks.

Dev local adapter có thể dùng multipart endpoint riêng, không thay production contract.

## 8. Remote import

Remote URL không được xử lý trong request. `remote-import-job`:

- validate HTTPS URL;
- DNS resolve và block private/link-local/loopback;
- kiểm tra mọi redirect;
- stream với size/time limit;
- sniff MIME/checksum;
- ingest như upload thông thường.

## 9. SSE events

### `backend/app/application/events/service.py`

- `subscribe(actor, projectIds, lastEventId) -> AsyncIterator[Event]`.
- `publish_after_commit(events) -> None` thông qua outbox.
- `authorize_event(event, actor) -> bool`.

Event types: project revision, artifact current/stale, asset state, job progress/terminal. Client vẫn phải refetch resource; SSE payload không phải source of truth.

`stream_events_route` đọc `Last-Event-ID`, phát các `domain_events` còn thiếu theo sequence rồi mới chuyển sang live stream. Redis/pub-sub chỉ dùng để đánh thức connection; database event log mới là nguồn resume. Nếu cursor cũ hơn retention, server phát `resync-required` và đóng stream để client refetch snapshot đầy đủ.

## 10. Webhooks

### `webhooks/service.py`

- `list_webhooks(workspaceId, actor, cursor) -> Page[Webhook]`.
- `create_webhook(workspaceId, url, eventTypes, actor) -> Webhook`.
- `update_webhook(webhookId, patch, precondition, actor) -> Webhook`.
- `delete_webhook(webhookId, precondition, actor) -> None`.
- `rotate_webhook_secret(webhookId, actor) -> SecretOnce`.
- `test_webhook(webhookId, actor, key) -> Job`.
- `enqueue_deliveries(events) -> int`.
- `sign_payload(secret, timestamp, body) -> signature`.
- `deliver_webhook(deliveryId) -> DeliveryResult`.

Retry có exponential backoff, max attempts, replay-safe event ID và disable threshold.

# 03 — Database, Storage và Job Runtime

## 1. Database models

```text
backend/app/infrastructure/db/models/
├── workspace.py
├── user.py
├── workspace_membership.py
├── project.py
├── artifact.py
├── artifact_input.py
├── asset.py
├── asset_derivative.py
├── upload_session.py
├── job.py
├── idempotency_record.py
├── outbox_event.py
├── domain_event.py
├── webhook.py
├── webhook_delivery.py
├── provider_credential.py
├── quota_ledger.py
├── share_link.py
├── publish_result.py
├── worker_heartbeat.py
└── audit_event.py
```

Tables quan trọng:

- `workspaces`, `users`, `workspace_memberships`: tenant boundary, role và membership lifecycle.
- `projects`: workspace, name, status, revision, current artifact IDs.
- `artifacts`: immutable JSONB document + metadata.
- `artifact_inputs`: dependency edges.
- `assets`: metadata/checksum/storage key/state.
- `asset_derivatives`: processed variants.
- `upload_sessions`: multipart state, intent, checksum, expiry và completion state.
- `jobs`: authoritative state/progress/input/output/error.
- `idempotency_records`: request hash + stored response/job.
- `outbox_events`: message cần publish, trạng thái delivery, attempt và lease.
- `domain_events`: event log bền vững, có sequence ID để resume SSE bằng `Last-Event-ID`.
- `webhooks`, `webhook_deliveries`: endpoint config và từng delivery attempt/replay state.
- `provider_credentials`: encrypted workspace credential reference; không lưu plaintext.
- `quota_ledger`: reservation/usage immutable cho provider, storage và render.
- `share_links`, `publish_results`: revoke/expiry và kết quả export/publish độc lập render asset.
- `worker_heartbeats`: worker identity, queues, build SHA và last seen.
- `audit_events`: append-only security/business audit.

Unique constraints:

- `(project_id, kind, revision)`.
- `(project_id, kind, input_fingerprint)` khi output deterministic.
- Partial unique index `(project_id, kind) WHERE status = 'current'`.
- `(workspace_id, idempotency_key, operation)`.
- `(workspace_id, user_id)` cho membership active.
- `(webhook_id, event_id)` cho delivery dedupe.
- `(job_id, snapshot_hash, output_role)` cho render output registration.
- Storage object checksum không thay ownership checks.

Mọi foreign key tenant-owned phải kiểm tra cùng `workspace_id`; không chỉ dựa vào opaque ID. Share token và provider secret chỉ lưu hash/encrypted reference. Quota reservation được tạo cùng transaction submit Job và được release/settle idempotently ở terminal transition.

### Column contract

Quy ước chung: public ID là `varchar(160)` có prefix/check constraint; revision/sequence là `bigint`; thời gian là UTC `timestamptz`; SHA-256 là `char(64)` lowercase; mutable row có `created_at`, `updated_at` và revision khi dùng ETag.

| Table | Cột bắt buộc chính |
|---|---|
| `workspaces` | `id`, `slug`, `name`, `status`, `revision`, `policy_version`, timestamps |
| `users` | `id`, `issuer`, `subject`, normalized email/display metadata, status, timestamps |
| `workspace_memberships` | `workspace_id`, `user_id`, `role`, `revision`, invited/accepted/removed timestamps |
| `projects` | `id`, `workspace_id`, name/locale/status, `revision`, render profile ref, current artifact refs, timestamps |
| `artifacts` | `id`, `workspace_id`, `project_id`, kind, schema/revision/status, `document jsonb`, document/input hashes, generator/provenance, timestamps |
| `artifact_inputs` | output artifact ID, input artifact ID/kind/revision/hash, ordinal |
| `assets` | `id`, tenant/project scope, origin/state, blob key, SHA-256, detected MIME, bytes/dimensions/duration, rights/provenance JSONB, revision, timestamps |
| `asset_derivatives` | `id`, asset ID, role, processing version, blob key/checksum/media metadata, state, timestamps |
| `upload_sessions` | `id`, workspace/project, intended metadata/checksum/bytes, storage upload/key, state, expiry/completed timestamps |
| `jobs` | `id`, workspace/project, type/state/stage/progress, input snapshot/fingerprint, attempt/max attempts, lease worker/expiry, cancel fields, output/error JSONB, retry time, timestamps |
| `idempotency_records` | workspace/actor/operation/key, canonical request hash, status/response/job ref, expiry, timestamps |
| `outbox_events` | `id`, topic/key/payload JSONB, state, attempts, lease/next attempt/sent timestamps |
| `domain_events` | monotonic `sequence`, event ID/type, workspace/project/aggregate refs, payload JSONB, occurred/expiry timestamps |
| `webhooks` | `id`, workspace, URL, encrypted secret ref/version, event filter, state, revision, timestamps |
| `webhook_deliveries` | `id`, webhook/event IDs, payload hash, attempt/state, HTTP outcome, lease/next attempt timestamps |
| `provider_credentials` | workspace/provider, encrypted envelope/KMS ref, key version, status, rotated/verified timestamps |
| `quota_ledger` | `id`, workspace/job, resource/period, entry type, reserved/actual amount, unit, idempotency ref, timestamp |
| `share_links` | `id`, workspace/asset, token hash, policy JSONB, expiry/revoked/created timestamps |
| `publish_results` | `id`, job/asset, destination, external ID/URL-safe metadata, state/error, timestamps |
| `worker_heartbeats` | worker ID, queues/build SHA/capabilities, started/last seen/draining timestamps |
| `audit_events` | monotonic ID, workspace/actor/action/resource/outcome, redacted metadata, request/IP hash, timestamp |

Không lưu signed URL, access token, plaintext share token/secret hoặc raw provider object. PostgreSQL enums chỉ dùng khi migration cost chấp nhận được; nếu dùng text + check constraint thì enum values vẫn phải được quản lý trong contract/migration.

### Index và partition contract

- Tenant list/query index luôn bắt đầu bằng `workspace_id`.
- Job dispatch: partial index `(state, next_attempt_at)` cho non-terminal jobs và `(lease_expires_at)` cho running jobs.
- Outbox/webhook claim: `(state, next_attempt_at, created_at)`.
- Domain events: `(workspace_id, sequence)` và `(project_id, sequence)`; partition/time retention nếu volume yêu cầu.
- Audit/quota ledger append-only, partition theo tháng trước khi production load test.
- JSONB GIN index chỉ thêm cho query đã đo; không index toàn document mặc định.

Cùng `Idempotency-Key`, operation và canonical request hash phải trả lại response/job đã lưu. Nếu key trùng nhưng request hash khác, trả `409 IDEMPOTENCY_KEY_REUSED`; tuyệt đối không chạy command lần hai.

## 2. Session và Unit of Work

### `backend/app/infrastructure/db/session.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `create_engine` | `(settings) -> AsyncEngine` | Pool, timeouts, health hooks |
| `session_factory` | `(engine) -> async_sessionmaker` | `expire_on_commit=False` |
| `get_session` | `() -> AsyncIterator[AsyncSession]` | Một session cho một request |

### `backend/app/application/uow.py`

| Symbol | Method | Mô tả |
|---|---|---|
| `UnitOfWork` | `__aenter__/__aexit__` | Mở/đóng transaction scope |
| | `commit()` | Commit application command |
| | `rollback()` | Rollback |
| | repositories | Workspace/membership/project/artifact/asset/job/outbox/quota/webhook/share/audit repositories |

Không share `AsyncSession` giữa concurrent asyncio tasks. Mỗi worker task và request có session riêng.

## 3. Repository functions

### `project_repository.py`

- `get(projectId, forUpdate=False) -> Project | None`
- `create(project) -> Project`
- `update_with_revision(projectId, expectedRevision, patch) -> Project`
- `set_current_artifact(projectId, kind, artifactId, expectedRevision) -> Project`
- `list(workspaceId, cursor, limit, filters) -> Page[Project]`

`update_with_revision` thực hiện compare-and-swap trong SQL và trả conflict nếu affected rows = 0.

### `artifact_repository.py`

- `insert(record, inputs) -> ArtifactRecord`
- `get(artifactId) -> ArtifactRecord | None`
- `get_current(projectId, kind) -> ArtifactRecord | None`
- `find_by_fingerprint(projectId, kind, fingerprint) -> ArtifactRecord | None`
- `mark_status(ids, fromStatus, toStatus, reason) -> int`
- `list_inputs(artifactId) -> list[ArtifactRef]`
- `list_descendants(artifactId) -> list[ArtifactRef]`

### `job_repository.py`

- `create(job) -> Job`
- `claim(jobId, workerId, leaseUntil) -> Job | None`
- `heartbeat(jobId, workerId, progress, stage, leaseUntil) -> bool`
- `schedule_retry(jobId, nextAttemptAt, error) -> Job`
- `mark_orphaned(jobId, expectedLease) -> Job | None`
- `request_cancel(jobId, actorId) -> Job`
- `finish_success(jobId, outputs) -> Job`
- `finish_failure(jobId, error) -> Job`
- `find_orphaned(now, limit) -> list[Job]`

Mọi transition kiểm tra allowed state trong một SQL update có condition.

### `outbox_repository.py`

- `insert(events) -> list[OutboxEvent]`
- `claim_batch(topic, now, limit, leaseUntil) -> list[OutboxEvent]`
- `mark_sent(eventId, publishedAt) -> None`
- `mark_retry(eventId, nextAttemptAt, safeError) -> None`
- `append_domain_event(event) -> DomainEvent`

Production PostgreSQL implementation của `claim_batch` dùng `FOR UPDATE SKIP LOCKED`. Publish có thể lặp khi worker chết sau broker acknowledgement nhưng trước `mark_sent`; consumer bắt buộc dedupe theo event ID. `append_domain_event` nằm trong cùng transaction với thay đổi aggregate để SSE không phát trạng thái chưa commit.

### `membership_repository.py`

- `list_members(workspaceId, cursor, limit) -> Page[Membership]`
- `create_invitation(workspaceId, email, role, tokenHash, expiresAt) -> Invitation`
- `accept_invitation(tokenHash, userId, now) -> Membership`
- `update_role(workspaceId, userId, role, expectedRevision) -> Membership`
- `remove_member(workspaceId, userId, expectedRevision) -> None`

Repository/service phải ngăn xóa hoặc hạ role owner cuối cùng trong transaction có lock workspace.

### `provider_credential_repository.py`

- `get_metadata(workspaceId, provider) -> CredentialMetadata | None`
- `upsert_encrypted(workspaceId, provider, envelope, actorId) -> CredentialMetadata`
- `rotate(workspaceId, provider, newEnvelope, actorId) -> CredentialMetadata`
- `revoke(workspaceId, provider, actorId) -> None`

Chỉ infrastructure secret adapter giải mã envelope; repository query/read model không bao giờ trả plaintext.

### `quota_repository.py`

- `reserve(workspaceId, jobId, resource, amount, period) -> QuotaReservation`
- `settle(reservationId, actualAmount) -> QuotaLedgerEntry`
- `release(reservationId, reason) -> QuotaLedgerEntry`
- `get_usage(workspaceId, period) -> QuotaUsage`

### `webhook_repository.py` và `share_repository.py`

- `insert_delivery(webhookId, eventId, payloadHash) -> WebhookDelivery`
- `claim_deliveries(now, limit, leaseUntil) -> list[WebhookDelivery]`
- `finish_delivery(deliveryId, outcome, nextAttemptAt?) -> WebhookDelivery`
- `create_share_link(assetId, tokenHash, expiresAt, policy) -> ShareLink`
- `revoke_share_link(linkId, revokedAt, actorId) -> ShareLink`
- `register_publish_result(jobId, destination, externalId, status) -> PublishResult`

## 4. Storage interface

### `backend/app/application/ports/blob_storage.py`

| Method | Tham số | Trả về |
|---|---|---|
| `create_upload` | workspace, contentType, size, checksum | UploadSession |
| `complete_upload` | uploadId, parts/checksum | StoredBlob |
| `open_read` | storageKey, byteRange? | Async stream |
| `put_stream` | namespace, stream, metadata | StoredBlob |
| `head` | storageKey | BlobMetadata |
| `delete` | storageKey | None |
| `create_download_url` | storageKey, ttl, disposition | Signed URL |

Production implementation dùng S3 multipart/presigned upload; local adapter ghi atomic temp→rename.

Storage keys do server tạo:

```text
workspaces/{workspaceId}/projects/{projectId}/assets/{assetId}/original/{checksum}
.../derivatives/{derivativeId}/{checksum}
.../renders/{jobId}/{outputId}.mp4
```

## 5. Job submission

### `backend/app/application/jobs/service.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `submit_job` | `async (command, actor, idempotencyKey) -> Job` | Transaction: validate, dedupe, create DB job, enqueue outbox |
| `cancel_job` | `async (jobId, actor) -> Job` | Authorization + cancel request |
| `get_job` | `async (jobId, actor) -> Job` | Scoped read |
| `retry_job` | `async (jobId, actor, idempotencyKey) -> Job` | Chỉ retryable terminal error |

Queue publish dùng transactional outbox: commit job/outbox cùng transaction, dispatcher publish Celery task rồi mark sent. Không publish task trước DB commit.

## 6. Celery tasks

### `backend/app/workers/tasks.py`

- `execute_job(jobId: str) -> None`: task entry, không nhận raw document.
- `dispatch_job(job) -> JobHandler`: chọn handler theo type.
- `with_job_lease(jobId, handler)`: claim, heartbeat, cancellation, terminal transition.
- `reconcile_orphaned_jobs()`: scheduler scan lease expired.
- `cleanup_expired_temp_objects()`: storage lifecycle.

Celery delivery là at-least-once. Handler PHẢI idempotent theo `jobId + inputFingerprint`; output ghi vào immutable object key duy nhất rồi đăng ký visibility trong database đúng một lần. Không giả định object storage có atomic rename.

Render tasks đi queue `render`; AI/TTS queue `provider`; media processing queue `media`. Visibility timeout lớn hơn hard task limit và task dùng late acknowledgement.

## 7. Job state machine

```text
queued ───────→ running ───────→ succeeded
  │               ├────────────→ failed
  │               ├────────────→ retry_wait ─→ queued
  │               ├────────────→ orphaned ───→ queued | failed
  └───────────────┴────────────→ cancelling ─→ cancelled
```

- Terminal states là `succeeded | failed | cancelled`; không được mutate lại.
- `queued` có thể thành `cancelled` trực tiếp nếu chưa worker nào claim.
- Automatic retry giữ nguyên Job ID, tăng `attempt` và giữ nguyên input snapshot/fingerprint.
- Manual `retry_job` tạo Job mới có `retryOfJobId`; idempotency key ngăn tạo nhiều retry jobs.
- `succeeded` chỉ được set trong transaction đăng ký đủ output; progress không bao giờ giảm trong cùng attempt.
- Mọi transition là compare-and-swap theo current state, worker ID và lease khi có.

## 8. Job error model

`JobError` fields:

- stable `code`;
- safe `message`;
- `stage`;
- `retryable`;
- optional provider HTTP/status category;
- internal diagnostic reference, không phải stack trace trả client.

Worker lưu full exception trong telemetry/error tracker có redaction; database chỉ lưu safe summary.

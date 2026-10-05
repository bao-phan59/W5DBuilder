# 10 — Security, Authorization và Observability Codebase

## 1. Authentication files

```text
backend/app/security/
├── auth.py
├── jwt.py
├── permissions.py
├── rate_limit.py
├── content_policy.py
├── url_policy.py
└── audit.py
```

### Functions

- `verify_access_token(token, jwksCache, audience, issuer) -> Principal`.
- `resolve_actor(principal, workspaceId?) -> ActorContext`.
- `authorize(actor, action, resource) -> AuthorizationDecision`.
- `require_permission(actor, action, resource) -> None`.
- `compute_quota_usage(workspaceId, period) -> QuotaUsage`.
- `enforce_rate_limit(key, policy) -> RateLimitResult`.

JWKS cache có refresh/rotation; không accept algorithm từ token ngoài allowlist. Service-to-service task dùng signed internal identity riêng, không reuse user token dài hạn.

## 2. RBAC

Roles: owner, admin, editor, viewer, billing. Permissions tách theo project read/edit, asset upload/generate, render, publish, manage members/webhooks.

Repository query luôn scope workspace/project; authorization không chỉ ở UI/router.

## 3. Content and URL policy

### `content_policy.py`

- `validate_upload_intent(intent, quota, policy) -> ValidationReport`.
- `validate_detected_media(metadata, policy) -> ValidationReport`.
- `sanitize_display_filename(name) -> str` chỉ để hiển thị.
- `classify_generated_content(result, policy) -> ModerationDecision`.

### `url_policy.py`

- `parse_https_url(value) -> URL`.
- `resolve_public_addresses(hostname) -> list[IPAddress]`.
- `validate_address_set(addresses) -> None`.
- `fetch_with_redirect_policy(url, limits) -> StreamResult`.

DNS được kiểm tra lại cho mỗi redirect/connect; client không dùng proxy environment ngoài allowlist.

## 4. Audit

### `audit.py`

- `record_audit_event(uow, actor, action, resource, outcome, metadata) -> AuditEvent`.
- `redact_audit_metadata(metadata) -> Mapping`.
- `query_audit_events(workspaceId, filters, actor) -> Page`.

Audit cho login/permission changes, project delete/restore, provider generation, render/publish, webhook/secret changes. Audit append-only và có retention policy.

## 5. Secret handling

- Secret từ environment/secret manager.
- Provider credential được encrypt at rest nếu workspace-specific.
- API trả secret đúng một lần khi tạo/rotate.
- Logs/traces không chứa token, signed URL, raw prompt/reference mặc định.
- Signed URL TTL ngắn, scope object/method/content disposition.

## 6. Telemetry files

```text
backend/app/telemetry/
├── logging.py
├── metrics.py
├── tracing.py
└── context.py
```

### Functions

- `configure_logging(settings) -> None`.
- `bind_context(requestId?, jobId?, projectId?, workspaceId?) -> ContextToken`.
- `redact_log_record(record) -> record`.
- `record_operation_metric(name, duration, outcome, tags) -> None`.
- `start_span(name, attributes) -> Span`.

Không dùng project/user ID raw làm high-cardinality metric label; chúng chỉ ở structured logs/traces có access control.

## 7. Required metrics

- HTTP request rate/latency/error by route/status.
- DB pool saturation/query latency.
- Queue depth/age by queue.
- Job duration/failure/retry/cancel by type/stage.
- Render real-time factor, frames, output size.
- Provider latency/error/token/image/audio usage/cost.
- Storage bytes/orphan/temp cleanup.
- SSE connections/reconnect/drop.

## 8. Alerts

- Readiness failures.
- Queue oldest age vượt SLO.
- Render/provider failure spike.
- Orphaned jobs.
- Storage/DB nearing capacity.
- Webhook delivery failure rate.
- Backup/cleanup/reconciliation missed schedule.

Mỗi alert link runbook với query và recovery steps.
SLO, RPO/RTO, retry, TTL và retention default dùng giá trị normative tại
[`14_production_configuration.md`](./14_production_configuration.md); dashboard
không được tự đặt một bộ ngưỡng khác không có ADR.

## 9. Privacy/retention

- Workspace policy có thể siết chặt prompt/reference retention; default triển khai
  theo `14_production_configuration.md`.
- Provider disclosure/consent trước gửi content ra ngoài.
- Delete workflow tạo tombstone, cancel jobs, revoke links, schedule blob purge.
- Legal hold/backup retention nếu sản phẩm yêu cầu phải được tách rõ.
- Analytics không thu raw narration/media mặc định.

## 10. Security tests

- JWT issuer/audience/expiry/key rotation.
- Horizontal/vertical authorization.
- IDOR qua asset/job/artifact IDs.
- Upload MIME spoof/SVG/XSS/archive bomb.
- SSRF DNS/redirect/IP literal/IPv6.
- Shell/subprocess injection.
- Signed URL scope/expiry.
- Rate-limit/idempotency abuse.
- Webhook signature/replay.

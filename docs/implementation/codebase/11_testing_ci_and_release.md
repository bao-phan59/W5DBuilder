# 11 — Testing, CI, Migration và Release

## 1. Test layout

```text
backend/tests/
├── unit/
├── contract/
├── integration/
├── security/
└── fixtures/
frontend/src/test/
├── unit/
├── component/
└── browser/
packages/video/tests/
├── unit/
├── snapshots/
└── render/
tests/e2e/
└── production-pipeline/
```

## 2. Contract tests

- Validate every example against schema.
- Generate Python/TS types and require clean diff.
- Round-trip JSON through Python and TS validators.
- Compatibility fixtures cho current major/minor.
- Migration fixtures old→new.
- OpenAPI client regeneration clean.

## 3. Backend tests

- Domain functions: pure unit tests.
- Repositories: PostgreSQL container, không SQLite giả production semantics.
- Application services: real UoW + fake providers/storage.
- API: auth, errors, ETag, idempotency, pagination.
- Workers: at-least-once duplicate delivery, lease, heartbeat, cancellation, retry.
- Storage: MinIO/S3-compatible integration.

## 4. Frontend tests

- Generated client/error mapping.
- Query cache + SSE invalidation.
- Editor commands/inverse/merge.
- Save conflict/rebase.
- Canvas coordinate transforms và letterbox.
- Timeline frame snapping/virtualization.
- Accessibility bằng automated scan + keyboard scenarios.

## 5. Render tests

- Preset interpolation ở start/middle/end frames.
- Composition schema rejection.
- Asset/font preload.
- Selected frame visual regression với tolerance.
- Short golden render media probe.
- Player/server render parity bằng cùng snapshot.
- Cancel/crash/retry quanh immutable upload và database registration.

Không pixel-snapshot mọi frame. Dùng semantic assertions + representative visual frames.

## 6. Production E2E scenarios

1. Manual script → placeholder → preview → render.
2. LLM script → approve → TTS/alignment → asset generation → render.
3. Upload PNG/SVG/video → processing → assignment.
4. Edit upstream script → downstream stale → recompute.
5. Concurrent editor conflict bằng ETag.
6. Worker crash giữa render → orphan recovery.
7. Provider rate-limit → retry/backoff.
8. Cancel job và project archive.
9. Publish fail sau render success.
10. Backup restore golden workspace.

## 7. CI pipelines

### Pull request

- Markdown links/JSON examples.
- Contract/schema generation.
- Backend lint/type/unit/contract.
- Frontend lint/type/unit/build.
- Video package type/unit/composition smoke.
- Dependency/license/secret scan.

### Main branch

- Integration với PostgreSQL/Redis/MinIO.
- Browser tests.
- Golden short render.
- Build versioned containers và SBOM.

### Release candidate

- Full E2E staging.
- Migration dry-run trên anonymized snapshot.
- Security scan.
- Load/soak render/job tests.
- Backup/restore drill.

## 8. Database migration

- Alembic migration review bắt buộc.
- Expand/contract cho zero-downtime breaking change.
- Backfill idempotent, batched, observable.
- API/code tương thích cả old/new schema trong deployment window.
- Rollback chỉ khi data-safe; nếu không có forward-fix runbook.

## 9. Contract migration

### `backend/app/application/migrations/contracts.py`

- `find_migration(kind, fromVersion, toVersion) -> MigrationPath`.
- `migrate_document(document, targetVersion) -> MigratedDocument`.
- `validate_migration_result(before, after) -> ValidationReport`.

Không migrate silently khi chỉ đọc nếu việc đó làm thay đổi persisted state. Migration persisted là explicit job với audit.

## 10. Release strategy

- Semantic application version + build SHA.
- Composition version pin vào RenderSnapshot.
- Provider adapter version pin vào artifact provenance.
- Canary API/worker deployment.
- Worker cũ hoàn thành snapshot cũ; worker mới phải đọc supported schema range.
- Không xóa composition version còn được render job active tham chiếu.

## 11. Performance budgets

- API read/write latency SLO theo environment.
- Editor interaction frame budget và max memory.
- Preview first-ready time.
- Queue wait and render real-time factor.
- Upload/process throughput.

Ngưỡng ban đầu bắt buộc lấy từ
[`14_production_configuration.md`](./14_production_configuration.md). Load test có
thể điều chỉnh bằng ADR trước release; CI đồng thời giữ absolute gate theo SLO mới
và regression threshold tương đối.

## 12. Release gate

Release production bị chặn nếu:

- Contract/generated diff chưa commit.
- Migration/backup test fail.
- Golden E2E hoặc render probe fail.
- Critical/high security finding mở.
- Alert/runbook cho service mới chưa có.
- Dependency license không được phép.

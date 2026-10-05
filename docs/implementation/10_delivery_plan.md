# 10 — Delivery Plan và Acceptance Criteria

## 1. Nguyên tắc delivery

- Hoàn thành theo vertical slice, không build toàn bộ từng layer rồi mới tích hợp.
- Mỗi work package tạo artifact kiểm chứng được.
- Mock path phải hoàn thành trước live provider path.
- MVP có thể dùng adapter local, nhưng WP6 bắt buộc chuyển sang production profile
  đã chốt; không để adapter MVP trở thành kiến trúc bản cuối.
- Status chỉ đổi theo định nghĩa tại [`../12_roadmap.md`](../12_roadmap.md).

## 2. WP0 — Documentation và contract baseline

### Deliverables

- Glossary và artifact lifecycle thống nhất.
- Contract executable cho ScriptDocument, TimingDocument, ScenePlan, AssetMap, TimelineDocument và RenderJob.
- Python/TypeScript type strategy.
- Golden fixture “Ba Chú Voi” đã sửa.
- Structural + semantic validator.
- Contract/versioning ADR.

### Acceptance

- Mọi fixture validate trong CI.
- Tổng duration được kiểm tra tự động.
- Entity lifecycle của fixture hợp lệ.
- Không còn `script.json`/`script_final.json`/`script_annotated.json` cạnh tranh làm canonical output.
- Design docs link về contract thay vì copy schema chuẩn.

## 3. WP1 — Backend foundation

### Deliverables

- Typed config và application factory.
- Health/readiness.
- Project/artifact repository local-first.
- Script import/update/validate API.
- Error envelope, request ID, revision conflict.
- Mock providers và local asset storage.

### Acceptance

- Khởi động từ môi trường sạch theo một documented command.
- Không cần API key cho test/happy path.
- API integration tests pass.
- Stale update trả conflict.
- Không lộ local path hoặc stack trace qua API.

## 4. WP2 — Planning và timeline

### Deliverables

- Deterministic scene planner cho golden fixture.
- Layout templates tối thiểu cho 1/2/3 instances.
- Placeholder AssetMap.
- Animation preset registry tối thiểu.
- Timeline composer và render-readiness validator.

### Acceptance

- Cùng input/version tạo cùng output.
- Timeline chỉ dùng integer frames.
- Không có dangling entity/asset reference.
- No-gap invariant đạt hoặc intentional bridge được khai báo.
- Unit và contract tests cho lifecycle/layout/preset pass.

## 5. WP3 — Browser editor/preview

### Deliverables

- W5D application shell thay Vite starter.
- Typed API client và project store.
- Script/validation view.
- Canvas + Remotion Player.
- Timeline play/pause/scrub.
- Asset assignment bằng placeholder/local image.
- Save/autosave/conflict feedback.

### Acceptance

- Golden project load và preview được.
- Scrub tới frame xác định cho state đúng.
- Canvas/timeline selection đồng bộ.
- Validation/missing asset không gây crash.
- Frontend build, tests và browser happy path pass.

## 6. WP4 — Render MVP

### Deliverables

- Remotion project/composition.
- Local render runner và RenderJob API.
- Progress/cancel/error handling.
- MP4 output registration.
- Output probe và key-frame tests.

### Acceptance

- Golden project render MP4 1920×1080, 30 FPS.
- Duration và total frames đúng contract.
- Player và render khớp tại selected key frames.
- Retry không tạo nhiều output “final” cho cùng idempotency key.
- Partial/failed output không được công bố.

Hoàn thành WP0–WP4 tương đương MVP end-to-end.

## 7. WP5 — Audio và provider integration

### Deliverables

- Một TTS provider + mock.
- Word alignment và TimingDocument reconciliation.
- Một image provider có capability matrix và contract test.
- Background removal/asset derivative pipeline.
- Usage/cost metadata và provider diagnostics.

### Acceptance

- Provider fail không corrupt project.
- Timeout/retry/cancel có tests.
- TTS audio và sentence spans không vượt duration.
- Provider không hỗ trợ feature phải từ chối rõ ràng, không silently ignore.

## 8. WP6 — Production readiness

Production profile, limit và SLO mặc định đã chốt tại
[`codebase/14_production_configuration.md`](./codebase/14_production_configuration.md).
Load test có thể điều chỉnh bằng ADR nhưng không được để quyết định mở.

- Authentication/authorization/quota.
- PostgreSQL, Redis/Celery và S3-compatible object storage bắt buộc.
- Migrations, backups và restore drill.
- Observability dashboards/alerts.
- Security review cho upload, remote fetch và render isolation.
- Deployment/runbook và incident procedure.
- Provider lock manifest, capability smoke tests và cost ceiling.

## 9. Review checklist cho mọi work package

- Contract impact đã được đánh giá.
- Docs và status roadmap đã cập nhật.
- Happy path và failure path có tests.
- Không cần undocumented manual step.
- Mock/offline path vẫn hoạt động.
- Security/privacy/cost impact đã được xem xét.
- Không mở rộng scope sang milestone sau mà chưa có quyết định.

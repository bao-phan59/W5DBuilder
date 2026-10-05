# Delivery phases và coverage

Chỉ đọc section phase đang làm. Bảng này là routing, không thay acceptance trong docs. Nếu docs đã thay đổi, cập nhật plan theo bản hiện hành và giữ requirement traceability. Đừng coi 14 file spec là 14 phase độc lập: storage, jobs, security và testing xuyên nhiều WP.

| Delivery | Roadmap | Phụ thuộc |
|---|---|---|
| WP0 contracts | M0 | Inventory thật |
| WP1 backend | M1 | WP0 |
| WP2 planning/timeline | Một phần M2 | WP0, WP1 |
| WP3 editor/preview | Hoàn thành M2 | WP2 |
| WP4 render | M3, MVP E2E | WP3 |
| WP5 audio/providers | M4 | WP4 |
| WP6 production | M5 | WP0–WP5 |

Trong `docs/implementation/codebase/` dưới đây chỉ liệt kê basename. Đọc section chức năng/test liên quan, không đọc hết mỗi file. Acceptance gốc lấy từ section WP tương ứng của `docs/implementation/10_delivery_plan.md` và milestone trong `docs/12_roadmap.md`.

## WP0 — Contract baseline

Sources: `01_repository_and_runtime.md` (target tree/dependency), `02_contracts_and_artifacts.md`; `11_testing_ci_and_release.md` (contract/CI); dùng `13_function_index.md` như index khi cần tìm symbol.

Batch gợi ý:
1. Inventory contract ScriptDocument của `.agents/skills/w5d-script`, ADR versioning/generation và runtime scaffolding tối thiểu phục vụ tests.
2. JSON Schema 2020-12 cho sáu artifacts, chia 1–2 artifacts/batch; golden examples có provenance/time units/ID rules.
3. Structural + semantic validator, regenerate Python/TS types, fixture round-trip và CI contract gate.

Gate: fixtures hợp lệ và negative fixtures bị từ chối; duration và entity lifecycle đúng; generated output sạch sau regenerate; canonical script output duy nhất. Không chỉ dùng schema syntax test để chứng minh semantic validity.

## WP1 — Backend foundation

Sources: `01_repository_and_runtime.md`, `03_database_storage_and_jobs.md` (interfaces/transaction), `04_backend_api_and_services.md` (project/script/API); `10_security_and_observability.md` cho boundary đang implement.

Batch gợi ý: typed config/app factory/health → repository local-dev + artifacts/revision → script APIs/errors/ETag → upload/mock providers và integration.

Gate: clean startup theo command documented, no-key mock happy path, API integration pass; stale update conflict; error không lộ path/trace; invalid input không mutate state. Production repositories/queue không bắt buộc triển khai đầy đủ ở đây; ghi deferred-to-WP6 rõ ràng, giữ interface tương thích spec.

## WP2 — Deterministic planning và timeline

Sources: `07_scene_timeline_pipeline.md`; contract/lifecycle section trong `02_contracts_and_artifacts.md`; `06_asset_pipeline.md` cho placeholder map và `05_script_voice_pipeline.md` chỉ khi cần timing mock.

Batch gợi ý: deterministic golden planner → layouts 1/2/3 instances → presets/placeholder assets → timeline composer và render-readiness.

Gate: same input/version → same output; integer frames; không dangling refs; no-gap hoặc bridge khai báo; tests lifecycle/layout/preset và invalid timing. WP2 DONE không đồng nghĩa M2 DONE vì browser acceptance còn ở WP3.

## WP3 — Browser editor và preview

Sources: `09_frontend_editor.md`; `08_render_and_publish_pipeline.md` cho shared composition/snapshot; `04_backend_api_and_services.md` cho client contract.

Batch gợi ý: replace starter shell/client/store → script/validation views → shared video composition/Player → selection/play/scrub → asset assignment/save/autosave/conflict.

Gate: golden project browser happy path; frame scrub đúng state; canvas/timeline selection đồng bộ; missing/invalid assets không crash; frontend lint/type/build/component và browser tests pass. Cài/pin Remotion khi slice thực sự dùng nó; không sao chép hai composition cho preview/server. Có thể dùng các skill Remotion có sẵn nếu đúng task, không phụ thuộc skill đó để resume.

## WP4 — Render MVP

Sources: `08_render_and_publish_pipeline.md`, `11_testing_ci_and_release.md` render/E2E, `12_end_to_end_execution.md` render/cancel/crash sections.

Batch gợi ý: Node argument-array runner/shared snapshot → RenderJob/progress/cancel → immutable output registration/probe → golden parity + idempotency/failure cases.

Gate: MP4 1920×1080/30 FPS, duration/frame count đúng; representative Player/server frames khớp có tolerance documented; retry không duplicate final; cancel/crash/partial không publish output. Probe media thật, không coi file extension hoặc render stub là PASS. WP0–WP4 đạt mới gọi MVP E2E.

## WP5 — Audio, providers và assets

Sources: `05_script_voice_pipeline.md`, `06_asset_pipeline.md`, `14_production_configuration.md` provider lock/capabilities/cost; failure sections `12_end_to_end_execution.md`.

Batch gợi ý: TTS mock/real adapter → alignment/timing reconciliation → image capability contract → derivative/background removal/media support → usage/cost/diagnostics.

Gate: mock path vẫn pass; ít nhất provider thật cho capabilities yêu cầu với authorization/keys; fail/timeout/retry/cancel không corrupt state; sentence/audio spans trong duration; unsupported feature trả lỗi rõ. Thực hiện thêm audio normalize/ducking/SFX, GIF/video cases theo acceptance M4 và spec, không coi riêng TTS pass là M4 DONE. Live gate thiếu keys/authorization = blocked, không phải skipped PASS.

## WP6 — Production readiness

Sources: `03_database_storage_and_jobs.md`, `10_security_and_observability.md`, `11_testing_ci_and_release.md`, `14_production_configuration.md`; `12_end_to_end_execution.md` final readiness/publish/failure; rà các requirements production chưa giao từ WP trước bằng section/symbol search.

Batch gợi ý:
1. PostgreSQL/async SQLAlchemy/Alembic + migration/restore fixture.
2. Redis/Celery/outbox/leases/reconciliation/at-least-once/cancel.
3. S3 immutable/multipart checksum/database visibility + orphan handling.
4. OIDC/JWT workspace RBAC/quota/audit; HMAC webhooks/publish/share nếu nằm trong spec.
5. Upload/SSRF/SVG/subprocess isolation; structured logs/traces/metrics/alerts.
6. Provider lock/limits/SLO, CI containers, deployment/recovery runbook.
7. Production E2E/security/load/soak/backup-restore drills.

Gate: real Postgres/Redis/S3 integration; auth/tenant isolation; duplicate delivery/worker crash/outage recovery; staging E2E all documented scenarios; security scans và unresolved critical/high findings chặn; performance thresholds/SLO/RPO/RTO từ `14_production_configuration.md`; actual restore drill có evidence; deployment/recovery runbook đã thử. Không dùng SQLite hoặc mock để chứng minh production semantics. Deploy hệ thống thật chỉ khi scope hiện tại cho phép.

## Final coverage audit

Khi WP6 gần xong, kiểm tra requirements từng spec **một section/batch** để tìm khoảng thiếu; không nạp lại toàn bộ docs. Map module/function trong `13_function_index.md` đến source và test, nhưng sự tồn tại của symbol không chứng minh đúng behavior. Coverage cuối gồm contracts/provenance/invalidation, script/timing, assets, timeline, preview/render, publish, auth/quota/audit, jobs/storage/recovery, operations. Chỉ gọi production-complete khi README DoD và release gate đều có evidence.

# 12 — Lộ Trình Phát Triển

> Loại: Status và delivery roadmap  
> Cập nhật: 2026-10-05  
> Nguồn sự thật về tiến độ: tài liệu này

## 12.1 Quy ước trạng thái

| Trạng thái | Ý nghĩa |
|---|---|
| `DESIGNED` | Đã có quyết định/tài liệu nhưng chưa có implementation |
| `SCAFFOLDED` | Đã có khung hoặc prototype, chưa chạy end-to-end |
| `IMPLEMENTED` | Có code và chạy cục bộ cho happy path |
| `TESTED` | Có automated tests và acceptance evidence |
| `DONE` | Đạt toàn bộ Definition of Done |
| `DEFERRED` | Chủ động đưa ra ngoài scope hiện tại |

## 12.2 Snapshot hiện tại

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Product/design documentation | `DESIGNED` | Đã chuẩn hóa baseline 0.2 |
| Implementation documentation | `DESIGNED` | Có bộ tài liệu triển khai chuẩn |
| Script skill | `SCAFFOLDED` | ScriptDocument 1.0/schema/example đã migrate; chưa có service integration |
| Image provider abstraction | `SCAFFOLDED` | Prototype, chưa có app/config/test |
| Backend API | `DESIGNED` | Chưa có FastAPI entrypoint/routes |
| Persistence và storage | `DESIGNED` | Chưa implement |
| Scene/layout engine | `DESIGNED` | Chưa implement |
| Timeline/animation composer | `DESIGNED` | Chưa implement |
| Frontend editor | `SCAFFOLDED` | Vite starter, chưa có W5D UI |
| Remotion renderer | `DESIGNED` | Chưa có project/package |
| TTS/alignment | `DESIGNED` | Chưa implement |
| Automated tests/CI | `DESIGNED` | Chưa có |

## 12.3 Milestone M0 — Contract Baseline

**Mục tiêu:** mọi module dùng cùng thuật ngữ và data contract.

- [ ] Chốt `ScriptDocument`, `TimingDocument`, `ScenePlan`, `AssetMap`, `TimelineDocument` và `RenderJob`.
- [ ] Chốt ID rules, versioning, time units và coordinate system.
- [ ] Viết JSON Schema/Pydantic/TypeScript generation strategy.
- [x] Sửa skill và fixture “Ba Chú Voi” theo ScriptDocument 1.0.
- [ ] Có structural và semantic validation cho golden fixture.

Acceptance criteria được mô tả tại [implementation/10_delivery_plan.md](./implementation/10_delivery_plan.md).

## 12.4 Milestone M1 — Executable Backend Foundation

**Mục tiêu:** backend chạy được không cần API key.

- [ ] FastAPI app, config, health/readiness, CORS.
- [ ] Project repository local-first.
- [ ] Script import/validate/update endpoints.
- [ ] Local asset upload với validation.
- [ ] Mock image/TTS adapters.
- [ ] OpenAPI và error envelope thống nhất.
- [ ] Unit/integration tests.

## 12.5 Milestone M2 — Browser Preview Vertical Slice

**Mục tiêu:** xem được golden project trong browser.

- [ ] Project store và API client typed.
- [ ] Canvas 16:9 với placeholder assets.
- [ ] Timeline play/pause/scrub.
- [ ] Preset enter/idle/exit tối thiểu.
- [ ] Validation panel và autosave có revision control.
- [ ] Component và browser tests cho happy path.

## 12.6 Milestone M3 — MP4 Render Vertical Slice

**Mục tiêu:** preview và output dùng cùng composition.

- [ ] Remotion composition đọc `TimelineDocument`.
- [ ] Preview bằng Remotion Player.
- [ ] Render job local, progress và cancellation cơ bản.
- [ ] MP4 1920×1080, 30 FPS.
- [ ] Golden render test: duration/frame count/asset completeness.

Khi M3 đạt `DONE`, dự án mới được gọi là **MVP end-to-end**.

## 12.7 Milestone M4 — Audio và Asset Quality

- [ ] Một TTS provider production và mock fallback.
- [ ] Word-level alignment và timing reconciliation.
- [ ] Background removal.
- [ ] Một image provider production có contract test.
- [ ] GIF/video playback theo capability matrix.
- [ ] Audio normalize, ducking và SFX cơ bản.

## 12.8 Milestone M5 — Production Readiness

- [ ] PostgreSQL, SQLAlchemy async và Alembic migrations.
- [ ] Redis/Celery durable queues, outbox, leases và reconciliation.
- [ ] S3-compatible object storage với multipart checksum và DB visibility boundary.
- [ ] Authentication, authorization và quotas.
- [ ] Signed webhooks, audit log, observability.
- [ ] Backup/restore và deployment runbook.
- [ ] Provider lock, production limits, SLO/RPO/RTO theo [production configuration](./implementation/codebase/14_production_configuration.md).

## 12.9 Deferred sau MVP

- Template marketplace.
- Collaboration thời gian thực.
- Analytics/retention.
- Style transfer và auto color match.
- Green-screen removal nâng cao.
- Mobile editor đầy đủ.
- Multi-region render farm.

## 12.10 Definition of Done theo milestone

| Milestone | Điều kiện tối thiểu |
|---|---|
| M0 | Golden fixture hợp lệ và types không drift |
| M1 | Backend chạy từ môi trường sạch, API tests pass |
| M2 | Golden project preview được trong browser |
| M3 | Render được MP4 và preview/output nhất quán |
| M4 | Audio/assets production có fallback và diagnostics |
| M5 | Có security, observability, backup và runbook |

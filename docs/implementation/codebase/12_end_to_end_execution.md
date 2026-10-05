# 12 — End-to-End Execution và Failure Recovery

## 1. Production happy path

### Phase A — Project và script

1. Frontend gọi `create_project`.
2. User nhập idea và gọi `submit_script_generation` với idempotency key.
3. API transaction tạo Job + outbox.
4. Dispatcher enqueue `execute_job(jobId)`.
5. Worker claim lease, gọi `execute_script_generation`.
6. LLM output được normalize và validate; candidate Script artifact được commit.
7. SSE báo candidate ready; user review/approve.
8. `approve_script` set current Script và invalidate descendants cũ.

### Phase B — Voice và timing

1. `submit_voice_job` snapshot Script ref + VoiceConfig.
2. Worker `build_voice_segments` rồi provider `synthesize`.
3. Audio ingest/probe thành VoiceAsset.
4. Nếu provider timing đủ: reconcile; nếu không: alignment provider.
5. `reconcile_sentence_spans` tạo TimingDocument.
6. Commit artifact với Script/VoiceAsset inputs.

### Phase C — Scene và assets

1. Scene job gọi `build_sentence_states`, `detect_scene_boundaries`, state resolver và layout solver.
2. Commit ScenePlan cùng validation warnings.
3. `find_unassigned_requirements` tạo asset requirements.
4. User upload/chọn/generate assets.
5. Mọi asset qua inspect/sanitize/derivative pipeline.
6. `assign_asset` commit AssetMap.

### Phase D — Timeline và preview

1. Timeline job load current Script, Timing, ScenePlan, AssetMap, PostprocessConfig.
2. Kiểm tra tất cả artifact current và fingerprints.
3. `build_timebase`, quantize spans, compile tracks.
4. `compute_meaningful_coverage` và continuity repair.
5. Validate/commit TimelineDocument.
6. Frontend refetch Timeline + controlled asset manifest.
7. `ProjectPlayer` render cùng `W5DComposition` production.

### Phase E — Final render

1. User chọn profile; frontend lấy readiness report.
2. `submit_render_job` tạo immutable RenderSnapshot.
3. Render worker stage assets và gọi Node runner.
4. `renderMediaWithProgress` gửi structured progress.
5. Output được probe, upload vào immutable object key, verify checksum và register Asset trong database; DB registration là visibility boundary.
6. Job succeeded; SSE/refetch hiển thị output.

### Phase F — Publish/share

1. Baseline luôn cho export file hoặc tạo signed/revocable share link từ render
   asset immutable.
2. External destination chỉ xuất hiện khi adapter đã qua capability/security tests;
   user chọn destination và xác nhận explicit.
3. Publish job dùng render asset immutable, không tạo lại render.
4. Publish result/audit lưu riêng; render asset không bị xóa nếu publish fail.

## 2. Human approval gates

Configurable gates:

- Script candidate approval.
- Voice approval.
- Scene/layout approval.
- Generated asset selection.
- Render final confirmation.
- External publish confirmation luôn explicit trừ automation policy được owner cấu hình.

Auto mode vẫn phải chạy validation/readiness và lưu provenance.

## 3. Upstream edit scenario

Khi user sửa Script revision 7 → 8:

1. API kiểm tra `If-Match` project revision.
2. Commit Script r8.
3. `mark_descendants_stale` đánh Timing/ScenePlan/AssetMap/Timeline liên quan stale.
4. Project readiness về `needsRebuild` được tính từ current refs; không persist trạng thái sai độc lập.
5. UI nhận event và disable final render.
6. User chọn rebuild all hoặc từng stage.
7. Unchanged asset blobs vẫn reusable; AssetMap được proposal lại theo instance IDs.
8. Render output cũ vẫn tải được trong history nhưng ghi rõ source revision cũ.

## 4. Concurrent edit scenario

1. Client A/B đọc revision 20.
2. A save bằng strong ETag `If-Match: "prj-20-7f3a9c"`, nhận revision 21 và ETag mới.
3. B save revision 20, server trả `412 REVISION_PRECONDITION_FAILED` và current revision 21.
4. Frontend tải artifact mới, rebase command patches có thể merge.
5. Conflict cùng field yêu cầu user chọn; không last-write-wins.

## 5. Provider failure

- Timeout/429/5xx: Job remains running attempt → scheduled retry; lease/heartbeat tiếp tục theo policy.
- Auth/quota/model invalid: fail non-retryable và giữ input artifact current.
- Malformed output: bounded repair; không commit invalid artifact.
- Partial provider blob: lưu temp, purge khi fail.
- Circuit breaker có thể ngăn request mới và trả provider unavailable.

## 6. Worker crash

1. Worker đã claim Job và cập nhật lease.
2. Crash làm heartbeat dừng.
3. Scheduler `find_orphaned` sau lease expiry.
4. Nếu cancellation requested → cancelled/cleanup.
5. Nếu retryable và attempt dưới max → requeue cùng job/input fingerprint.
6. Handler kiểm tra immutable output object và DB registration trước chạy lại.
7. Nếu output đã complete/probe pass → finish transaction; nếu partial → cleanup và rerun stage.

## 7. Render cancellation

1. API `request_cancel` chuyển job sang cancelling.
2. Worker heartbeat thấy flag hoặc nhận control signal.
3. Node runner nhận cancel signal, dừng Remotion/Chrome/FFmpeg process tree.
4. Worker không đăng ký output; schedule cleanup workspace/object chưa visible.
5. Job thành cancelled chỉ sau runner exit/timeout handling.

## 8. Storage/database outage

- DB unavailable: API readiness false; không nhận mutation. Worker không ack task nếu chưa claim/commit state.
- Redis unavailable: job submit transaction giữ outbox unsent; dispatcher gửi lại khi hồi phục.
- S3 unavailable: metadata transaction không ghi asset ready; upload/render retry theo stage.
- Không có distributed transaction DB/S3; dùng immutable key + database visibility + reconciliation.

## 9. Reconciliation jobs

### `backend/app/workers/reconciliation.py`

- `dispatch_unsent_outbox(limit) -> int`.
- `reconcile_orphaned_jobs(limit) -> ReconcileReport`.
- `reconcile_pending_uploads(cutoff) -> int`.
- `reconcile_unregistered_outputs(limit) -> int`.
- `mark_missing_blobs(limit) -> ValidationReport`.
- `purge_expired_temp_objects(limit) -> int`.
- `recalculate_project_readiness(projectId) -> ReadinessState`.

Mọi reconciliation idempotent và phát metrics/audit khi sửa state.

## 10. Final readiness computation

### `application/projects/readiness.py`

`compute_readiness(project, artifacts, assets, jobs) -> ProjectReadiness` trả:

- stage hiện tại;
- blockers;
- warnings;
- stale/missing artifacts;
- active jobs;
- allowed next operations.

Readiness được tính từ source of truth, không lưu boolean `ready` dễ drift. Có thể cache với project revision làm key.

## 11. Production acceptance scenario

Một release cuối phải chạy scenario 10 phút video với:

- Script generated và manually edited.
- Voice thật + word alignment.
- PNG, sanitized SVG derivative, GIF/video/Lottie assets.
- AI-generated character references.
- Nhiều scenes, camera, music/SFX.
- Portrait và landscape timelines/renders.
- Concurrent editor conflict.
- Provider retry và render worker crash injection.
- Export file + signed/revocable share link; external publish chỉ là acceptance khi
  adapter tương ứng đã được certified.
- Backup/restore rồi verify asset/artifact hashes.

# 08 — Render, Export và Publish Pipeline

## 1. Package tree

```text
packages/video/src/
├── Root.tsx
├── compositions/W5DComposition.tsx
├── schema/parse-render-snapshot.ts
├── tracks/
│   ├── BackgroundTrack.tsx
│   ├── ObjectTrack.tsx
│   ├── TextTrack.tsx
│   ├── CameraTrack.tsx
│   └── AudioTrack.tsx
├── presets/
├── assets/AssetResolver.ts
├── diagnostics/
└── runner/
    ├── render-job.ts
    ├── render-still.ts
    └── probe-output.ts
```

Tất cả Remotion packages pin cùng exact version. Player và render runner import cùng `W5DComposition` và cùng generated contract types.

## 2. Composition functions

### `W5DComposition.tsx`

| Symbol | Props | Mô tả |
|---|---|---|
| `W5DComposition` | `RenderSnapshot` | Render tracks theo frame hiện tại |
| `calculateW5DMetadata` | snapshot | Validate width/height/fps/duration/default codec |
| `CompositionRoot` | none | Register composition versioned ID |

Composition không fetch network tùy ý, không đọc current time, không dùng `Math.random`, không mutate props.

## 3. Track components

- `BackgroundTrack({items, assetManifest})`.
- `ObjectTrack({items, assetManifest, presetRegistry})`.
- `TextTrack({items, fontManifest})`.
- `CameraTrack({track, children})`.
- `AudioTrack({voice, music, sfx, assetManifest})`.

Mỗi track dùng half-open frame ranges. Item ngoài range không mount trừ premount window cần preload.

## 4. Asset resolver

### `assets/AssetResolver.ts`

- `createAssetResolver(manifest, policy) -> AssetResolver`.
- `resolve(assetId, derivativeRole) -> ResolvedAsset`.
- `preflightAll(requiredRefs) -> Promise<AssetPreflightReport>`.
- `verifyChecksum(asset) -> Promise<void>` trong worker staging.

Backend tạo signed/internal URLs hoặc stage local files. Render component không nhận S3 credentials.

## 5. Render snapshot service

### `backend/app/application/render/snapshot.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `build_render_snapshot` | `async (projectId, profile, actor) -> RenderSnapshot` | Resolve current artifacts và manifest |
| `validate_snapshot` | `(snapshot) -> ValidationReport` | Schema, stale, readiness, capability |
| `persist_snapshot` | `async (snapshot, inputs, uow) -> ArtifactRef` | Immutable snapshot artifact |

Snapshot gồm exact artifact refs/hashes, asset derivatives/checksums, fonts, composition version, render profile, audio policy và deterministic seed.
Snapshot còn chứa rights/attribution manifest của assets và fonts; readiness policy quyết định block hay warning.

## 6. Render job functions

### `backend/app/application/render/service.py`

- `submit_render_job(projectId, profileId, publishIntent, actor, key) -> Job`.
- `execute_render_job(jobId, context) -> RenderResult`.
- `cancel_render_job(jobId, actor) -> Job`.
- `register_render_output(job, probe, blob) -> Asset`.

### `packages/video/src/runner/render-job.ts`

- `runRenderJob(args: RenderJobArgs): Promise<RenderRunnerResult>`.
- `bundleComposition(input): Promise<BundleRef>` với cache theo composition build SHA.
- `selectComposition(bundle, snapshot): Promise<CompositionInfo>`.
- `renderMediaWithProgress(input, callbacks): Promise<OutputPath>`.
- `cancelRender(signal): Promise<void>` dùng supported cancel signal/process handling.
- `probeAndValidateOutput(path, expected): Promise<ProbeReport>`.

Python worker gọi Node runner bằng executable + argument array, truyền snapshot path trong isolated workspace, đọc structured JSON lines từ stdout. Không ghép shell string.

## 7. Render stages

```text
validate_snapshot
→ stage_assets
→ bundle_or_reuse
→ resolve_composition
→ render_media
→ probe_output
→ upload_immutable_output
→ verify_stored_output
→ register_asset
→ succeeded
```

Output chỉ publish sau probe pass. Worker upload vào key immutable chứa `jobId + snapshotHash + checksum`, dùng conditional create khi storage hỗ trợ. Database `register_asset` mới là visibility boundary: object tồn tại nhưng chưa đăng ký không được cấp download URL. Nếu worker chết giữa upload và DB commit, reconciliation xác minh checksum rồi đăng ký idempotently hoặc purge theo TTL.

General-purpose S3 không có atomic rename; “promote” không được implement bằng giả định rename. Nếu adapter dùng staging key, copy/delete chỉ là cleanup workflow và không phải transaction boundary. Multipart upload phải khai báo full-object checksum; không dùng multipart ETag như SHA-256.

## 8. Profiles

Production profiles có version:

- Landscape 1080p30/60.
- Portrait 1080×1920 30/60.
- Square 1080×1080.
- Preview proxy 960×540/30.
- Still/thumbnail.

Profile quy định codec, pixel format, audio codec/sample rate, bitrate/CRF bounds, color space và max duration. Project layout có thể cần profile-specific ScenePlan/Timeline; không chỉ resize final frames.

## 9. Audio finalization

- Voice target loudness và true-peak limit.
- Music ducking envelope theo voice activity.
- SFX bus limiter.
- Fade policies.
- Audio tail được tính vào totalFrames.
- Probe xác nhận sample rate/channels/duration tolerance.

Postprocess config lưu dB/LUFS semantics rõ, không dùng “so với voice” mơ hồ.

## 10. Publish/export

### `backend/app/application/publish/service.py`

- `create_export(projectId, renderAssetId, destination, actor, key) -> Job`.
- `execute_export(jobId, context) -> PublishResult`.
- `create_share_link(assetId, policy, actor) -> ShareLink`.
- `revoke_share_link(linkId, actor) -> None`.

- `build_attribution_manifest(snapshot) -> AttributionManifest` tổng hợp attribution/license cho output và publish destination.

Destination adapters kiểm tra OAuth scope, rate limit và retry semantics. Publish không nằm trong render transaction; render thành công vẫn được giữ nếu publish fail.

## 11. Recovery

- Worker restart: lease hết hạn → orphan reconciliation.
- Nếu immutable output object đã có checksum đúng nhưng chưa đăng ký, retry tiếp tục từ verify/register stage.
- Nếu render incomplete, xóa workspace và render lại.
- Unique immutable key và conditional create theo job ID + snapshot hash ngăn duplicate final.
- Cancellation terminal chỉ sau process tree dừng và temp cleanup scheduled.

## 12. Tests bắt buộc

- Player/render key-frame parity.
- Asset checksum mismatch.
- Font load/timeout và Vietnamese glyphs.
- Cancel giữa render/upload/register.
- Worker crash rồi retry.
- Output duration/FPS/dimensions/codec/audio.
- 16:9/9:16 layout-specific timeline selection.

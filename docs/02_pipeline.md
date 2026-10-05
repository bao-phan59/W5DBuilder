# 02 — Pipeline Tổng Thể

> Loại: Design specification đã đồng bộ artifact contracts  
> Low-level execution: [`implementation/codebase/12_end_to_end_execution.md`](./implementation/codebase/12_end_to_end_execution.md)

## 2.1 Artifact flow

```text
Idea / imported content
  → ScriptDocument candidate
  → approved ScriptDocument
  ├─→ VoiceAsset → TimingDocument
  └──────────────→ ScenePlan
                    ↓
Asset ingest/generation → Asset resources → AssetMap
                    ↓
Script + Timing + ScenePlan + AssetMap + PostprocessConfig
  → TimelineDocument
  → RenderSnapshot
  → RenderOutput Asset
  → Export / signed share link
```

Mỗi mũi tên tạo artifact/resource mới hoặc Job; không ghi đè document cũ. Mọi artifact có schema version, provenance, document hash, input fingerprint và dependency edges.

## 2.2 Các stage

### A. Script

Input: idea, target duration, language/style/tone và provider config snapshot.

Output: `ScriptDocument` candidate gồm narration, entity definitions/instances, keyword ranges, semantic visual instructions và estimated timing.

Candidate phải qua schema + semantic validation và approval policy trước khi trở thành current ScriptDocument. Chi tiết: [Script Engine](./03_script_engine.md).

### B. Voice và timing

Voice job snapshot current ScriptDocument và VoiceConfig, synthesize segment, tạo VoiceAsset, sau đó reconcile provider timing hoặc chạy forced alignment để tạo TimingDocument.

Timing dùng millisecond và half-open spans. Estimate chỉ là fallback; final render không dùng estimated timing khi audio thật đã tồn tại.

### C. Scene planning

Scene planner đọc Script + Timing, group sentences thành narrative scenes, resolve active instance state và layout intent. Scene không đồng nghĩa sentence.

ScenePlan chỉ giữ semantic action/transition family và normalized layout intent. Nó không chứa keyframe, file path hoặc provider object.

### D. Assets

Asset requirements được suy ra từ ScenePlan/entity definitions. User có thể upload, chọn library hoặc tạo ảnh qua provider.

Mọi media đều đi qua:

```text
ingest/quarantine
→ checksum + MIME sniff + media probe + rights inspection
→ sanitize/transcode/rasterize
→ derivative generation
→ ready Asset
```

`AssetMap` liên kết entity instance + visual state với immutable Asset/derivative ID.

### E. Timeline compile

Compiler đọc current Script, Timing, ScenePlan, AssetMap, PostprocessConfig và RenderProfile. Nó quantize millisecond boundaries sang frame, resolve layout box, presets, camera, text và audio tracks.

TimelineDocument là render-ready, deterministic và không chứa signed URL. Continuity validation chặn unintended blank frames/invalid overlap.

### F. Preview và edit

Frontend lấy TimelineDocument cùng controlled asset manifest. Remotion Player và server renderer dùng chung `W5DComposition` và generated types.

Editor command tạo patch có revision precondition. Upstream edit làm downstream artifact stale; UI không được tự coi preview cũ là final-ready.

### G. Final render

Render submit tạo immutable RenderSnapshot gồm exact artifact refs/hashes, asset/font manifest, composition version, profile và rights manifest.

Worker stage assets, render, probe output, upload vào immutable object key và đăng ký Asset trong database. DB registration là visibility boundary; không giả định S3 atomic rename.

### H. Export/publish

Baseline production hỗ trợ download/export và signed/revocable share link. Destination adapter bên ngoài chỉ bật khi có provider lock, OAuth scopes, rights policy và contract tests.

## 2.3 Human approval gates

Các gate có thể cấu hình theo workspace automation policy:

1. Script candidate.
2. Voice/timing quality.
3. Scene/layout proposal.
4. Generated asset selection và rights.
5. Final render confirmation.
6. External publish confirmation.

Auto mode không bỏ validation, provenance, quota, moderation hoặc render readiness.

## 2.4 Invalidation

- Script edit → Timing, ScenePlan, dependent AssetMap mappings, Timeline và render readiness stale.
- VoiceConfig/VoiceAsset edit → Timing và downstream timeline stale; Script không stale.
- Asset replacement → dependent AssetMap/Timeline stale; Script/Timing không stale.
- Postprocess edit → Timeline/RenderSnapshot stale.
- Render output cũ không bị xóa; nó được giữ với source revision và đánh dấu superseded trong UI.

## 2.5 Failure boundary

- Provider failure không làm hỏng current artifact.
- Invalid candidate không được promote.
- Worker crash được xử lý bằng lease/orphan reconciliation.
- Retry giữ nguyên input snapshot/fingerprint.
- Storage object chưa đăng ký trong DB không visible cho client.
- Publish fail không xóa RenderOutput đã thành công.

## 2.6 Nguồn contract

- Domain semantics: [`implementation/03_domain_and_data_contracts.md`](./implementation/03_domain_and_data_contracts.md).
- Artifact graph: [`implementation/codebase/02_contracts_and_artifacts.md`](./implementation/codebase/02_contracts_and_artifacts.md).
- Pipeline functions: [`implementation/codebase/05_script_voice_pipeline.md`](./implementation/codebase/05_script_voice_pipeline.md) đến [`08_render_and_publish_pipeline.md`](./implementation/codebase/08_render_and_publish_pipeline.md).

> Tiếp theo: [03_script_engine.md](./03_script_engine.md)

# 09 — Render Engine

> Loại: Design specification  
> Trạng thái: chưa có Remotion project trong repository. Implementation chuẩn xem
> tại [implementation/codebase/08_render_and_publish_pipeline.md](./implementation/codebase/08_render_and_publish_pipeline.md).

---

## 9.1 Render Strategy

### Two-Pass Rendering

```
Pass 1: PREVIEW RENDER (nhanh)
  → Resolution: 960×540 (half HD)
  → FPS: 30
  → No SFX, simplified effects
  → Target time: < 30s cho 60s video
  → Dùng: User review

Pass 2: FINAL RENDER (chất lượng cao)
  → Resolution: 1920×1080 (Full HD) hoặc 1080×1920 (Vertical)
  → FPS: 30 cho MVP; 60 là profile tùy chọn sau MVP
  → Full effects, color grade
  → Target time: ~2-3x realtime (120s render cho 60s video)
  → Output: MP4 (H.264), WebM (VP9)
```

---

## 9.2 Remotion-Based Render

### Tại Sao Remotion?

- **Code-first**: Animation được định nghĩa bằng React code → dễ debug
- **Frame-accurate**: Render từng frame riêng biệt → không drop frame
- **Preview = Output**: Những gì thấy trong browser là những gì render ra
- **Compositing**: Hỗ trợ nhiều track, layer, compositing tốt
- **Parallelizable**: Render nhiều frame song song → nhanh hơn

### Render Pipeline

```
validated TimelineDocument
    │
    ├─[1] Compile → Remotion Composition
    │     (validated TimelineDocument → React component tree)
    │
    ├─[2] Bundle Remotion composition
    │
    ├─[3] Render frames (parallel, multi-thread)
    │     Frame 0: t=0/30
    │     Frame 1: t=1/30
    │     ...
    │     Frame N: t=N/30
    │
    ├─[4] Encode frames → video
    │     FFmpeg: frames → H.264 MP4
    │
    ├─[5] Mux audio
    │     FFmpeg: video + audio → final.mp4
    │
    └─[6] Post-encode: color grade (LUT apply)
```

---

## 9.3 Export Formats

| Format | Resolution | FPS | Use Case |
|---|---|---|---|
| MP4 (H.264) | 1920×1080 | 30 | MVP, YouTube, Facebook |
| MP4 (H.264) | 1080×1920 | 30/60 | Profile tương lai cho TikTok, Reels, Shorts |
| WebM (VP9) | 1920×1080 | 30/60 | Export profile tương lai |
| GIF | 960×540 | 24 | Thumbnail preview, email |
| Frame sequence | 1920×1080 | 60 | Post-production editing |

---

## 9.4 Render Job System

### Job contract excerpt

Đây là payload minh họa, không thay thế executable schema. Thời lượng output được
probe thành millisecond; media được tham chiếu bằng Asset ID, không bằng local path
hay public URL tùy ý.

```json
{
  "schemaVersion": "1.0",
  "id": "job_01J...",
  "projectId": "prj_01J...",
  "status": "running",
  "renderPass": "final",
  "progress": 0.65,
  "createdAt": "2026-10-05T08:00:00Z",
  "startedAt": "2026-10-05T08:00:03Z",
  "completedAt": null,
  "outputAssetId": null,
  "errorCode": null
}
```

### Job Lifecycle
```
[queued] → [running] → [succeeded]
                   ↘ [failed]
[queued/running] → [cancelling] → [cancelled]
```

Webhook notification khi status thay đổi:
```json
{
  "schemaVersion": "1.0",
  "eventId": "evt_01J...",
  "eventType": "render.completed",
  "jobId": "job_01J...",
  "outputAssetId": "ast_01J...",
  "durationMs": 32500,
  "sizeBytes": 47395635
}
```

> Tiếp theo: [10_agent_api.md](./10_agent_api.md)

# 02 — Kiến Trúc Hệ Thống

## 1. System context

W5D Builder có ba runtime chính:

```text
User / AI Agent
       │
       ▼
Web Editor ───── REST/JSON ───── Backend API
    │                                  │
    │ Remotion Player                  ├── Project repository
    │                                  ├── Asset storage
    └──────── TimelineDocument ────────┤
                                       └── Render runner ── Remotion/FFmpeg
```

UI và agent gọi cùng API. Agent không được bypass validation hoặc ghi trực tiếp vào storage.

## 2. Container responsibilities

### Web Editor

- Hiển thị và chỉnh project.
- Giữ ephemeral UI state như selection, zoom, panel state.
- Preview TimelineDocument.
- Gửi mutation có expected revision.
- Không tự quyết định business rules canonical.

### Backend API

- Xác thực input và quyền truy cập.
- Quản lý project revision và artifact lifecycle.
- Điều phối script, scene, asset, timeline và job services.
- Trả error có cấu trúc.
- Không chứa logic render frame-by-frame.

### Render runtime

- Nhận immutable render snapshot.
- Resolve assets đã được cho phép.
- Render deterministic theo composition version.
- Ghi progress/output/error vào job store.
- Không tự sửa project đang render.

### Storage/repository

- Repository lưu metadata và versioned artifacts.
- Blob storage lưu upload, processed asset, audio và render output.
- Domain chỉ dùng asset ID; path/URL vật lý thuộc storage adapter.

## 3. Dependency direction

```text
API/UI adapters
      ↓
Application services
      ↓
Domain models + validators
      ↑
Repository/provider/render adapters
```

Domain layer PHẢI độc lập với FastAPI, React, Remotion SDK và provider SDK. Adapter phụ thuộc domain interface, không ngược lại.

## 4. Pipeline boundaries

Mỗi bước tạo một artifact có version và provenance:

| Bước | Input | Output |
|---|---|---|
| Script authoring | idea/manual input | ScriptDocument |
| Voice alignment | ScriptDocument + voice config | TimingDocument |
| Scene planning | ScriptDocument + optional TimingDocument | ScenePlan |
| Asset assignment | ScenePlan + Asset library | AssetMap |
| Timeline compose | ScenePlan + AssetMap + TimingDocument | TimelineDocument |
| Render | immutable project snapshot | RenderJob + output asset |

MVP cho phép TimingDocument được tạo từ estimated durations thay vì TTS thật.

## 5. Sync và async

Synchronous operations:

- Project reads và metadata updates.
- Script validation.
- Small deterministic scene/timeline composition.
- Asset metadata update.

Asynchronous jobs:

- AI generation.
- TTS/alignment.
- Background removal.
- Preview/final render.
- Media probing/transcoding nếu vượt ngưỡng request time.

API không giữ HTTP request mở trong suốt tác vụ dài. Tác vụ dài trả `jobId` và được poll; webhook/SSE là extension sau.

## 6. Project revision flow

1. Client đọc project revision `N`.
2. Client gửi strong ETag đã nhận trước đó, ví dụ `If-Match: "prj-N-hash"`; API parse thành opaque version precondition và revision `N` cho application layer.
3. Server validate và commit atomically.
4. Server trả revision `N+1`.
5. Nếu current revision khác `N`, server trả `412 REVISION_PRECONDITION_FAILED` cùng current revision/ETag.

Render tạo snapshot gắn revision. Thay đổi project sau đó không được làm output job thay đổi.

## 7. Failure boundaries

- Provider failure không làm hỏng Project aggregate.
- Asset processing tạo derivative mới; không ghi đè original.
- Timeline compose failure giữ lại ScenePlan hợp lệ.
- Render retry dùng cùng snapshot/idempotency key.
- Error log có correlation ID nhưng không ghi secret hoặc raw media content.

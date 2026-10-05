# 09 — Frontend Editor Codebase

## 1. File tree

```text
frontend/src/
├── app/
│   ├── App.tsx
│   ├── router.tsx
│   ├── providers.tsx
│   └── error-boundary.tsx
├── api/
│   ├── client.generated.ts
│   ├── query-client.ts
│   ├── errors.ts
│   └── events.ts
├── features/
│   ├── projects/
│   ├── script/
│   ├── voice/
│   ├── assets/
│   ├── scenes/
│   ├── timeline/
│   ├── postprocess/
│   └── render/
├── editor/
│   ├── EditorShell.tsx
│   ├── player/
│   ├── canvas/
│   ├── timeline/
│   ├── commands/
│   ├── selection/
│   └── store/
└── test/
```

## 2. State split

TanStack Query quản lý server state; Zustand quản lý editor state. Không duplicate full Project/Timeline vào cả hai.

### `editor/store/editor-store.ts`

State:

- `projectId`, `selectedSceneId`, `selectedObjectIds`.
- `playheadFrame`, `isPlaying`, `zoom`, `viewportPan`.
- `activeTool`, panels, draft commands.
- `saveState`, conflict info.

Actions:

- `selectObjects(ids, mode)`.
- `setPlayhead(frame)`.
- `setPlaying(value)`.
- `beginTransform(objectIds)` / `previewTransform(delta)` / `commitTransform()`.
- `pushCommand(command)` / `undo()` / `redo()`.
- `clearProjectSession()`.

Persisted server document không được mutate trực tiếp trong store.

## 3. API hooks

### `features/projects/api.ts`

- `useProject(projectId)` trả data + ETag/revision.
- `useUpdateProject()` gửi `If-Match`, xử lý `412 REVISION_PRECONDITION_FAILED`.
- `useArtifact(projectId, kind, revision?)`.
- `useArtifactHistory(projectId, kind)`.

### Job hooks

- `useSubmitJob(operation)` tự tạo idempotency key theo user action.
- `useJob(jobId)` polling fallback.
- `useProjectEvents(projectId)` SSE, reconnect với Last-Event-ID.
- `useCancelJob()` và `useRetryJob()`.

Query invalidation dựa trên event type/project revision; SSE payload không trực tiếp overwrite cache phức tạp.

## 4. Editing commands

### `editor/commands/types.ts`

`EditorCommand` methods:

- `apply(document) -> document`.
- `invert(documentBefore) -> EditorCommand`.
- `toPatch() -> JsonPatchOperation[]`.
- `mergeWith(next) -> EditorCommand | null` cho drag liên tục.

Command types: move/resize object, change preset, adjust frame range, edit text, assign asset, change postprocess.

Undo/redo chỉ local trước save. Sau remote conflict, history được rebase hoặc clear với thông báo; không replay mù lên revision mới.

## 5. Save coordinator

### `editor/store/save-coordinator.ts`

| Hàm | Input | Mô tả |
|---|---|---|
| `queuePatch` | command patch | Debounce và merge |
| `flush` | reason | Gửi patch + If-Match |
| `handleConflict` | server snapshot, local patches | Tạo conflict model |
| `resolveConflict` | reload/reapply/manual | Controlled resolution |
| `beforeUnloadGuard` | save state | Cảnh báo unsaved changes |

Server vẫn validate toàn bộ document. Client validation chỉ cải thiện UX.

## 6. Player integration

### `editor/player/ProjectPlayer.tsx`

Props: TimelineDocument, RenderSnapshot-compatible asset manifest, playhead callbacks, editor overlay flag.

Functions/hooks:

- `usePlayerController()` trả seek/play/pause/currentFrame.
- `buildPlayerProps(timeline, manifest) -> W5DCompositionProps` dùng cùng serializer với render snapshot.
- `preloadVisibleAssets(frame, lookaheadFrames)`.
- `handleBufferState(state)` pause UI và hiển thị diagnostics.

Không dùng browser-bundler để chạy code user. Composition là trusted application code; project chỉ cung cấp data props.

## 7. Canvas overlay

### `editor/canvas/CanvasOverlay.tsx`

- `screenToCompositionPoint(clientPoint, viewport, letterbox) -> NormalizedPoint`.
- `compositionToScreenBox(box, viewport) -> ScreenBox`.
- `hitTest(point, resolvedObjects) -> ObjectId[]`.
- `computeTransform(selection, pointerDelta, modifiers) -> TransformPreview`.
- `snapTransform(transform, guides, threshold) -> TransformPreview`.

Overlay không nằm trong composition output. x/y luôn là anchor point theo geometry contract.

## 8. Timeline UI

### `editor/timeline/`

- `TimelineView({tracks, totalFrames, fps})`.
- `useTimelineScale(containerWidth, zoom, totalFrames)`.
- `frameToX(frame, scale)` / `xToFrame(x, scale)`.
- `buildVisibleRows(tracks, viewport) -> rows`.
- `moveItem(itemId, deltaFrames, snapPolicy) -> EditorCommand`.
- `resizeItem(itemId, edge, deltaFrames) -> EditorCommand`.

Virtualize rows/items khi project lớn. Frame tick cập nhật imperative/ref hoặc isolated store selector để không re-render toàn editor.

## 9. Feature panels

- Script: sentence editor, entity/range validation, generation candidates.
- Voice: voice config, preview, alignment warnings.
- Assets: upload/generate/search, processing state, assignment by instance/visual state.
- Scene: scene grouping/layout template/constraints.
- Animation: semantic intent, resolved preset, frame ranges.
- Postprocess: camera/audio/effects with capability validation.
- Render: profile, readiness report, job progress, output/publish.

## 10. Authorization UX

UI ẩn/disable action theo capability nhưng backend authorization là bắt buộc. 403 phải hiển thị rõ, không biến thành “resource missing” chung cho owner UI.

## 11. Accessibility/performance tests

- Keyboard navigation cho editor command chính.
- Screen-reader label/status live region cho jobs/errors.
- Reduced-motion cho UI chrome.
- 1.000 timeline items vẫn scrub đạt target frame rate theo performance budget.
- Memory không tăng vô hạn khi đổi project/job events.
- Browser matrix Chrome/Edge/Firefox/Safari cho Player và media formats đã công bố.

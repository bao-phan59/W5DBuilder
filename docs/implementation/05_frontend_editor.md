# 05 — Frontend Editor

## 1. Mục tiêu

Editor là client của domain contract, không phải một pipeline riêng. Nó phải chỉnh project an toàn, preview đúng composition và hiển thị rõ validation/job state.

## 2. Cấu trúc target

```text
frontend/src/
├── app/                 # shell, routing, providers
├── api/                 # generated/typed client
├── features/
│   ├── project/
│   ├── script/
│   ├── assets/
│   ├── scene/
│   ├── timeline/
│   └── render/
├── player/              # Remotion Player integration
├── store/               # editor/session state
├── components/          # shared accessible UI
└── test/
```

Feature module sở hữu UI và commands của nó; shared components không biết domain workflow.

## 3. State ownership

### Server state

- Project và artifact revisions.
- Asset/job status.
- Validation results.
- Render outputs.

Server state được cache qua query layer hoặc API client strategy; không copy toàn bộ sang Zustand nếu không cần.

### Editor state

- Selected scene/object.
- Playhead frame, playing state.
- Zoom/pan của editor viewport.
- Open panels, tool mode, unsaved local patch.

Zustand phù hợp với editor state. Undo/redo lưu command hoặc patch có giới hạn, không snapshot binary/large document tùy tiện.

## 4. Editing model

- UI edit tạo local patch.
- Patch được validate nhẹ trước khi gửi.
- Save gửi expected project revision.
- Conflict không tự động overwrite; UI hiển thị reload/merge choice.
- Autosave có debounce và trạng thái `saving/saved/conflict/error` rõ ràng.
- Destructive action có confirmation và khả năng phục hồi khi hợp lý.

## 5. Canvas và player

- Remotion Player render TimelineDocument canonical.
- Selection/handles là overlay editor, không xuất hiện trong render.
- Pointer coordinates được chuyển sang normalized content coordinates.
- Letterbox area không tham gia hit testing.
- Scrub phải seek theo frame integer.
- Missing asset hiển thị placeholder có ID và warning, không crash player.

MVP chỉ cần select, drag, resize cơ bản nếu các thao tác đó nằm trong acceptance scope. Rotation/path editing có thể deferred.

## 6. Timeline UI

Timeline tối thiểu gồm:

- Playhead theo frame.
- Scene spans và object spans.
- Voice/audio lane nếu TimingDocument tồn tại.
- Zoom scale nhưng snap vẫn theo frame.
- Validation marker.
- Chọn object đồng bộ với canvas.

Không cho phép tạo range âm hoặc `endFrame <= startFrame`. UI constraint không thay thế server validation.

## 7. Script và asset workflow

- Script editor hiển thị sentence order, entity instructions và validation issues.
- Asset panel phân biệt original, derivative và placeholder.
- Assignment hiển thị entity instance, không chỉ entity label.
- Processing/generation là job state; UI không giả định hoàn thành ngay.
- Provider capability quyết định control nào được bật.

## 8. Performance

- Không re-render toàn timeline ở mỗi frame tick.
- Player time không ghi vào persisted project state.
- Large lists dùng memoization/virtualization khi cần đo được.
- Thumbnail và preview dùng derivative phù hợp, không tải original lớn mặc định.
- Abort request khi user đổi project hoặc hủy tác vụ.

## 9. Accessibility

- Toàn bộ command chính có keyboard path.
- Control có label và focus state.
- Timeline/canvas action quan trọng có alternative form input.
- Không chỉ dùng màu để biểu thị error/status.
- Reduced-motion preference áp dụng cho editor chrome, không thay đổi nội dung video project.

## 10. Frontend Definition of Done

- Golden project load và preview được.
- Play/pause/scrub frame-accurate.
- Selection đồng bộ canvas/timeline.
- Save/conflict/error states có tests.
- Missing asset và invalid document không tạo blank/crash.
- Build, lint, component tests và browser happy path pass.

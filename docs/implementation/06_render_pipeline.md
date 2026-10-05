# 06 — Render Pipeline

## 1. Nguyên tắc single composition

Preview và final output PHẢI dùng cùng composition code và TimelineDocument. Khác biệt chỉ nằm ở render profile hoặc quality flags đã được khai báo, không phải hai implementation animation.

```text
TimelineDocument + resolved AssetManifest
                │
                ▼
        W5D Remotion Composition
          ├── Remotion Player
          └── Remotion renderer → MP4
```

## 2. Render input snapshot

Render job nhận immutable snapshot gồm:

- Project/revision.
- Timeline/revision/schema version.
- Composition version.
- Render profile.
- Asset manifest với checksum và controlled URI.
- Audio manifest.

Renderer không đọc “latest project” trong lúc chạy.

## 3. Render profile

MVP profile:

| Field | Giá trị |
|---|---|
| Width × height | 1920×1080 |
| FPS | 30 |
| Codec/container | H.264/MP4 |
| Pixel format | yuv420p |
| Audio | AAC nếu có |
| Color space | sRGB/Rec.709 baseline |

Preview player có thể render viewport nhỏ hơn nhưng composition dimensions và frame semantics không đổi.

## 4. Frame semantics

- Tổng duration là `totalFrames / fps`.
- Track item dùng range `[startFrame, endFrame)`.
- Animation preset là pure function của local frame và validated parameters.
- Không dùng wall clock, random không seed hoặc network fetch trong frame render.
- Randomized effect phải dùng deterministic seed lưu trong TimelineDocument.

## 5. Asset resolution

- Renderer chỉ nhận asset đã resolve từ ID sang manifest entry.
- Check checksum/availability trước frame đầu.
- Font và system asset phải được bundle/pin.
- Remote URL tùy ý không được fetch trong render.
- Missing required asset làm job fail trước rendering; optional asset dùng declared placeholder policy.

## 6. Layer model

Thứ tự logical:

1. Background.
2. Ambient/decorative effects.
3. Main objects.
4. Connectors/annotations.
5. Text overlays.
6. Foreground effects.
7. Editor overlay — player only, không thuộc composition output.

Z-index phải deterministic. Hai item cùng z-index dùng stable document order.

## 7. Audio

- Audio master timeline dùng millisecond source spans được chuyển sang frames theo policy thống nhất.
- Voice là primary track.
- Music ducking/SFX nằm sau MVP nhưng track model phải mở rộng được.
- Không tự stretch voice để khớp animation; composer điều chỉnh animation quanh audio.
- Final duration không được cắt voice tail.

## 8. One-shot validation

Trước render final:

- Không có unintended visual gap vượt threshold.
- Background hoặc intentional bridge luôn visible.
- Enter/exit overlap không tạo duplicate instance state.
- Camera không làm content bắt buộc ra ngoài safe area.
- Text không vượt bounding box theo font metrics thực.

Intentional blank/solid-color bridge phải được khai báo, không phát sinh do thiếu object.

## 9. Job execution

- Validate snapshot.
- Resolve/bundle assets.
- Render frames.
- Encode/mux.
- Probe output.
- Register output asset.
- Mark job succeeded.

Failure trả stage, retryable flag và safe diagnostic. Partial output không được công bố như final asset.

## 10. Render quality tests

MVP không cần pixel-perfect snapshot cho mọi frame. Bắt buộc kiểm tra:

- Composition load được.
- Total frames/duration đúng.
- Asset references đầy đủ.
- Một số key frame có image snapshot ổn định với tolerance.
- Output probe đúng codec, dimensions, FPS và audio presence.
- Player/render cùng timeline cho kết quả key frame tương đương.

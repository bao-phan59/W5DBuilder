# 01 — Tổng Quan Hệ Thống W5D Builder

> Loại: Design specification  
> Trạng thái: Target product behavior; chưa phản ánh tính năng đã implement  
> Chuẩn triển khai: [implementation/README.md](./implementation/README.md)

---

## 1.1 Mục Tiêu Dự Án

W5D Builder giải quyết một vấn đề cụ thể: **tạo video explainer chất lượng cao đòi hỏi nhiều công sức thủ công** — viết kịch bản, tìm ảnh, dàn cảnh, làm animation, ghép audio. Quy trình này thường mất hàng ngày đến hàng tuần.

Mục tiêu của W5D Builder là rút ngắn quy trình này xuống còn **vài giờ hoặc ít hơn**, với chất lượng video đạt chuẩn có thể publish được.

### Định Nghĩa "Video W5D"

Video W5D là thể loại explainer/whiteboard video với đặc trưng:
- **Nền tối giản** — trắng, đen, hoặc gradient nhẹ — không phân tâm
- **Nhân vật & vật thể cutout** xuất hiện, di chuyển, tương tác theo câu chuyện
- **Text keyword** bật ra đúng lúc để nhấn mạnh điểm quan trọng
- **Giọng đọc (voiceover)** dẫn dắt toàn bộ nội dung
- **Hiệu ứng vẽ tay** tạo cảm giác thân thiện, handmade
- **One-shot flow** — video là một mạch liên tục, không có slide riêng biệt

---

## 1.2 Triết Lý Thiết Kế

### "Auto-first, Control-always"
Hệ thống luôn cố gắng tự động hóa mọi thứ có thể. Nhưng tại mỗi bước, user có thể override bất kỳ quyết định nào.

### "Confirm before commit"
Mỗi bước tự động đều có preview và xác nhận trước khi chuyển bước tiếp. Không có gì xảy ra ngầm không thể đảo ngược.

### "One-shot video philosophy"
Video là một luồng kể chuyện liên tục. Không có "slide 1", "slide 2". Thay vào đó:
- Các phần tử cũ **exit ra ngoài khung hình** khi câu kết thúc
- Các phần tử mới **enter từ ngoài vào** khi câu mới bắt đầu
- Camera/viewport có thể **pan, zoom** nhẹ để tạo cảm giác chuyển động liên tục
- Không bao giờ có màn hình trống hoàn toàn giữa các scene

### "Agent-native design"
Mọi chức năng đều được thiết kế để có thể gọi từ AI agent:
- REST API với JSON schema rõ ràng
- Mỗi bước nhận input JSON và trả về output JSON
- Webhook notify khi job dài xong
- Idempotent operations — gọi lại cùng request cho cùng kết quả

---

## 1.3 Luồng Người Dùng Tổng Quát

```
1. USER đưa vào ý tưởng (text tự do)
        ↓
2. AGENT sinh kịch bản W5D đầy đủ
        ↓
3. USER review + chỉnh sửa kịch bản (optional)
        ↓
4. SYSTEM tự động:
   - Tách câu theo beat
   - Highlight keyword
   - Lên danh sách entities cần ảnh
   - Generate scene plan (bố cục, vị trí, animation type)
        ↓
5. USER (hoặc AI) cung cấp ảnh cho từng entity
   - Upload từ máy
   - Generate bằng AI từ prompt gợi ý
   - Tìm từ asset library có sẵn
        ↓
6. SYSTEM auto-assign ảnh vào scene plan
   - Tách nền tự động
   - Preview bố cục
        ↓
7. USER confirm hoặc chỉnh layout/animation
        ↓
8. SYSTEM render preview (low-res, nhanh)
        ↓
9. USER review, điều chỉnh postprocess (transitions, effects)
        ↓
10. SYSTEM render final video
```

---

## 1.4 Các Loại Asset Được Hỗ Trợ

Đây là capability matrix mục tiêu. MVP đầu tiên chỉ bắt buộc ảnh tĩnh và placeholder; các format động được mở theo milestone trong roadmap.

| Loại | Format | Ghi Chú |
|---|---|---|
| Ảnh tĩnh | PNG, JPG, WebP, SVG | Tự động tách nền |
| GIF | GIF | Hỗ trợ loop hoặc play-once |
| Video clip | MP4, WebM | Hỗ trợ loop hoặc play-once, có thể mute |
| SVG animation | SVG (với SMIL/CSS) | Render trực tiếp |
| Lottie | JSON (Lottie format) | Animation vector phong phú |

### Playback Control cho GIF & Video

```jsonc
{
  "assetId": "ast_01J...",
  "type": "gif",
  "playback": {
    "mode": "loop",          // "loop" | "once" | "ping-pong"
    "speed": 1.0,            // 0.5 = chậm, 2.0 = nhanh
    "startTrigger": "sceneEnter",
    "stopTrigger": "sceneExit",
    "loopCount": null        // null = vô hạn, hoặc số nguyên
  }
}
```

Đây là cấu hình authoring; compiler resolve trigger thành frame range trước khi
render. Asset resource chuẩn không nhúng path hay URL storage trực tiếp.

---

## 1.5 Các Thành Phần Hệ Thống

```
┌─────────────────────────────────────────────────────────┐
│                    W5D BUILDER                          │
│                                                         │
│  [Script Engine]  ──→  [Scene Planner]                  │
│        ↓                    ↓                           │
│  [Voice Generator]   [Layout Engine]                    │
│        ↓                    ↓                           │
│  [Timing Sync]  ──→  [Animation Composer]               │
│                            ↓                            │
│  [Asset Manager]  ──→  [Postprocess Layer]              │
│        ↓                    ↓                           │
│  [AI Image Gen]    [Render Engine]                      │
│                            ↓                            │
│              [Agent API Gateway]                        │
└─────────────────────────────────────────────────────────┘
```

> Tiếp theo: [02_pipeline.md](./02_pipeline.md) — Pipeline chi tiết từng bước

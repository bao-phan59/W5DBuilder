# 05 — Asset Manager

> Loại: Design specification  
> Trạng thái: capability mục tiêu; MVP chỉ bắt buộc image/placeholder và local storage.

> Quản lý toàn bộ tài nguyên hình ảnh: ảnh tĩnh, GIF, video clip, Lottie animations.

---

## 5.1 Tổng Quan

Asset Manager là kho lưu trữ trung tâm cho tất cả tài nguyên hình ảnh của hệ thống.
Nó xử lý upload, tách nền, gắn tag, tìm kiếm, và mapping asset vào entities trong scene.

---

## 5.2 Các Loại Asset Được Hỗ Trợ

### 5.2.1 Ảnh Tĩnh (Static Image)

| Format | Tách Nền | Ghi Chú |
|---|---|---|
| PNG | Tự động | Nếu đã có alpha channel thì bỏ qua |
| JPG / JPEG | Tự động | Nên có nền trắng/đơn sắc |
| WebP | Tự động | |
| SVG | Không cần | Vector, scale vô hạn |

**Xử lý tách nền:**
- Tool: `rembg` (model U2Net) — tốt nhất cho nền trắng/đơn sắc
- Fallback: `remove.bg` API (chính xác hơn, mất phí)
- Output: PNG với alpha channel (transparent background)
- Quality score: 0-100, dưới 60 → cảnh báo user

### 5.2.2 GIF

GIF hỗ trợ đầy đủ với các tùy chọn playback:

```json
{
  "type": "gif",
  "playback": {
    "mode": "loop",
    "speed": 1.0,
    "startTrigger": "sceneEnter",
    "stopTrigger": "sceneExit",
    "loopCount": null
  }
}
```

**Mode options:**
- `loop` — phát vô hạn
- `once` — phát 1 lần rồi dừng ở frame cuối
- `ping-pong` — phát tới rồi phát ngược
- `count` — phát N lần (kết hợp với `loopCount`)

**Tách nền GIF:**
- Xử lý từng frame riêng bằng rembg
- Giữ transparency per-frame
- Cảnh báo nếu GIF có nhiều hơn 60 frames (performance)

### 5.2.3 Video Clip (MP4, WebM)

Video clip được embed như một "texture" trong scene:

```json
{
  "type": "video",
  "playback": {
    "mode": "loop",
    "speed": 1.0,
    "muted": true,
    "startTrigger": "sceneEnter",
    "stopTrigger": "sceneExit",
    "trimStartMs": 0,
    "trimEndMs": null
  }
}
```

**Lưu ý quan trọng:**
- Video clip thường dùng làm background hoặc element đặc biệt
- Nếu video có nền xanh (green screen) → hỗ trợ chroma key removal
- Khuyến nghị dùng WebM với alpha channel cho video transparent
- Production hard limit: 10 phút/500 MiB theo policy chuẩn; khuyến nghị clip scene
  không quá 30 giây để giảm decode/render cost

### 5.2.4 Lottie Animation

Lottie là JSON-based animation format, rất phù hợp cho W5D:

```json
{
  "type": "lottie",
  "sourceAssetId": "ast_01J...",
  "playback": {
    "mode": "once",
    "speed": 1.0,
    "startFrame": 0,
    "endFrame": null
  }
}
```

**Nguồn Lottie:**
- LottieFiles.com (thư viện miễn phí/mất phí)
- Adobe After Effects + Bodymovin export
- Tạo tay bằng code

---

## 5.3 Asset resource excerpt

Ví dụ sau mô tả API resource, không phải schema đầy đủ. Binary/object key không
được trả như local path; API cấp derivative IDs và signed URL theo quyền khi client
cần tải. Schema executable và storage semantics xem bộ implementation docs.

```json
{
  "schemaVersion": "1.0",
  "id": "ast_01J...",
  "workspaceId": "wsp_01J...",
  "projectId": "prj_01J...",
  "name": "elephant_happy",
  "displayName": "Voi Vui",
  "mediaType": "image",
  "mimeType": "image/png",
  "status": "ready",
  "checksumSha256": "<64 lowercase hex characters>",
  "metadata": {
    "width": 1200,
    "height": 800,
    "hasTransparency": true,
    "sizeBytes": 245000,
    "durationMs": null
  },
  "tags": ["animal", "elephant", "happy", "cute"],
  "category": "animal",
  "playback": null,
  "origin": "upload",
  "derivativeIds": ["ast_01K..."],
  "createdAt": "2026-10-05T08:00:00Z",
  "updatedAt": "2026-10-05T08:00:00Z"
}
```

---

## 5.4 Tag System

### 5.4.1 Tag Categories

```
CATEGORY TAGS (1 per asset, bắt buộc):
  animal, person, object, location, icon,
  arrow, meme, shape, text, decoration, background

CONTENT TAGS (nhiều, auto + manual):
  Mô tả nội dung: elephant, happy, running, eating, office...

STYLE TAGS:
  flat, cartoon, realistic, sketch, pixel, 3d, minimalist

COLOR TAGS (auto từ dominant color):
  red, blue, green, yellow, grey, colorful, monochrome, dark, light

SPECIAL TAGS:
  transparent, has-alpha, vector, animated, loop, hand-drawn
```

### 5.4.2 Auto-Tagging (AI Vision)

Dùng CLIP model (OpenAI) hoặc Google Vision API để auto-tag:

```python
from transformers import CLIPProcessor, CLIPModel

# Candidates
candidates = ["animal", "elephant", "person", "arrow", "meme", 
              "cartoon", "realistic", "happy", "sad", ...]

# Score similarity
scores = clip_model.similarity(image, candidates)
# Tags với score > 0.3 được thêm vào auto_tags
```

### 5.4.3 Search Logic

```
Tìm kiếm: "voi vui"
    ↓
Tokenize: ["voi", "vui"]
    ↓
Match trên:
  - name: "elephant_happy" → 0 match
  - display_name: "Voi Vui" → 2 match → score cao nhất
  - tags.manual: ["animal", "elephant", "happy"] → 1 match ("vui" ~ "happy")
  - tags.auto: ["mammal", "wildlife"] → 0 match
    ↓
Rank + trả về kết quả
```

---

## 5.5 Background Removal Pipeline

```
INPUT: image file
    │
    ├─[1] Detect image type (jpg/png/gif/video)
    │
    ├─[2] Check if already has transparency (PNG with alpha)
    │     └─ Nếu có → skip removal, score = 100
    │
    ├─[3] Detect background color
    │     ├─ Nếu near-white (#F0F0F0+) → rembg với optimize_for_white=True
    │     ├─ Nếu green screen → chroma key removal
    │     └─ Khác → rembg standard
    │
    ├─[4] Run rembg
    │     └─ output: PNG với alpha channel
    │
    ├─[5] Calculate quality score
    │     ├─ Edge smoothness score (0-100)
    │     ├─ Artifact detection (fringe/halo check)
    │     └─ Overall score
    │
    ├─[6] Apply post-processing
    │     ├─ Edge feathering (nếu jagged)
    │     ├─ Subtle drop shadow
    │     └─ Color normalize
    │
    └─[7] Save processed file + generate thumbnail
```

**Quality Score Thresholds:**
- **90-100**: Excellent, tự động chấp nhận
- **70-89**: Good, hiển thị preview để user confirm
- **50-69**: Fair, cảnh báo user và suggest manual refine
- **< 50**: Poor, yêu cầu user upload ảnh khác hoặc tự xử lý

---

## 5.6 Asset Library

Hệ thống có sẵn một **Built-in Asset Library** bao gồm:

```
CATEGORY: Arrows & Connectors
  ├── arrow_right_hand.png
  ├── arrow_left_hand.png
  ├── arrow_curved_lottie.json
  ├── arrow_bounce.gif
  └── connector_dotted.svg

CATEGORY: Memes & Expressions  
  ├── thinking_face.png
  ├── thumbs_up.png
  ├── light_bulb_hand.png
  ├── question_mark.svg
  └── exclamation_animated.lottie

CATEGORY: Shapes
  ├── circle_highlight.svg
  ├── box_sketch.png
  ├── speech_bubble.svg
  └── underline_hand.gif

CATEGORY: Icons
  ├── check_mark.svg
  ├── cross_mark.svg
  ├── star_fill.svg
  ├── clock_animated.lottie
  └── loading_spinner.gif

CATEGORY: Backgrounds (plain)
  ├── white_clean.png
  ├── cream_texture.jpg
  ├── dark_charcoal.jpg
  ├── gradient_blue.png
  └── field_illustration.jpg
```

---

## 5.7 AI Image Generation Integration

Khi entity chưa có ảnh, user có thể yêu cầu AI generate:

### Request Schema
```json
{
  "entity_id": "e_elephant",
  "prompt": "cute cartoon elephant eating grass, white background, flat illustration style",
  "style": "flat | cartoon | realistic | sketch | pixel",
  "background": "white | transparent | none",
  "aspect_ratio": "1:1 | 4:3 | 3:4 | 16:9",
  "engine": "dalle3 | flux | midjourney",
  "variations": 4
}
```

### Prompt Engineering cho W5D Assets

Hệ thống tự động thêm suffix vào prompt của user để đảm bảo output phù hợp:

```
User prompt: "cute elephant"
    ↓
System enhanced:
"cute elephant, white background, clean cutout, flat cartoon illustration style,
no shadows, bold outlines, vibrant colors, suitable for explainer video,
isolated subject, centered composition"
```

### Generated Image → Asset Flow
1. Generate 4 variations
2. Hiển thị để user chọn
3. Auto tách nền
4. Lưu vào asset library
5. Auto-assign vào entity đang chờ

> Tiếp theo: [06_scene_layout.md](./06_scene_layout.md)

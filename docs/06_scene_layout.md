# 06 — Scene Layout & Bố Cục Tự Động

> Loại: Design specification  
> Quy tắc dữ liệu bắt buộc xem tại [implementation/03_domain_and_data_contracts.md](./implementation/03_domain_and_data_contracts.md).

> Module quan trọng nhất về mặt visual — quyết định "cái gì đứng ở đâu trong khung hình".

---

## 6.1 Triết Lý Bố Cục

### One-Shot Canvas

Video W5D được coi như một **canvas duy nhất** — không có "màn hình slide 1", "slide 2".
Thay vào đó, các vật thể **đi vào và đi ra khỏi canvas** liên tục. Canvas luôn sống động.

```
t=0s                t=4s                t=7s
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  🐘 🐘 🐘   │    │    🐘 🐘    │    │      🐘      │
│              │ →  │              │ →  │              │
│              │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
  Ba voi enter        Voi trái exit        Voi phải exit
  từ dưới lên          sang trái             sang phải
```

Không có màn hình trắng trống. Luôn có ít nhất 1 element visible.

---

## 6.2 Layout Template System

### 6.2.1 Tại Sao Dùng Template?

Thay vì để LLM tự tính tọa độ pixel (không ổn định), hệ thống dùng **Layout Templates** —
các mẫu bố cục được thiết kế sẵn, đảm bảo đẹp và cân đối.

LLM chỉ được đề xuất grouping, narrative role và layout hint. `select_template`,
`assign_instances_to_slots` và `solve_layout` mới là bước quyết định cuối: chạy
deterministic, safe-area aware và có validator. LLM không ghi pixel, frame hay
keyframe trực tiếp.

### 6.2.2 Template Library

#### Templates cho 1 Entity
```
SINGLE_CENTER         SINGLE_LEFT           SINGLE_RIGHT
┌────────────┐        ┌────────────┐        ┌────────────┐
│     ███    │        │  ███       │        │       ███  │
│            │        │            │        │            │
└────────────┘        └────────────┘        └────────────┘
slot: [center]        slot: [left]          slot: [right]

SINGLE_LARGE (focal point)
┌────────────┐
│    ████    │
│    ████    │
└────────────┘
slot: [center], box lớn hơn preset thường
```

#### Templates cho 2 Entities
```
DUAL_SYMMETRIC        DUAL_COMPARE          DUAL_STORY
┌────────────┐        ┌────────────┐        ┌────────────┐
│  ███  ███  │        │ ██  │  ██ │        │  ███       │
│            │        │     │     │        │       ███  │
└────────────┘        └────────────┘        └────────────┘
slot: [left,right]   slot: [left,right]    slot: [left,right]
                     + vertical divider    + vertical offset

HERO_SIDEKICK
┌────────────┐
│  ████  ██  │
│            │
└────────────┘
slot: [center(large), right(small)]
```

#### Templates cho 3 Entities
```
TRIPLE_EVEN           TRIPLE_PYRAMID        TRIPLE_LEAD
┌────────────┐        ┌────────────┐        ┌────────────┐
│ ██  ██  ██ │        │    ██      │        │ ████ █  █  │
│            │        │  ██  ██    │        │            │
└────────────┘        └────────────┘        └────────────┘
slot:[l,c,r]         slot:[top,bl,br]      slot:[c(lg),l,r]
```

#### Templates cho 4+ Entities
```
QUAD_GRID             ROW_4                 CROWD
┌────────────┐        ┌────────────┐        ┌────────────┐
│  ██    ██  │        │ █  █  █  █ │        │ █ █ █ █ █  │
│  ██    ██  │        │            │        │   █ █ █    │
└────────────┘        └────────────┘        └────────────┘
```

### 6.2.3 Template Selection Logic

Scene planner nhận số entity active, narrative role, `sceneHint`, profile và layout
trước đó rồi chấm điểm template. Khi bằng điểm, template ID được dùng làm
deterministic tie-break. Bảng dưới là rule/scoring input, không phải enum action
của ScriptDocument.

```
Quy tắc chọn template tự động:

count == 1:
  sceneHint == "focal" → SINGLE_LARGE
  sceneHint == "intro" → SINGLE_CENTER
  default → SINGLE_CENTER

count == 2:
  narrativeRole == "compare" → DUAL_COMPARE
  narrativeRole == "interact" → DUAL_SYMMETRIC
  narrativeRole == "story" → DUAL_STORY
  default → DUAL_SYMMETRIC

count == 3:
  one entity is "primary" → TRIPLE_LEAD
  all equal importance → TRIPLE_EVEN
  sceneHint == "hierarchy" → TRIPLE_PYRAMID
  default → TRIPLE_EVEN

count == 4:
  default → QUAD_GRID
  linear process → ROW_4

count >= 5:
  → CROWD template với staggered positioning
```

---

## 6.3 Slot System — Tọa Độ Thực Tế

Ví dụ dưới đây dùng design space **1920×1080**. Implementation phải lưu tọa độ normalized hoặc có quy tắc chuyển đổi profile rõ ràng; không được giả định mọi output đều 16:9.

```json
{
  "templateId": "TRIPLE_EVEN",
  "canvas": { "width": 1920, "height": 1080 },
  "slots": {
    "left":   { "x": 0.167, "y": 0.537, "anchor": "bottom_center", "maxWidth": 0.208, "maxHeight": 0.463 },
    "center": { "x": 0.500, "y": 0.537, "anchor": "bottom_center", "maxWidth": 0.208, "maxHeight": 0.463 },
    "right":  { "x": 0.833, "y": 0.537, "anchor": "bottom_center", "maxWidth": 0.208, "maxHeight": 0.463 }
  },
  "textZone": { "x": 0.500, "y": 0.111, "width": 0.729, "height": 0.185 },
  "safeArea": { "top": 0.074, "bottom": 0.093, "left": 0.042, "right": 0.042 }
}
```

**Quy tắc fit asset vào slot:**
- Asset được fit vào `maxWidth × maxHeight`, giữ tỉ lệ gốc; kết quả là normalized box
- Anchor point xác định điểm neo (bottom_center = chân vật thể chạm đất)
- Asset không được ra ngoài `safeArea`

---

## 6.4 Scene Planning Logic Chi Tiết

### 6.4.1 Quy Trình Scene Planning

```
Input: ScriptDocument + TimingDocument
    │
    ├─[1] Group sentences thành scenes
    │     Quy tắc: Một scene = một "trạng thái" của canvas
    │     Scene change khi: entity vào/ra, background thay đổi
    │
    ├─[2] Với mỗi scene:
    │     ├─ Đếm entities active
    │     ├─ Chọn layout template
    │     ├─ Assign entities vào slots
    │     └─ Xác định background
    │
    ├─[3] Xác định transition giữa scenes
    │     ├─ Entity nào exit? (semantic action `exit`)
    │     ├─ Entity nào enter? (semantic action `enter`)
    │     └─ Entity nào stay/move/emphasize?
    │
    └─[4] Validate one-shot flow
          └─ Đảm bảo không có "gap" trống giữa scenes
```

### 6.4.2 Entity Continuity Rules

Khi entity "stay" từ scene này sang scene khác:
1. **Position**: Nếu không đổi slot → giữ nguyên vị trí
2. **Box**: Giữ normalized box; `emphasize` chỉ tạo transform tạm trong preset
3. **Opacity**: Giữ 1.0; trạng thái `dimmed` chỉ đến từ validated style/preset
4. **Idle animation**: Tiếp tục loop, không reset

```
Scene 1: elephant_1 ở slot left, elephant_2 ở center, elephant_3 ở right
Scene 2: elephant_1 EXIT → elephant_2 và elephant_3 STAY
    ↓
Scene Transition:
- elephant_1: exit animation (slide_out_left, duration 0.5s)
- elephant_2: vẫn ở center, idle animation tiếp tục
- elephant_3: vẫn ở right, idle animation tiếp tục
- Không có gap! elephant_2 và elephant_3 visible suốt quá trình.
```

### 6.4.3 Background Logic

```
Background types:
  solid_white     — #FFFFFF (default W5D)
  solid_dark      — #1A1A2E
  solid_custom    — any hex color
  gradient        — 2-color gradient
  image           — background asset (ảnh cánh đồng, văn phòng...)
  video           — video background (muted, looped)
  none            — transparent (dùng khi compositing)

Background change rules:
  - Background KHÔNG thay đổi giữa scenes mặc định
  - Chỉ thay đổi khi có explicit entity type == "location" thay đổi
  - Background transition: crossfade trong 0.8s
```

---

## 6.5 Safe Zone & Typography Zone

```
Canvas 1920×1080 với các zones:

┌─────────────────────────────────────────────────────┐ ← y=0
│  ███████████ TEXT ZONE (keyword overlays) ████████  │ ← y=60-250
│─────────────────────────────────────────────────────│
│                                                     │
│                                                     │
│       OBJECT ZONE (entities live here)              │
│                                                     │
│    🐘           🐘           🐘                    │
│─────────────────────────────────────────────────────│ ← y=900
│  ██████████ SUBTITLE ZONE (optional) ██████████████ │ ← y=920-1000
└─────────────────────────────────────────────────────┘ ← y=1080
  ↑x=80                                        x=1840↑

SAFE AREA: margin 80px mỗi cạnh
TEXT ZONE: y=[60, 250], centered, max-width: 1600px
OBJECT ZONE: y=[250, 900]
SUBTITLE ZONE: y=[920, 1000]
```

---

## 6.6 Layer System

Objects được render theo layer (z-index):

```
Layer 0: Background (image/color/video)
Layer 1: Background decorations (grass, floor lines)
Layer 2: Shadow layer (drop shadows của objects)
Layer 3: Back objects (objects ở hàng sau, dimmed)
Layer 4: Main objects (primary entities)
Layer 5: Front objects (foreground elements)
Layer 6: Effects (particles, glow, hand-draw overlay)
Layer 7: Text overlays (keyword text)
Layer 8: UI overlay (progress bar, etc.)
```

**Object layer assignment:** ScenePlan lưu `zOrderGroup`; layout engine resolve group
đó thành `zIndex` số trong TimelineDocument. Named slot chỉ là authoring hint và
không được renderer dùng như geometry.

> Tiếp theo: [07_animation_system.md](./07_animation_system.md)

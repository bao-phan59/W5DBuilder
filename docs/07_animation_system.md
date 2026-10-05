# 07 — Hệ Thống Animation Tự Động

> Loại: Design specification  
> Các giá trị thời gian dạng giây trong ví dụ chỉ để dễ đọc. Implementation dùng integer frame cho animation và millisecond cho audio alignment.

> Trái tim của W5D Builder — dịch scene plan thành keyframe animation đạt chuẩn video.

---

## 7.1 Kiến Trúc Animation System

```
scene_plan.json + timing.json + asset_map.json
            │
            ▼
    [Animation Composer]
            │
    ┌───────┼───────────────────────┐
    │       │                       │
    ▼       ▼                       ▼
[Object  [Text Overlay        [Effect Layer
Keyframes]  Animations]         Generator]
    │       │                       │
    └───────┴───────────────────────┘
            │
            ▼
    TimelineDocument artifact
```

---

## 7.2 Animation Grammar — Ngôn Ngữ Animation

Animation Grammar là hệ thống quy tắc dịch **(ScenePlan semantic intent, style,
available frames, context) → validated preset parameters/keyframes**. Renderer
không đọc action thô từ ScriptDocument.

### 7.2.1 Animation Preset Library

#### ENTER Animations

```typescript
// Tất cả enter animation bắt đầu từ NGOÀI khung hình hoặc invisible

ENTER_SLIDE_BOTTOM: {
  // Object xuất hiện từ dưới trượt lên
  from: { x: slot.x, y: canvas.height + 50, opacity: 1, scale: 1 },
  to:   { x: slot.x, y: slot.y, opacity: 1, scale: 1 },
  duration: 0.6,
  easing: "spring(1, 80, 10)"   // spring physics: mass, stiffness, damping
}

ENTER_SLIDE_LEFT: {
  // Object xuất hiện từ trái
  from: { x: -asset.width - 50, y: slot.y, opacity: 1, scale: 1 },
  to:   { x: slot.x, y: slot.y, opacity: 1, scale: 1 },
  duration: 0.5,
  easing: "cubic-bezier(0.22, 1, 0.36, 1)"
}

ENTER_SLIDE_RIGHT: {
  from: { x: canvas.width + 50, y: slot.y, opacity: 1, scale: 1 },
  to:   { x: slot.x, y: slot.y, opacity: 1, scale: 1 },
  duration: 0.5,
  easing: "cubic-bezier(0.22, 1, 0.36, 1)"
}

ENTER_FADE: {
  from: { x: slot.x, y: slot.y, opacity: 0, scale: 0.95 },
  to:   { x: slot.x, y: slot.y, opacity: 1, scale: 1 },
  duration: 0.5,
  easing: "ease-out"
}

ENTER_ZOOM: {
  from: { x: slot.x, y: slot.y, opacity: 0, scale: 0.3 },
  to:   { x: slot.x, y: slot.y, opacity: 1, scale: 1 },
  duration: 0.6,
  easing: "spring(1, 100, 15)"
}

ENTER_BOUNCE: {
  // Xuất hiện từ dưới với bounce vật lý
  keyframes: [
    { progress: 0,    y: slot.y + 80, scale: 1 },
    { progress: 0.6,  y: slot.y - 20, scale: 1.05 },  // overshoot
    { progress: 0.8,  y: slot.y + 8,  scale: 0.98 },
    { progress: 1.0,  y: slot.y,      scale: 1 }
  ],
  duration: 0.8,
  easing: "linear"  // keyframes handle easing
}

ENTER_HAND_DRAW: {
  // SVG mask reveal — như đang vẽ ra
  // Áp dụng SVG clip path animation
  clip_path_animation: "draw_in",
  duration: 1.2,
  stroke_color: "#333333",
  draw_sound: "pencil_stroke"
}
```

#### EXIT Animations

```typescript
// Tất cả exit animation kết thúc NGOÀI khung hình hoặc invisible

EXIT_SLIDE_LEFT: {
  from: { x: slot.x, y: slot.y, opacity: 1 },
  to:   { x: -asset.width - 50, y: slot.y, opacity: 1 },
  duration: 0.5,
  easing: "cubic-bezier(0.64, 0, 0.78, 0)"  // ease-in, accelerate out
}

EXIT_SLIDE_RIGHT: {
  from: { x: slot.x, y: slot.y, opacity: 1 },
  to:   { x: canvas.width + 50, y: slot.y, opacity: 1 },
  duration: 0.5,
  easing: "cubic-bezier(0.64, 0, 0.78, 0)"
}

EXIT_SLIDE_BOTTOM: {
  from: { x: slot.x, y: slot.y, opacity: 1 },
  to:   { x: slot.x, y: canvas.height + 100, opacity: 1 },
  duration: 0.5,
  easing: "cubic-bezier(0.64, 0, 0.78, 0)"
}

EXIT_FADE: {
  from: { opacity: 1, scale: 1 },
  to:   { opacity: 0, scale: 0.95 },
  duration: 0.4,
  easing: "ease-in"
}

EXIT_ZOOM_OUT: {
  from: { opacity: 1, scale: 1 },
  to:   { opacity: 0, scale: 0.2 },
  duration: 0.5,
  easing: "ease-in"
}

EXIT_DISSOLVE: {
  // Particle dissolve effect
  effect: "particle_burst_out",
  particle_count: 20,
  duration: 0.8
}
```

#### IDLE Animations (Loop)

```typescript
// Tất cả idle animation là loop vô hạn, biên độ nhỏ

IDLE_FLOAT: {
  // Lơ lửng nhẹ lên xuống
  keyframes: [
    { progress: 0,   y: slot.y },
    { progress: 0.5, y: slot.y - 8 },
    { progress: 1,   y: slot.y }
  ],
  duration: 2.5,
  loop: true,
  easing: "ease-in-out"
}

IDLE_SWAY: {
  // Lắc lư nhẹ sang hai bên
  keyframes: [
    { progress: 0,   rotation: 0 },
    { progress: 0.25, rotation: -2 },
    { progress: 0.75, rotation: 2 },
    { progress: 1,   rotation: 0 }
  ],
  duration: 3.0,
  loop: true,
  transform_origin: "bottom_center"
}

IDLE_BREATHE: {
  // Scale nhỏ nhịp nhàng như thở
  keyframes: [
    { progress: 0,   scale: 1.0 },
    { progress: 0.5, scale: 1.03 },
    { progress: 1,   scale: 1.0 }
  ],
  duration: 2.0,
  loop: true,
  easing: "ease-in-out"
}

IDLE_EAT: {
  // Nghiêng đầu xuống nhịp nhàng
  keyframes: [
    { progress: 0,   rotation: 0,  y: slot.y },
    { progress: 0.3, rotation: 8,  y: slot.y + 5 },
    { progress: 0.6, rotation: 0,  y: slot.y },
    { progress: 1,   rotation: 0,  y: slot.y }
  ],
  duration: 1.5,
  loop: true
}
```

#### EMPHASIS Animations

```typescript
EMPHASIS_PULSE: {
  keyframes: [
    { scale: 1.0 },
    { scale: 1.15 },
    { scale: 1.0 }
  ],
  duration: 0.4,
  loop: false,
  effect: "glow_pulse"
}

EMPHASIS_SHAKE: {
  keyframes: [
    { x: slot.x },
    { x: slot.x - 8 },
    { x: slot.x + 8 },
    { x: slot.x - 5 },
    { x: slot.x + 5 },
    { x: slot.x }
  ],
  duration: 0.4,
  loop: false
}

EMPHASIS_ZOOM_PUNCH: {
  // Camera zoom punch — toàn bộ scene zoom vào
  target: "camera",
  keyframes: [
    { scale: 1.0, x: 0, y: 0 },
    { scale: 1.2, x: -(slot.x - 960) * 0.2, y: -(slot.y - 540) * 0.2 },
    { scale: 1.0, x: 0, y: 0 }
  ],
  duration: 0.6,
  easing: "spring(1, 80, 20)"
}
```

---

## 7.3 Stagger System — Vào Không Cùng Lúc

Khi nhiều objects enter cùng một scene, chúng KHÔNG enter đồng thời. Dùng stagger:

```typescript
STAGGER_CONFIG = {
  base_delay: 0,          // Delay của object đầu tiên
  stagger_gap: 0.15,      // Khoảng cách giữa mỗi object (giây)
  max_stagger: 0.5        // Tối đa stagger tổng cộng
}

// 3 objects enter:
// object_1: delay = 0.0s
// object_2: delay = 0.15s
// object_3: delay = 0.30s

// 5 objects enter:
// object_1: delay = 0.0s
// object_2: delay = 0.1s  (stagger_gap = 0.5/5 = 0.1)
// object_3: delay = 0.2s
// object_4: delay = 0.3s
// object_5: delay = 0.4s
```

**Stagger direction** dựa theo template slot position:
- Template TRIPLE_EVEN: stagger từ trái → phải
- Template TRIPLE_PYRAMID: stagger từ trên → dưới
- Template DUAL_COMPARE: cả hai enter cùng lúc (symmetric)

---

## 7.4 Text Overlay Animations

### 7.4.1 Text Styles

```typescript
KEYWORD_POP: {
  // Bold, màu accent, scale punch vào
  enter: {
    from: { scale: 0.5, opacity: 0 },
    to:   { scale: 1.0, opacity: 1 },
    duration: 0.25,
    easing: "spring(1, 200, 15)"
  },
  idle: "none",
  exit: {
    from: { scale: 1.0, opacity: 1 },
    to:   { scale: 0.8, opacity: 0 },
    duration: 0.2
  },
  font: "Nunito, bold",
  size: "72px",
  color: "#FFD700",         // Gold
  stroke: "#333 2px",
  shadow: "0 4px 20px rgba(255,215,0,0.6)"
}

KEYWORD_TYPEWRITER: {
  // Chữ xuất hiện từng chữ cái
  effect: "typewriter",
  chars_per_second: 15,
  cursor: true,
  font: "Courier Prime, bold",
  size: "64px",
  color: "#FFFFFF"
}

KEYWORD_HANDWRITE: {
  // Font handwriting với SVG stroke animation
  font: "Caveat, bold",
  size: "80px",
  color: "#333333",
  effect: "svg_stroke_draw",
  stroke_color: "#333333",
  stroke_width: 3
}

KEYWORD_GLOW: {
  // Neon glow effect
  font: "Poppins, black",
  size: "68px",
  color: "#FFFFFF",
  text_shadow: "0 0 10px #fff, 0 0 20px #fff, 0 0 40px #FF6B6B, 0 0 80px #FF6B6B"
}
```

### 7.4.2 Text Positioning

```
Vị trí text_zone:
  top_center     — trên cùng, canh giữa (phổ biến nhất)
  top_left       — trên cùng, trái
  top_right      — trên cùng, phải
  bottom_center  — dưới cùng, canh giữa
  center         — giữa màn hình (dùng cho tiêu đề)
  over_entity    — phía trên entity cụ thể
```

---

## 7.5 Hand-Draw Reveal Effect

Hiệu ứng vẽ tay là đặc trưng của W5D video. Có 2 loại:

### Type A: Object Hand-Draw Reveal
Object xuất hiện như đang được vẽ ra bằng tay:

```
Cơ chế:
1. Ảnh được convert sang SVG outline (hoặc dùng contour detection)
2. SVG stroke animation vẽ outline trước (0.4s)
3. Fill color flood-fill sau khi outline xong (0.2s)
4. Drop shadow xuất hiện (0.1s)

Hoặc đơn giản hơn:
1. Overlay một brush texture mask
2. Animate mask reveal từ một điểm (như bàn tay vẽ)
3. Reveal theo clipPath animation
```

### Type B: Text Hand-Draw
Text xuất hiện như đang được viết tay:
- Dùng font có stroke path
- Animate stroke-dashoffset từ full → 0
- Kèm sound: bút chì scraping

---

## 7.6 Mapping Semantic Intent → Animation Preset

ScriptDocument chỉ có action ổn định `enter | stay | move | emphasize | exit` và
`stateHint` tùy chọn. Scene resolver chuyển chúng thành `TransitionIntent`; timeline
compiler mới chọn preset cụ thể. Registry dưới đây là ví dụ cấu hình, không phải
schema hay ánh xạ trực tiếp từ script:

```typescript
const PRESET_RULES: PresetRule[] = [
  { intent: "enter", stateHint: "drawn", presetId: "ENTER_HAND_DRAW" },
  { intent: "enter", presetId: "ENTER_SLIDE_BOTTOM" },
  { intent: "stay", stateHint: "eating", presetId: "IDLE_EAT" },
  { intent: "stay", presetId: "IDLE_FLOAT" },
  { intent: "move", presetId: "MOVE_BETWEEN_BOXES" },
  { intent: "emphasize", presetId: "EMPHASIS_PULSE" },
  { intent: "exit", stateHint: "left", presetId: "EXIT_SLIDE_LEFT" },
  { intent: "exit", presetId: "EXIT_FADE" }
]

// resolve_preset(intent, styleGuide, availableFrames) dùng thứ tự specificity,
// deterministic tie-break và fail nếu preset không fit min/max frames.
```

---

## 7.7 TimelineDocument boundary

TimelineDocument là artifact render-ready, không còn tên legacy
`animation_timeline.json`. Mọi item dùng `[startFrame, endFrame)`, asset ID và
normalized `box`; không dùng giây, local path, URL, named slot hay `scale` làm
geometry. Tracks chuẩn gồm background, object, text, camera, audio và effect.

Schema executable duy nhất nằm tại `contracts/schemas/timeline-document.schema.json`
khi WP0 được triển khai. Semantics và hàm compiler bắt buộc xem tại
[implementation/03_domain_and_data_contracts.md](./implementation/03_domain_and_data_contracts.md)
và
[implementation/codebase/07_scene_timeline_pipeline.md](./implementation/codebase/07_scene_timeline_pipeline.md).

> Tiếp theo: [08_postprocess.md](./08_postprocess.md) — Lớp hậu kỳ và one-shot flow

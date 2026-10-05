# 08 — Lớp Hậu Kỳ: Motion Effects, Transitions & One-Shot Flow

> Loại: Design specification  
> Postprocess nâng cao nằm ngoài vertical slice MVP; one-shot gap validation vẫn là yêu cầu cốt lõi.

> Module cuối cùng trước render — nơi video trở nên sống động và chuyên nghiệp.

---

## 8.1 Triết Lý One-Shot Video

### Không Có Slide, Chỉ Có Dòng Chảy

Video W5D là **một mạch câu chuyện liên tục**. Xem như xem một bộ phim animation ngắn —
không phải xem slide PowerPoint.

**Nguyên tắc cốt lõi:**
1. **Canvas không bao giờ trống hoàn toàn** — luôn có ít nhất 1 element visible
2. **Exit và Enter overlap** — khi A đang exit thì B đã bắt đầu enter
3. **Idle animations chạy liên tục** — không bao giờ "pause"
4. **Audio là backbone** — animation phải sync với từng nhịp của giọng đọc

### Timeline Mẫu Cho Câu Chuyện Ba Chú Voi

```
Timeline (giây):
0   1   2   3   4   5   6   7   8   9   10

AUDIO: [---"Có ba chú voi"-------][---"ăn cỏ"---][--"một chú rời đi"--]

VOI_1: [=== enter ===][~~~~~~ idle_eat ~~~~~~][>> exit_left >>]
VOI_2: [== enter ==][~~~~~~~~ idle_eat ~~~~~~~~][~~~~~~ idle ~~~~~~][idle]
VOI_3: [= enter =][~~~~~~~~~~ idle_eat ~~~~~~~~~~][~~~~~~ idle ~~~~~~][idle]

TEXT:           [BA CHÚ VOI]        [ĂN CỎ]            [RỜI ĐI]

EFFECT:  [hand_draw voi_1][hand_draw voi_2][hand_draw voi_3]

Chú thích:
  [=== enter ===]  → enter animation
  [~~~~~~ idle ~~] → idle animation (loop)
  [>> exit >>]     → exit animation
  [TEXT]           → text overlay visible
```

**Key**: Voi_1 exit bắt đầu ở t=6.0, nhưng voi_2 và voi_3 vẫn đang idle — canvas không trống.

---

## 8.2 Scene Transition System

### 8.2.1 Transition Types

Transition xảy ra tại ranh giới giữa các "trạng thái" của canvas.
Không phải transition của toàn bộ screen — mà là transition của **từng element riêng lẻ**.

```
OBJECT_TRANSITION (per-object):
  Dùng cho: Entity từ scene này sang scene tiếp theo

  SEAMLESS (mặc định):
    → Entity cũ EXIT, entity mới ENTER, overlap 0.3s
    → Không có gap
    
  SWAP:
    → Entity cũ EXIT sang một hướng
    → Entity mới ENTER từ hướng đối diện
    → Thường dùng khi thay thế hoàn toàn
    
  MORPH:
    → Entity cũ scale down + fade
    → Entity mới scale up + fade tại cùng vị trí
    → Dùng khi "biến đổi" (concept change)
    
  HOLD_AND_REPLACE:
    → Entity cũ đứng yên 0.2s
    → Sau đó crossfade sang entity mới
```

### 8.2.2 Camera / Viewport Transitions

Đây là lớp motion áp dụng cho toàn bộ "camera" — tạo cảm giác depth và cinematic:

```
CAMERA_TRANSITIONS:

  SUBTLE_PAN:
    → Viewport dịch chuyển nhẹ (20-40px) theo hướng nội dung
    → Duration: toàn bộ scene
    → Amplitude: nhỏ, không gây chóng mặt

  ZOOM_IN_FOCUS:
    → Zoom nhẹ vào entity đang được nhắc đến (scale 1.0 → 1.1)
    → Duration: 1-2s
    → Dùng khi muốn nhấn mạnh một entity cụ thể

  ZOOM_OUT_REVEAL:
    → Zoom out để reveal entity mới ở góc khác
    → scale 1.1 → 1.0, với pan nhẹ
    
  PUSH_LEFT / PUSH_RIGHT:
    → Toàn bộ canvas "đẩy" sang một hướng như page turn
    → Dùng khi chuyển sang chapter/phần mới của câu chuyện

  STATIC (mặc định):
    → Không camera movement
    → Dùng cho content cần đọc rõ ràng
```

### 8.2.3 Background Transitions

```
BG_CROSSFADE:
  → Background cũ fade out, background mới fade in
  → Duration: 0.8s
  → Threshold: overlap ở opacity 0.5

BG_WIPE_LEFT / BG_WIPE_RIGHT:
  → Background mới trượt vào từ một bên
  → Duration: 0.6s
  → Dùng khi chuyển địa điểm trong câu chuyện

BG_INSTANT:
  → Thay đổi ngay lập tức
  → Dùng khi chuyển cảnh mạnh (có object enter che phủ)
```

---

## 8.3 Motion Effects Library

### 8.3.1 Global Motion Effects

Các effect áp dụng cho toàn bộ video hoặc một đoạn dài:

```
PARALLAX_IDLE:
  → Background di chuyển chậm hơn foreground
  → Tỉ lệ: background di chuyển 30% tốc độ so với foreground
  → Tạo cảm giác depth 3D nhẹ
  → Recommend: BẬT cho tất cả video

AMBIENT_MOTION:
  → Các particle/dust nhỏ di chuyển trong background
  → Opacity: 5-15%, rất tinh tế
  → Tạo cảm giác "sống"

VIGNETTE:
  → Viền tối nhẹ quanh màn hình
  → Opacity: 0-30%, user có thể điều chỉnh
  → Tạo cảm giác cinematic
```

### 8.3.2 Per-Object Motion Effects

```
SHADOW_DYNAMIC:
  → Drop shadow của object thay đổi theo idle animation
  → Khi float lên: shadow nhỏ lại và mờ hơn
  → Khi float xuống: shadow to hơn và đậm hơn
  → Effect depth rất hiệu quả

HIGHLIGHT_RING:
  → Vòng tròn phát sáng quanh object khi được nhắc đến
  → Sync với word_timestamp của entity trong timing.json

SPEECH_BUBBLE:
  → Bong bóng thoại xuất hiện trên object
  → Có thể chứa text hoặc icon (meme)
  → Animation: pop in từ nhỏ ra to, bounce nhẹ

PARTICLE_SYSTEM:
  → Các particles phát ra từ object
  → Types: sparkle, confetti, dust, fire, steam, hearts
  → Trigger: theo action (ví dụ: confetti khi "thành công")

ZOOM_PUNCH (Camera Effect):
  → Toàn bộ scene zoom nhanh vào, zoom ra
  → Duration: 0.3s in + 0.3s out
  → Dùng: khi giọng đọc nhấn từ quan trọng nhất

SCREEN_SHAKE:
  → Toàn bộ scene rung nhẹ
  → Amplitude: 4-8px
  → Duration: 0.3-0.5s
  → Dùng: action mạnh (va chạm, thất bại, ngạc nhiên)
```

---

## 8.4 Audio Layer

### 8.4.1 Audio Track Architecture

```
Track 1: VOICE (voiceover)
  - Volume: 0 dB (reference)
  - Normalize: luôn clear
  - Ducking target: không

Track 2: BACKGROUND MUSIC
  - Volume: -20 dB so với voice
  - Auto-duck: giảm thêm -6dB khi voice active
  - Fade in: 1s ở đầu video
  - Fade out: 2s ở cuối video
  - Loop: tự động

Track 3: SFX (Sound Effects)
  - Volume: -10 dB so với voice
  - Synced với animation events
  - Multiple simultaneous SFX allowed
```

### 8.4.2 SFX Library — Sync với Animation

```
ENTER_SFX:
  slide_in:      "whoosh_soft.mp3"       (khi object slide vào)
  zoom_in:       "pop_in.mp3"            (khi object zoom vào)
  bounce:        "bounce_land.mp3"       (khi bounce)
  hand_draw:     "pencil_stroke.mp3"     (khi vẽ tay reveal)

EXIT_SFX:
  slide_out:     "whoosh_out.mp3"
  fade_out:      "dissolve.mp3"
  zoom_out:      "shrink_pop.mp3"

TEXT_SFX:
  keyword_pop:   "text_pop.mp3"          (khi text xuất hiện)
  typewriter:    "typewriter_keys.mp3"   (cho typewriter effect)

EMPHASIS_SFX:
  pulse:         "ding_soft.mp3"
  shake:         "rumble_short.mp3"
  zoom_punch:    "impact_soft.mp3"

SPECIAL_SFX:
  particle_burst: "sparkle.mp3"
  confetti:       "confetti_pop.mp3"
  speech_bubble:  "bubble_pop.mp3"
  success:        "success_chime.mp3"
  transition:     "page_turn.mp3"
```

### 8.4.3 Background Music Categories

```
UPBEAT:     Nhạc năng động, phù hợp marketing/tutorial
CALM:       Nhạc nhẹ nhàng, phù hợp educational
CORPORATE:  Nhạc chuyên nghiệp, phù hợp business
PLAYFUL:    Nhạc vui nhộn, phù hợp children/storytelling
DRAMATIC:   Nhạc căng thẳng, phù hợp problem/solution
INSPIRING:  Nhạc truyền cảm hứng, phù hợp motivational
```

---

## 8.5 One-Shot Flow Engine

Đây là thuật toán đảm bảo video "chạy một mạch không gián đoạn":

### 8.5.1 Gap Detection & Fix

```python
def ensure_one_shot_flow(timeline: AnimationTimeline) -> AnimationTimeline:
    """
    Kiểm tra timeline và tự động fix các "gap" — khoảng thời gian
    không có element nào visible trên canvas.
    """
    
    # Tìm tất cả time ranges có ít nhất 1 object visible
    visible_ranges = compute_visible_ranges(timeline.tracks.objects)
    
    # Tìm gaps
    gaps = find_gaps(visible_ranges, min_gap_duration=0.1)
    
    for gap in gaps:
        # Strategy 1: Extend exit animation của element trước
        prev_element = get_last_element_before(timeline, gap.start)
        if prev_element:
            extend_exit_animation(prev_element, until=gap.end)
            continue
            
        # Strategy 2: Early enter của element sau
        next_element = get_first_element_after(timeline, gap.end)
        if next_element:
            advance_enter_time(next_element, by=gap.duration)
            continue
            
        # Strategy 3: Thêm transition placeholder (background animation)
        add_ambient_transition(timeline, gap.start, gap.end)
    
    return timeline
```

### 8.5.2 Overlap Zone Calculation

Khi scene A kết thúc và scene B bắt đầu, cần tính **overlap zone** — khoảng thời gian
cả A và B đều có element visible:

```
Scene A end:   t=5.0s
Scene B start: t=4.7s  (B start TRƯỚC A end 0.3s)
Overlap zone:  t=4.7s → t=5.0s (0.3s)

Trong overlap zone:
- Element cuối của A: đang exit (exit_animation đang chạy)
- Element đầu của B: đang enter (enter_animation đang bắt đầu)
- Canvas: luôn có content → ✅ one-shot
```

**Overlap duration mặc định**: 0.3s (configurable, range 0.1s — 0.8s)

### 8.5.3 Scene Bridge Animations

Khi cần transition "đẹp" hơn giữa scenes, dùng Bridge Animation:

```
BRIDGE_TYPES:

  SWIPE_LEFT:
    → Tất cả old elements exit sang trái cùng lúc (0.4s)
    → Background slide right → left
    → New elements enter từ phải sang (0.4s)
    → Overlap: 0.1s (rất nhanh)
    
  CURTAIN:
    → Một color overlay/shape phủ dần canvas (0.3s)
    → Background thay đổi
    → Overlay rút dần, elements enter (0.3s)
    → Tổng: 0.6s
    → Dùng: khi thay đổi context lớn

  RIPPLE:
    → Circle ripple expand từ center, che phủ màn hình
    → Elements thay đổi sau ripple
    → Dùng: cho effect hoạt hình vui nhộn

  PUSH_THROUGH:
    → Elements mới đẩy elements cũ ra khỏi frame
    → New slides in từ right, old slides out to left
    → Coherent, linear feel
```

---

## 8.6 Postprocess Layer UI

### Những Gì User Có Thể Điều Chỉnh

```
┌─────────────────────────────────────────────────────┐
│  POSTPROCESS EDITOR                                 │
│                                                     │
│  [Timeline Preview] ←─── Scrub để xem từng frame   │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  🎬 SCENE TRANSITIONS                               │
│  Scene 1→2: [Seamless ▼]  Duration: [0.3s ────]    │
│  Scene 2→3: [Swipe Left ▼] Duration: [0.4s ────]   │
│                                                     │
│  📷 CAMERA MOTION                                   │
│  Global: [Subtle Pan ▼]  Intensity: [Low ────]      │
│  Zoom Punches: [✓] Auto on emphasis words           │
│                                                     │
│  ✨ EFFECTS                                         │
│  Parallax: [✓ ON]                                  │
│  Ambient particles: [✗ OFF]                        │
│  Vignette: [✓] Strength: [20% ────]                │
│  Screen shake on impacts: [✓]                      │
│                                                     │
│  🎵 AUDIO                                           │
│  Music: [Upbeat Corporate ▼]  Vol: [-20dB ────]    │
│  SFX: [✓ ON]   SFX Vol: [-10dB ────]               │
│                                                     │
│  🎨 COLOR GRADE                                     │
│  Preset: [Warm & Bright ▼]                         │
│  Saturation: [+10 ────]  Contrast: [+5 ────]       │
│                                                     │
│  [Preview]    [Reset to Defaults]    [Apply & Render]│
└─────────────────────────────────────────────────────┘
```

### Default Configurations (khuyến nghị)

```json
{
  "camera": {
    "motion": "subtle_pan",
    "zoom_punch_on_emphasis": true,
    "intensity": "low"
  },
  "effects": {
    "parallax": true,
    "ambient_particles": false,
    "vignette": true,
    "vignette_strength": 0.2,
    "shadow_dynamic": true
  },
  "audio": {
    "music_category": "auto",
    "music_volume_db": -20,
    "sfx_enabled": true,
    "sfx_volume_db": -10,
    "voice_normalize": true
  },
  "color_grade": {
    "preset": "warm_bright",
    "saturation": 10,
    "contrast": 5,
    "brightness": 0
  },
  "transitions": {
    "default_type": "seamless",
    "default_duration": 0.3,
    "overlap_duration": 0.3
  }
}
```

---

## 8.7 Quality Checklist Trước Render

Hệ thống tự động kiểm tra trước khi cho phép render final:

```
✅ CHECK: Không có gap > 0.1s trong canvas
✅ CHECK: Tất cả entities có asset assigned
✅ CHECK: Tất cả audio tracks normalized
✅ CHECK: Không có text overlap (2 text overlays cùng lúc cùng vị trí)
✅ CHECK: Tổng duration khớp với audio duration ± 0.5s
✅ CHECK: Không có object ra ngoài safe area
✅ CHECK: Background music fade out ở cuối
⚠️ WARN:  Số entity trong 1 scene > 4 (có thể crowded)
⚠️ WARN:  Câu nào dài hơn 8s (có thể buồn ngủ)
⚠️ WARN:  Không có keyword text nào (ít impactful hơn)
```

> Tiếp theo: [09_render_engine.md](./09_render_engine.md)

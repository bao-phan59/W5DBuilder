# 07 — Scene Planning, Layout và Timeline Compilation

## 1. Boundary

ScenePlan chỉ chứa semantic intent và resolved normalized layout. TimelineDocument chứa frame ranges, preset parameters và render tracks.

```text
Script + Timing
  → semantic scene proposal
  → deterministic state/lifecycle resolution
  → layout solve
  → ScenePlan
ScenePlan + Timing + AssetMap + PostprocessConfig
  → frame quantization
  → animation preset resolution
  → continuity repair
  → TimelineDocument
```

## 2. Files

```text
backend/app/application/scenes/
├── service.py
├── segmentation.py
├── state_machine.py
├── layout.py
├── transitions.py
└── scoring.py
backend/app/application/timeline/
├── service.py
├── compiler.py
├── presets.py
├── continuity.py
├── text.py
├── camera.py
└── audio.py
```

## 3. Scene generation service

### `scenes/service.py`

- `submit_scene_plan_job(projectId, config, actor, key) -> Job`.
- `execute_scene_plan_job(jobId, context) -> ArtifactRef`.
- `generate_scene_plan(script, timing, config, generator) -> ScenePlan`.
- `validate_scene_plan(plan, script, timing) -> ValidationReport`.
- `commit_scene_plan(plan, inputs, projectRevision) -> CommitResult`.

LLM có thể đề xuất grouping/intent nhưng output phải đi qua deterministic resolver và validator. LLM không đặt pixel/frame/keyframe.

## 4. Segmentation

### `scenes/segmentation.py`

| Hàm | Input | Output |
|---|---|---|
| `build_sentence_states` | ScriptDocument | list[SentenceState] |
| `detect_scene_boundaries` | sentence states, policy | list[Boundary] |
| `group_sentences` | sentences, boundaries | list[SceneDraft] |
| `assign_scene_spans` | scenes, TimingDocument | scenes với start/end ms |

Scene boundary khi background/context đổi, active instance set đổi đáng kể hoặc narrative beat yêu cầu. Không mặc định một sentence = một scene.

## 5. Entity state machine

### `scenes/state_machine.py`

- `apply_instruction(state, instruction) -> EntityState`.
- `resolve_active_instances(script) -> list[SentenceEntityState]`.
- `validate_transition(previous, current) -> list[Issue]`.
- `compute_scene_end_state(scene) -> SceneState`.

State: absent, entering, active, exiting. Persistent instance giữ identity, visual state, asset requirement và last layout hint. Exit kết thúc active state; re-enter tạo lifecycle segment mới nhưng giữ instance ID nếu story identity vẫn vậy.

## 6. Layout engine

### `scenes/layout.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `select_template` | `(scene, profile, library) -> TemplateId` | Rule/scoring, deterministic tie-break |
| `instantiate_slots` | `(template, profile) -> list[NormalizedSlot]` | Safe-area aware |
| `assign_instances_to_slots` | `(instances, slots, previousLayout) -> Assignment` | Giảm movement, giữ narrative role |
| `solve_layout` | `(assignment, assetMetadata, textZones, constraints) -> LayoutResult` | Collision/crowding solver |
| `score_layout` | `(layout, constraints) -> ScoreBreakdown` | Visibility, balance, continuity |

Fallback khi solver không đạt threshold: reduce size trong bounds → alternate template → warning/human review; không silently overlap.

## 7. Transition intent

### `scenes/transitions.py`

- `derive_instance_changes(previous, next) -> ChangeSet`.
- `choose_transition(changeSet, styleGuide, context) -> TransitionIntent`.
- `validate_transition_intent(intent, scenes) -> list[Issue]`.

ScenePlan chỉ lưu `enter`, `stay`, `move`, `emphasize`, `exit` và transition family. Preset cụ thể/duration/easing thuộc compiler.

## 8. Timeline compilation

### `timeline/service.py`

- `submit_timeline_job(projectId, config, actor, key) -> Job`.
- `execute_timeline_job(jobId, context) -> ArtifactRef`.
- `compile_timeline(inputs, config) -> TimelineDocument`.
- `validate_and_commit_timeline(timeline, inputs, revision) -> CommitResult`.

### `timeline/compiler.py`

| Hàm | Input | Output |
|---|---|---|
| `build_timebase` | TimingDocument, render profile | Timebase |
| `quantize_scene_spans` | ScenePlan spans | frame spans |
| `compile_background_track` | scenes/transitions | track items |
| `compile_object_tracks` | instances/layout/asset map | object tracks |
| `compile_text_track` | script/timing/layout | text items |
| `compile_camera_track` | scenes/postprocess | camera keyframes |
| `compile_audio_tracks` | voice/music/SFX config | audio items |
| `finalize_total_frames` | all tracks/audio | integer totalFrames |

Compiler là deterministic function với explicit `compilerVersion` và seed.

## 9. Preset registry

### `timeline/presets.py`

- `register_preset(definition) -> None` startup-time only.
- `resolve_preset(intent, styleGuide, availableFrames) -> ResolvedPreset`.
- `validate_preset_params(presetId, params) -> ValidationReport`.
- `fit_preset_duration(preset, availableFrames, policy) -> ResolvedPreset`.

Preset definition có semantic category, min/default/max frames, parameter schema, reduced-motion/editor behavior và Remotion implementation ID. Không lưu easing bằng string không parse được.

## 10. Text timing/layout

### `timeline/text.py`

- `resolve_text_trigger(range, timing) -> FrameRange`.
- `shape_text(text, font, box, language) -> TextLayout`.
- `fit_text(textLayout, box, minFontSize) -> FitResult`.
- `detect_text_collisions(items) -> list[Issue]`.

Font file/version/checksum thuộc render snapshot. Vietnamese glyph coverage phải validate trước render.

## 11. Continuity invariant

### `timeline/continuity.py`

- `compute_meaningful_coverage(timeline) -> list[FrameRange]`.
- `find_unintended_gaps(coverage, policy) -> list[Gap]`.
- `repair_gap(timeline, gap, strategyPolicy) -> RepairResult`.
- `validate_instance_overlap(timeline) -> list[Issue]`.

Chỉ item có `continuityRole=meaningful | declaredBridge` được tính. Static background và ambient particle không đủ để pass. Intentional blank phải có declared bridge/reason.

Repair order: extend meaningful hold without stretching motion → advance compatible enter → insert declared bridge → fail review. Không tự kéo dài exit animation làm sai easing/audio.

## 12. Camera

### `timeline/camera.py`

- `plan_camera(sceneLayouts, emphasisEvents, policy) -> CameraTrack`.
- `validate_camera_safe_area(camera, requiredBoxes) -> list[Issue]`.
- `limit_camera_velocity(track, limits) -> CameraTrack`.

Camera motion phải có velocity/acceleration bounds và reduced-motion preview option; output video vẫn theo project config.

## 13. Tests bắt buộc

- Scene grouping không đồng nhất sentence.
- Entity persistence/exit/re-entry.
- Layout deterministic và safe area.
- Time quantization không gap do rounding.
- Short sentence không đủ min preset frames.
- One-shot meaningful coverage.
- Text overflow và Vietnamese fonts.
- Camera crop content bắt buộc.

# 03 — Script Engine và Skill `w5d-script`

> Loại: Design specification đã đồng bộ Contract 1.0  
> Contract executable hiện tại: [`contracts/schemas/script-document.schema.json`](../contracts/schemas/script-document.schema.json)
> Production implementation: [`implementation/codebase/05_script_voice_pipeline.md`](./implementation/codebase/05_script_voice_pipeline.md)

## 3.1 Vai trò

Script Engine biến ý tưởng hoặc nội dung thô thành `ScriptDocument` có cấu trúc để user review trước khi voice, scene và asset pipeline chạy.

Script Engine chịu trách nhiệm:

- Narration sentences và thứ tự.
- Entity definitions và persistent instances.
- Keyword emphasis bằng character ranges.
- Visual text tùy chọn.
- Estimated timing theo millisecond.
- Semantic visual instructions ở mức intent.

Script Engine không chọn animation preset, keyframe, pixel, frame, asset ID hoặc layout cuối. Các quyết định đó thuộc ScenePlan và Timeline compiler.

## 3.2 Input

| Field | Bắt buộc | Default |
|---|---|---|
| `idea` | Có | — |
| `projectId` | Có khi commit | Preview có thể dùng placeholder ID hợp lệ |
| `targetDurationMs` | Không | `60000` |
| `style` | Không | `storytelling` |
| `tone` | Không | `casual` |
| `language` | Không | `vi` |

User có thể nhập giây ở UI; boundary chuyển sang millisecond trước khi tạo command.

## 3.3 Output canonical

`ScriptDocument 1.0` dùng `camelCase`, JSON Schema 2020-12 và gồm:

- `schemaVersion`, `id`, `projectId`.
- `title`, `language`, `style`, `tone`.
- `targetDurationMs`, `interSentencePauseMs`, `estimatedTotalDurationMs`.
- `sentences`.
- `entityDefinitions`.
- `entityInstances`.

Mỗi sentence có:

- Stable `sen_` ID và `order` liên tục từ 0.
- `narrationText`.
- `sceneHint` chỉ là narrative hint.
- `emphasisRanges` theo `[startChar, endChar)`.
- Optional `visualText`.
- `entityInstructions`.
- `estimatedDurationMs`.

Example chuẩn: [Ba Chú Voi](../.agents/skills/w5d-script/examples/example_01_elephants.json).

## 3.4 Entity definition và instance

Entity definition mô tả visual identity chung, ví dụ `ent_elephant`. Entity instance là cá thể tồn tại xuyên narration, ví dụ `ins_elephant_1`.

Quy tắc:

- Ba cá thể phải có ba instance ID; không dùng `count: 3`.
- Instance phải `enter` trước các action khác.
- Sau `exit`, instance chỉ trở lại bằng `enter` mới.
- Omitted background instruction có thể giữ trạng thái từ câu trước; resolver phải làm điều này explicit trong ScenePlan.
- `targetInstanceId` phải tham chiếu instance đã tồn tại và active.

`assetHints` nằm trên entity definition, chỉ hỗ trợ search/generation. Nó không phải Asset, không mang license và không chứa local path/provider object.

## 3.5 Semantic visual instructions

Script chỉ dùng năm action family:

| Action | Ý nghĩa |
|---|---|
| `enter` | Instance bắt đầu active |
| `stay` | Giữ instance và trạng thái |
| `move` | Thay đổi narrative placement |
| `emphasize` | Làm nổi bật về ý nghĩa |
| `exit` | Instance kết thúc active span |

`stateHint` mô tả ý định như `eating`, `walk_slow`, `smile`, `exit_left`. Scene planner có thể bảo toàn intent nhưng Timeline compiler mới resolve thành preset/duration/easing.

## 3.6 Generation flow

```text
input
→ normalize idea/config
→ draft narration
→ segment sentences
→ extract definitions/instances
→ add semantic instructions
→ resolve emphasis ranges/visual text
→ estimate timing
→ structural validation
→ semantic validation/repair giới hạn
→ candidate ScriptDocument
→ user approval/current ScriptDocument
```

Provider output không được commit trực tiếp. Repair loop có attempt/token/cost limit và chỉ nhận invalid document cùng validation issues; không lưu chain-of-thought.

## 3.7 Validation

Structural validation dùng schema. Semantic validation bắt buộc kiểm tra:

1. ID/reference uniqueness và đúng prefix.
2. Sentence order liên tục.
3. Emphasis text khớp chính xác character range, không overlap.
4. Entity lifecycle hợp lệ.
5. Mỗi sentence có visualizable instruction.
6. Duration formula: `sum(sentence) + pause × (count - 1)`.
7. Estimated total nằm trong tolerance 20% của target.
8. Không có câu trừu tượng không thể biểu diễn.

Validation trả toàn bộ issues có thể thu thập an toàn trong một lần; error chặn approval, warning vẫn cho review.

## 3.8 Skill package

```text
.agents/skills/w5d-script/
├── SKILL.md
├── schemas/script.schema.json
└── examples/example_01_elephants.json
```

Skill chỉ tạo/chuẩn hóa document và trả output. Application service chịu trách nhiệm persistence, provenance, approval, audit và downstream invalidation.

> Tiếp theo: [04_sentence_keyword.md](./04_sentence_keyword.md)

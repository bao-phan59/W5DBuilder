---
name: w5d-script
description: Tạo hoặc chuẩn hóa ScriptDocument 1.0 cho video W5D từ ý tưởng, bài viết hoặc kịch bản thô; dùng khi đầu ra cần câu narration, entity instances, semantic visual instructions, keyword ranges và timing estimate. Không dùng để lập ScenePlan, TimelineDocument hay render video.
---

# W5D ScriptDocument

Tạo một `ScriptDocument` hợp lệ để pipeline W5D tiếp tục xử lý. Script chỉ mô tả nội dung và visual intent; không chọn animation preset, pixel, frame hay asset cụ thể.

## Contract bắt buộc

Đọc và tuân thủ:

- [`schemas/script.schema.json`](./schemas/script.schema.json) — contract JSON Schema 2020-12.
- [`examples/example_01_elephants.json`](./examples/example_01_elephants.json) — example structurally và semantically hợp lệ.

Nếu instruction này khác schema, schema là nguồn sự thật. Output dùng `camelCase`, millisecond và ID prefix chuẩn; không phát sinh contract snake_case cũ.

## Input

- `idea`: bắt buộc.
- `projectId`: dùng ID caller cung cấp; nếu chỉ preview, dùng một ID hợp lệ có prefix `prj_` và nói rõ đây là placeholder.
- `targetDurationMs`: mặc định `60000`; nhận input giây thì đổi sang millisecond.
- `style`: mặc định `storytelling`.
- `tone`: mặc định `casual`.
- `language`: mặc định `vi`.

Chỉ hỏi lại khi thiếu `idea` hoặc một lựa chọn làm thay đổi đáng kể nội dung. Các field còn lại dùng default.

## Quy tắc nội dung

- Mỗi sentence tối đa khoảng 15 từ và thể hiện một hành động hoặc trạng thái có thể nhìn thấy.
- Hook xuất hiện sớm; phần giữa có progression; câu cuối là kết luận/CTA có thể hình ảnh hóa.
- Không dùng câu trừu tượng nếu không chuyển được thành hành vi, vật thể hoặc text visual cụ thể.
- Entity definition mô tả khái niệm chung; mỗi cá thể xuyên suốt video phải có một `entityInstance` riêng.
- Không dùng đồng thời một instance và `count` để đại diện nhiều cá thể.
- Instance phải `enter` trước `stay`, `move`, `emphasize` hoặc `exit`; sau `exit` chỉ trở lại bằng `enter` mới.
- `action` chỉ dùng semantic family: `enter`, `stay`, `move`, `emphasize`, `exit`.
- Hành vi cụ thể như `eating`, `walk_slow`, `exit_left` nằm trong `stateHint`; ScenePlan/compiler mới chọn preset.
- `positionHint` chỉ là authoring hint, không phải tọa độ.

## Keyword và timing

- `emphasisRanges` dùng half-open character offsets `[startChar, endChar)` trên đúng `narrationText`.
- Text tại range phải khớp chính xác field `text`; ranges không overlap và tối đa ba range mỗi câu.
- `visualText` tối đa 30 ký tự; dùng `null` nếu không cần hiển thị.
- `estimatedDurationMs` mỗi câu nằm trong `1500..8000`.
- `estimatedTotalDurationMs` phải bằng tổng `estimatedDurationMs` cộng `interSentencePauseMs × (sentenceCount - 1)`.
- Tổng thời lượng phải nằm trong tolerance 20% của `targetDurationMs`; nếu không đạt, điều chỉnh nội dung hoặc timing trước khi trả kết quả.

## Asset hints

Mỗi `entityDefinition` có một `assetHints` duy nhất:

- `searchQuery`: từ khóa tìm asset.
- `generationPrompt`: mô tả tạo ảnh, không chứa credential, local path hoặc provider-specific object.

Asset hints không phải Asset resource và không khẳng định license. Asset pipeline chịu trách nhiệm search/generate, rights metadata, moderation và processing.

## Validation trước khi trả

Kiểm tra cả structural và semantic invariants:

1. JSON hợp lệ theo schema.
2. ID duy nhất và mọi reference tồn tại.
3. Sentence `order` liên tục từ 0.
4. Emphasis offsets khớp narration.
5. Entity lifecycle hợp lệ.
6. Duration formula và target tolerance đúng.
7. Không có sentence trừu tượng hoặc instance mơ hồ.

Trả JSON thuần khi caller yêu cầu machine-readable output. Skill không tự ghi file hoặc gọi provider; application service chịu trách nhiệm persistence, approval và provenance.

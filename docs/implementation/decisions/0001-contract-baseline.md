# ADR 0001 — Contract baseline và tương thích ScriptDocument 1.0

- Trạng thái: Chấp nhận định hướng; implementation và WP0 gate còn cần evidence.
- Phạm vi: WP0-B01, baseline ScriptDocument; không xác nhận hoàn thành WP0.
- Ngày: 2026-10-06.

## Bối cảnh

Blueprint yêu cầu executable contracts dùng JSON Schema 2020-12, generated Python/TypeScript models và structural + semantic validation. Contract ScriptDocument 1.0 hiện có trong skill `w5d-script`; chưa có canonical `contracts/` trước batch này. Cần chuyển quyền sở hữu contract về project mà không phá payload đã được skill tạo.

## Quyết định

1. `contracts/schemas/` là nguồn canonical cho domain schemas, `contracts/examples/` là nguồn golden fixtures. JSON Schema 2020-12, `camelCase` và `additionalProperties: false` được giữ; metadata extension phải khai báo rõ. API DTO sau này thuộc `contracts/api/`, không tạo bản domain schema viết tay cạnh tranh.
2. Baseline `script-document.schema.json` giữ nguyên schema ID, `schemaVersion: "1.0"`, required fields, enums, limits, optional/null semantics và cấu trúc ScriptDocument đang có. Schema tại `.agents/skills/w5d-script/schemas/script.schema.json` trở thành mirror byte-for-byte; check tự động phải fail khi drift. Mọi sửa đổi bắt đầu từ canonical rồi đồng bộ mirror. Skill không là nguồn contract thứ hai.
3. Structural validation kiểm tra schema; semantic validation kiểm tra ID duy nhất, reference tồn tại, sentence order liên tục từ 0 và các invariants dưới đây. Lỗi dữ liệu dự kiến trả validation issues/report; programming hoặc infrastructure errors không được che thành lỗi document.
4. Emphasis offsets tính bằng Unicode code points trên nguyên bản `narrationText`, không dùng UTF-16 code units hay normalize text âm thầm. Range là half-open `[startChar, endChar)`, với `0 <= startChar < endChar <= codePointLength`; substring phải khớp `text` chính xác và các ranges không overlap. TypeScript phải chuyển text sang code points trước khi slice.
5. `estimatedTotalDurationMs = sum(sentence.estimatedDurationMs) + interSentencePauseMs * (sentenceCount - 1)`. Kiểm tra tự động tổng này và tolerance 20% của `targetDurationMs`; timing estimates không được xem là timing audio đã reconcile.
6. Entity lifecycle được duyệt theo sentence order, rồi instruction order trong mỗi sentence. Instance phải `enter` trước `stay`, `move`, `emphasize` hoặc `exit`; không được `enter` lại khi đang active; sau `exit` chỉ active lại bằng `enter` mới. References của instruction và `entityId` phải tồn tại. Baseline không bổ sung yêu cầu mọi instance phải exit ở câu cuối.
7. Breaking change phải có version mới và migration/ADR rõ ràng; không đổi ý nghĩa payload `1.0` âm thầm. Schema migration không đồng nghĩa với persisted artifact revision. Artifact persistence sẽ dùng lifecycle `candidate | current | stale | superseded | failed` theo blueprint; promotion và descendant invalidation thuộc application transaction trong batch tương lai, không thuộc script authoring skill.

## Python/TypeScript generation — chưa triển khai

Batch sau sẽ chọn generator Pydantic từ JSON Schema và generator TypeScript types, kèm runtime validator hỗ trợ draft 2020-12. Cần đánh giá bằng cùng fixtures trước khi chọn package/version, đặc biệt optional/nullability, Unicode length, strict integers và unknown fields. Toolchain sẽ được pin trong lockfiles, regenerate trong CI và fail nếu generated output drift. Round-trip fixtures và các lỗi semantic phải thống nhất giữa hai runtime. ADR này chưa lock package/version, chưa tạo generated models và chưa xác nhận type strategy acceptance của WP0 đã đạt.

## Xung đột và giới hạn

- Blueprint đặt schema tại `contracts/`, còn schema executable hiện hữu nằm trong skill. Giải quyết bằng canonical + mirror, giữ byte compatibility thay vì thay schema cũ bằng model mới.
- Skill nói character offsets nhưng chưa định nghĩa đơn vị Unicode. Quyết định code points làm rõ tính tương thích với JSON Schema/Python; fixture có ký tự ngoài BMP cần chứng minh parity khi triển khai TypeScript.
- WP0 yêu cầu sáu contracts, CI fixtures và validators; batch baseline ScriptDocument chỉ giải quyết một phần. TimingDocument, ScenePlan, AssetMap, TimelineDocument, RenderJob và generation vẫn pending; không được chuyển phase chỉ vì baseline validate.

## Nguồn đã đọc

- [Contracts, Artifact Graph và Invalidation](../codebase/02_contracts_and_artifacts.md): §1 Contract files, §2 Generation tools, §6 Artifact record, §7 Dependency graph, §8 Invalidation functions, §9 Structural và semantic validation.
- [Delivery plan](../10_delivery_plan.md): §2 WP0, Deliverables và Acceptance.
- [ScriptDocument schema hiện hữu](../../../.agents/skills/w5d-script/schemas/script.schema.json): toàn bộ schema 1.0.
- [Skill w5d-script](../../../.agents/skills/w5d-script/SKILL.md): Quy tắc nội dung, Keyword và timing, Validation trước khi trả.

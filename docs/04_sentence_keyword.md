# 04 — Sentence, Keyword, Voice và Timing

> Loại: Design specification đã đồng bộ Contract 1.0  
> Script contract: [`03_script_engine.md`](./03_script_engine.md)  
> Production implementation: [`implementation/codebase/05_script_voice_pipeline.md`](./implementation/codebase/05_script_voice_pipeline.md)

## 4.1 Artifact boundary

```text
ScriptDocument candidate
→ approval/current ScriptDocument
→ VoiceConfig snapshot
→ VoiceAsset
→ provider timing hoặc forced alignment
→ TimingDocument
```

Keyword annotation thuộc `ScriptDocument`. Timing thực tế thuộc `TimingDocument`; không ghi word timestamps hoặc audio duration ngược vào Script.

## 4.2 Emphasis ranges

`emphasisRanges` dùng character offsets half-open trên `narrationText`:

```json
{
  "startChar": 21,
  "endChar": 31,
  "text": "ba chú voi"
}
```

Quy tắc:

- Tối đa ba ranges mỗi sentence.
- Text phải bằng chính xác `narrationText[startChar:endChar]` theo contract character-index semantics.
- Range không overlap, không âm và không vượt text.
- Ưu tiên subject/object, động từ hành động, số lượng hoặc contrast quan trọng.
- Không lưu một mảng từ rời vì occurrence có thể mơ hồ khi text lặp.

Python và TypeScript phải có cross-language fixtures cho tiếng Việt combining marks và emoji. Text được normalize trước khi tính range; không normalize lại sau commit.

## 4.3 Visual text

`visualText` là text overlay ngắn, tối đa 30 ký tự. Dùng `null` nếu sentence không cần overlay.

Visual text:

- Không bắt buộc giống emphasis text.
- Không thay thế narration.
- Phải có glyph trong font manifest.
- Chỉ mô tả nội dung; layout/font/animation thuộc ScenePlan và Timeline.

## 4.4 Estimated timing

`estimatedDurationMs` chỉ dùng trước khi có audio thật. Tổng estimate được tính:

```text
sum(sentence.estimatedDurationMs)
+ interSentencePauseMs × (sentenceCount - 1)
```

Estimate không được dùng làm final timing nếu VoiceAsset/alignment đã tồn tại. Khi user sửa narration, TimingDocument và downstream artifacts trở thành stale.

## 4.5 Voice configuration

Voice job snapshot:

- Current ScriptDocument ID/revision/hash.
- Provider/model/voice IDs từ provider lock.
- Language, speaking rate và style instructions.
- Segment policy, output format, sample rate và channel policy.
- Consent/retention policy.

Narration dài được chia theo sentence boundaries. Mỗi segment có deterministic key dựa trên script hash + voice config + provider adapter version để retry không tạo audio khác ngoài ý muốn.

## 4.6 TTS và audio master

TTS adapter trả audio, duration, sample rate/channels, provider usage/provenance và optional word boundaries.

Pipeline:

1. Synthesize segments.
2. Validate provider response và media type.
3. Store/inspect từng segment.
4. Merge theo sentence order với pause policy.
5. Normalize audio master 48 kHz stereo theo PostprocessConfig.
6. Probe duration và checksum.
7. Tạo VoiceAsset immutable.

Không âm thầm thay narration để khớp provider output.

## 4.7 Alignment và TimingDocument

Nếu provider word boundaries đủ chất lượng, map trực tiếp. Nếu không, alignment adapter chạy trên audio master và narration snapshot.

`TimingDocument` chứa:

- `audioAssetId`, `audioDurationMs`.
- Sentence spans `[startMs, endMs)`.
- Optional word spans.
- Confidence và provider provenance.
- Source mode: `estimated`, `ttsNative`, `forcedAlignment`, `manual`.

Validation:

- Spans tăng đơn điệu, không overlap ngoài policy và không vượt audio duration.
- Mọi sentence có span.
- Token/text mismatch vượt threshold chặn final render.
- Low confidence có thể warning cho preview nhưng phải đạt render threshold ở policy production.
- Tail silence/fade được tính rõ; không cắt voice cuối.

## 4.8 Failure semantics

- Timeout, 429 và provider 5xx: retry với policy versioned.
- Credential/quota/capability invalid: fail non-retryable cho config hiện tại.
- Audio partial/wrong MIME: quarantine rồi cleanup.
- Alignment mismatch: giữ VoiceAsset, fail Timing artifact; không làm hỏng Script.
- User manual timing tạo revision mới và provenance `manual`.

> Tiếp theo: [05_asset_manager.md](./05_asset_manager.md)

# 05 — Script, TTS và Timing Pipeline

## 1. Pipeline

```text
Idea/Input
  → ScriptGenerationJob
  → validate/repair
  → ScriptDocument candidate
  → user approval/current ScriptDocument
  → VoiceJob
  → VoiceAsset + provider timings
  → AlignmentJob nếu cần
  → TimingDocument
```

LLM output không tự động trở thành current artifact nếu project yêu cầu human approval.

## 2. Files

```text
backend/app/application/script/
├── commands.py
├── service.py
├── prompts.py
├── normalization.py
└── approval.py
backend/app/application/voice/
├── service.py
├── alignment.py
└── reconciliation.py
backend/app/providers/
├── llm/base.py
├── tts/base.py
└── alignment/base.py
```

## 3. Script commands

### `script/commands.py`

- `GenerateScriptCommand(projectId, idea, targetDurationMs, language, style, tone, provider, model, approvalMode)`.
- `ImportScriptCommand(projectId, document)`.
- `UpdateScriptCommand(projectId, patch)`.
- `ApproveScriptCommand(projectId, candidateArtifactId)`.

## 4. Script service functions

### `script/service.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `submit_script_generation` | `async (command, actor, idempotencyKey) -> Job` | Validate quota/input, snapshot config, submit job |
| `execute_script_generation` | `async (jobId, context) -> ArtifactRef` | Provider call, normalize, validate, repair tối đa policy, commit candidate |
| `import_script` | `async (command, projectRevision, actor) -> CommitResult` | Validate external document và commit current |
| `patch_script` | `async (projectId, patch, projectRevision, actor) -> CommitResult` | Apply JSON Patch allowlist, validate, invalidate downstream |
| `approve_script` | `async (candidateId, projectRevision, actor) -> CommitResult` | Promote candidate current |

## 5. Script normalization

### `script/normalization.py`

- `normalize_unicode(text) -> str`: Unicode NFC, line endings, control chars.
- `segment_sentences(text, language) -> list[SentenceDraft]`: deterministic segmentation fallback.
- `normalize_entity_instances(script) -> ScriptDocument`: unique instances, canonical IDs.
- `resolve_emphasis_ranges(text, phrases) -> list[TextRange]`: offsets rõ, xử lý phrase lặp.
- `estimate_sentence_duration(text, language, speakingRate) -> int`: milliseconds, chỉ fallback.
- `recalculate_total_duration(sentences) -> int`.

## 6. LLM provider contract

### `providers/llm/base.py`

| Method | Input | Output |
|---|---|---|
| `generate_structured` | messages, schema, model, temperature, timeout, idempotency token | ProviderResult[JSON] |
| `capabilities` | none | model/context/schema support |
| `estimate_cost` | request estimate | CostEstimate |

Provider result lưu model/version, usage, latency, finish reason và safe trace ID. Raw chain-of-thought không được lưu/yêu cầu.

Repair loop chỉ nhận validation issues + invalid document; giới hạn attempts và token/cost budget. Hết budget thì job fail `SCRIPT_VALIDATION_FAILED` kèm candidate diagnostic.

## 7. TTS service

### `voice/service.py`

| Hàm | Signature | Mô tả |
|---|---|---|
| `submit_voice_job` | `async (projectId, VoiceConfig, actor, key) -> Job` | Snapshot current script, quota, submit |
| `execute_voice_job` | `async (jobId, context) -> VoiceResult` | Synthesize, store audio, probe, normalize metadata |
| `build_voice_segments` | `(script, config) -> list[VoiceSegment]` | Sentence text/SSML/pause mapping |
| `merge_audio_segments` | `(segments, outputFormat) -> AudioAsset` | Gap/crossfade policy, timestamps |

### `providers/tts/base.py`

- `synthesize(request: TtsRequest) -> TtsResult`.
- `list_voices(language, filters) -> list[VoiceInfo]`.
- `capabilities() -> TtsCapabilities`.

`TtsResult`: audio stream/file, sample rate, channels, duration, optional word boundaries, usage/provenance.

### `providers/alignment/base.py`

- `align(request: AlignmentRequest) -> AlignmentResult`.
- `capabilities() -> AlignmentCapabilities`.

Final audio master chuẩn: 48 kHz, stereo output; voice source có thể mono nhưng normalize trong audio pipeline. Loudness target và true peak nằm trong PostprocessConfig.

## 8. Alignment

### `voice/alignment.py`

- `needs_alignment(ttsResult, requiredGranularity) -> bool`.
- `align_audio(audioAsset, script, provider) -> AlignmentResult`.
- `map_provider_tokens(tokens, sentenceText) -> list[WordSpan]`.
- `score_alignment(timing, script) -> AlignmentQuality`.

### `voice/reconciliation.py`

- `reconcile_sentence_spans(script, providerSpans, audioDurationMs) -> TimingDocument`.
- `fill_missing_boundaries(spans, policy) -> list[Span]`.
- `enforce_monotonic_spans(spans) -> list[Span]`.
- `compare_estimated_to_actual(script, timing) -> TimingDriftReport`.

Không âm thầm sửa narration text để khớp provider tokens. Mismatch vượt threshold tạo warning/error và yêu cầu regenerate hoặc manual edit.

## 9. Failure và retry

- Provider 429/5xx/network timeout: retryable với backoff/jitter.
- Invalid API key/quota exhausted: non-retryable cho cùng config.
- Invalid structured output: repair loop, sau đó non-retryable job error.
- Alignment low confidence: job có thể succeeded-with-warnings nếu policy cho phép preview; final render bị chặn nếu dưới render threshold.
- Job cancel đóng response stream, không đăng ký partial audio và schedule cleanup object/workspace tạm.

## 10. Tests bắt buộc

- Vietnamese Unicode/range offsets.
- Phrase lặp cho emphasis.
- Entity lifecycle normalization.
- Duration total và target tolerance.
- Provider timing missing/overlap/out-of-order.
- Retry không tạo hai VoiceAsset current.
- Script edit làm stale đúng Timing/ScenePlan/Timeline.

# 14 — Production Configuration, Providers và Operational Limits

## 1. Normative deployment profile

Bản production đầu tiên dùng:

- PostgreSQL là source of truth.
- Redis làm Celery broker/cache/rate-limit; không giữ authoritative Job state.
- S3-compatible object storage có multipart checksum và conditional create.
- Celery workers tách `provider`, `media`, `render` queues.
- Một Celery beat instance active; mọi periodic task còn lấy PostgreSQL advisory lock để chống chạy trùng khi failover.
- OIDC Authorization Code + PKCE cho web; API xác minh JWT access token bằng issuer/audience/JWKS allowlist.
- Export file và signed/revocable share link là publish destination bắt buộc đầu tiên.

Thay thế thành phần trong profile này cần ADR và chạy lại contract, recovery, load và security tests.

## 2. Provider baseline và lockfile

Adapter production baseline dùng OpenAI cho structured script generation, GPT Image family cho image generation, Audio Speech API cho TTS và Audio Transcription có word timestamps cho alignment. Không dùng `dall-e-3`, model xAI hard-code cũ hoặc `google-generativeai` legacy trong production baseline.

Provider/model availability phụ thuộc account/region và thay đổi theo thời gian. Vì vậy source code không hard-code model alias. Mỗi deployment phải commit một manifest đã resolve:

```text
config/provider-lock.yaml
```

Manifest bắt buộc có, cho từng capability:

- `provider`, `apiFamily`, exact `modelId`/snapshot.
- SDK package + exact version.
- region/base URL.
- capability flags: structured output, references, transparency, word timestamps.
- timeout, max attempts, concurrency, cost ceiling.
- data-retention/consent policy ID.
- `certifiedAt`, contract-test build SHA và expiry review date.

`validate_production_settings` fail startup nếu manifest thiếu, dùng alias không immutable khi provider có snapshot ID, model không còn accessible, capability smoke test chưa đạt hoặc certification quá 90 ngày.

Optional Gemini adapter phải dùng maintained `google-genai`; optional xAI adapter phải discover model catalog rồi pin exact supported ID. Provider mới không được thêm trực tiếp vào factory; phải implement port, capability tests, moderation, cost accounting và provenance.

Tham chiếu kiểm chứng:

- [OpenAI models](https://platform.openai.com/docs/models)
- [OpenAI Audio API](https://platform.openai.com/docs/api-reference/audio)
- [Google GenAI SDK migration](https://ai.google.dev/gemini-api/docs/libraries)
- [xAI image generation](https://docs.x.ai/developers/model-capabilities/images/generation)

## 3. Baseline limits

Các giá trị dưới đây là default bắt buộc cho release đầu; chỉ thay bằng versioned workspace/deployment policy.

| Policy | Default |
|---|---:|
| Maximum final video | 10 phút |
| Image original | 25 MiB |
| SVG original | 5 MiB |
| Lottie JSON | 10 MiB |
| Audio original | 100 MiB |
| Video asset | 500 MiB, tối đa 10 phút |
| Remote redirects | 5 |
| Remote connect timeout | 10 giây |
| Remote total timeout | 5 phút |
| Upload session TTL | 24 giờ |
| Signed download URL TTL | 15 phút |
| Share link default/max TTL | 7 ngày / 30 ngày |
| Idempotency record retention | 7 ngày |
| Domain event/SSE replay | 72 giờ |
| Unregistered object cleanup | 24 giờ |
| Soft-deleted project retention | 30 ngày |
| Audit retention | 365 ngày |

Media dimension/frame/codec allowlist nằm trong versioned `MediaPolicy`; decompressed pixels và frame count được kiểm tra trước full decode để chống decompression bomb.

## 4. Job timing và retry

| Setting | Provider/media | Render |
|---|---:|---:|
| Heartbeat interval | 15 giây | 15 giây |
| Lease duration | 60 giây | 90 giây |
| Orphan grace | 30 giây | 60 giây |
| Automatic attempts | 5 | 3 |
| Initial retry delay | 2 giây | 10 giây |
| Maximum retry delay | 5 phút | 10 phút |
| Jitter | full jitter | full jitter |

Retry chỉ áp dụng timeout, connection, 429 và provider 5xx được phân loại retryable. Authentication, unsupported capability, invalid input và policy rejection fail ngay. Celery visibility timeout phải lớn hơn hard task limit cộng orphan grace; render dài dùng lease heartbeat, không dựa duy nhất vào broker timeout.

Webhook thử tối đa 10 lần trong 24 giờ, exponential backoff/full jitter. Signature timestamp chấp nhận lệch tối đa 5 phút và event ID phải chống replay.

## 5. Initial SLO và recovery objective

| Chỉ tiêu | Target ban đầu |
|---|---:|
| API availability hàng tháng | 99.9% |
| Read API p95, không tính media | 300 ms |
| Mutation/job-submit p95 | 500 ms |
| SSE event visible p95 | 2 giây |
| Preview first-ready p95 | 5 giây sau manifest ready |
| Render real-time factor p95 | ≤ 1.5× cho profile 1080p30 chuẩn |
| RPO PostgreSQL | ≤ 5 phút |
| RTO service | ≤ 60 phút |

Load test có thể điều chỉnh target bằng ADR trước release, nhưng không được để trống. Alert thresholds được tạo từ SLO và error budget, không dùng số tùy ý trong dashboard.

## 6. Secret và configuration rules

- Development `.env` chỉ chứa mock/local values; production lấy secret manager.
- Biến bắt buộc được parse bằng typed `Settings`; unknown/misspelled production variables fail startup.
- Credential workspace-specific lưu encrypted envelope với KMS key reference và rotation metadata.
- Provider response/log không được chứa secret, signed URL hoặc raw reference media.
- Config, provider lock, contract version và composition build SHA được ghi vào deployment/version endpoint và artifact provenance.

## 7. Release configuration gate

Production deploy bị chặn nếu:

- provider lock thiếu hoặc smoke test fail;
- policy/limit manifest không có version/hash;
- PostgreSQL migration chưa dry-run;
- backup restore chưa đạt RPO/RTO;
- queue visibility/lease settings không thỏa invariant;
- storage adapter không chứng minh checksum + conditional/idempotent write;
- OIDC issuer/audience, TLS hoặc signing secrets còn development value.

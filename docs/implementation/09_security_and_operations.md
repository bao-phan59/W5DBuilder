# 09 — Security và Operations

## 1. Threat boundaries

Input không tin cậy gồm:

- Script/JSON từ user hoặc agent.
- Uploaded media và filenames.
- Remote URLs.
- AI provider output.
- Webhook payload.
- Prompt/reference images.

Mọi boundary phải validate trước khi đưa vào storage, subprocess hoặc renderer.

## 2. Upload security

- Giới hạn kích thước theo media type và theo project quota.
- Xác minh MIME/magic bytes; không tin extension hoặc client header.
- Tạo server-side filename/asset ID.
- Không dùng user filename làm path.
- Chặn archive bomb và format không cần thiết.
- Media probe/transcode chạy với timeout và resource limit.
- Original immutable; derivative ở namespace riêng.

Malware scanning là requirement production tùy deployment, nhưng interface ingest phải cho phép thêm bước scan.

## 3. Path và URL handling

- API không nhận local filesystem path tùy ý.
- Resolve path phải ở trong storage root đã cấu hình.
- Chặn `..`, symlink escape và alternate path syntax.
- Remote fetch chỉ hỗ trợ `https` và allow policy rõ ràng.
- Chặn loopback, link-local, private network và redirect sang mạng nội bộ để phòng SSRF.
- Download có byte/time limit và content verification.

## 4. Secrets và provider data

- Secret chỉ qua secret manager/environment, không commit vào repo.
- Không log Authorization header/API key.
- Provider request logs mặc định không chứa full prompt/reference media.
- Ghi rõ retention/privacy policy của provider trước production.
- Dev/test mặc định dùng mock; live provider cần explicit enable flag.

## 5. Authentication và authorization

MVP local single-user có thể chưa cần login, nhưng API production phải có:

- Principal rõ ràng.
- Project/resource ownership check ở mọi read/write.
- Role hoặc capability cho render/generate/delete.
- Rate limit/quota cho tác vụ tốn phí.
- Audit event cho mutation quan trọng.

Không dựa vào asset/project ID khó đoán để bảo vệ dữ liệu.

## 6. Subprocess/render isolation

- Không ghép input user thành shell command string.
- Dùng argument arrays và allowlisted options.
- Render workspace riêng cho từng job.
- Resource limits cho CPU, memory, runtime và output size.
- Renderer không có credential không cần thiết.
- Dọn temp data theo lifecycle kể cả job fail/cancel.

## 7. Webhook security

Khi webhook được triển khai:

- HMAC signature có timestamp.
- Replay window và event ID deduplication.
- Retry exponential backoff với giới hạn.
- Endpoint HTTPS.
- Không đưa signed secret vào query string.
- Delivery log không lưu payload nhạy cảm quá retention.

## 8. Observability

### Logs

Structured, có request/job/project ID, operation, duration và error code. Redact secret và privacy-sensitive content.

### Metrics

- API latency/error rate.
- Job queue time/run time/failure/cancel.
- Render real-time factor.
- Provider latency/error/cost.
- Storage size và orphan derivatives.

### Traces

Trace request → application service → provider/job khi production complexity cần. Không bắt buộc distributed tracing cho local MVP.

## 9. Storage lifecycle

- Original, derivative, temporary và output có retention riêng.
- Delete project là recoverable/soft-delete trước permanent purge nếu production.
- Orphan cleanup dựa trên references, không dùng filename guessing.
- Checksum hỗ trợ integrity và deduplication nhưng không thay authorization.

## 10. Backup và recovery

Production readiness yêu cầu:

- Backup metadata/database.
- Policy cho blob storage versioning hoặc backup.
- Restore drill có bằng chứng.
- RPO/RTO được ghi theo deployment.
- Migration có rollback/forward recovery plan.

## 11. Deployment environments

- Development: local/mock, debug cho phép, dữ liệu disposable.
- Test/CI: isolated, deterministic, không secret live.
- Staging: gần production, provider sandbox/quota thấp.
- Production: debug off, strict CORS, TLS, durable storage, monitoring và backup.

Readiness endpoint phải kiểm tra dependency bắt buộc; liveness không gọi provider bên ngoài.

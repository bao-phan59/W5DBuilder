# 10 — Agent/API Gateway

> Loại: Design specification  
> Trạng thái: capability target, chưa được implement. Route, transport và error
> contract chuẩn nằm tại
> [implementation/codebase/04_backend_api_and_services.md](./implementation/codebase/04_backend_api_and_services.md).

## 10.1 Boundary

Agent và web client dùng cùng REST API; không có đường ghi dữ liệu riêng bỏ qua
authorization, quota, validation, revision hoặc audit. OpenAPI là nguồn để sinh
client/tool definitions. Job dài trả `202`, resource Job và URL theo dõi; không giữ
HTTP request cho tới khi provider/render hoàn tất.

Mutation có revision bắt buộc strong `If-Match`; mutation tạo side effect bắt buộc
`Idempotency-Key`. API trả error envelope ổn định và request ID. SSE chỉ báo thay
đổi; client refetch resource chuẩn sau sự kiện.

## 10.2 Route groups

Danh sách này là bản tóm tắt. Không tự thêm route từ tài liệu này nếu chưa cập nhật
OpenAPI và catalog chi tiết.

```text
GET    /api/v1/me
GET    /api/v1/workspaces
GET    /api/v1/workspaces/{workspaceId}/members
GET    /api/v1/workspaces/{workspaceId}/usage
GET    /api/v1/workspaces/{workspaceId}/provider-config
PUT    /api/v1/workspaces/{workspaceId}/provider-config

GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/{projectId}
PATCH  /api/v1/projects/{projectId}
POST   /api/v1/projects/{projectId}:clone
POST   /api/v1/projects/{projectId}:archive

PUT    /api/v1/projects/{projectId}/script
POST   /api/v1/projects/{projectId}/script-jobs
POST   /api/v1/projects/{projectId}/script-candidates/{artifactId}:approve
POST   /api/v1/projects/{projectId}/voice-jobs
POST   /api/v1/projects/{projectId}/scene-plan-jobs
POST   /api/v1/projects/{projectId}/timeline-jobs
POST   /api/v1/projects/{projectId}/render-jobs

POST   /api/v1/projects/{projectId}/uploads
POST   /api/v1/projects/{projectId}/uploads/{uploadId}:complete
GET    /api/v1/assets/{assetId}
POST   /api/v1/assets/{assetId}/processing-jobs
POST   /api/v1/projects/{projectId}/asset-generation-jobs
PUT    /api/v1/projects/{projectId}/asset-map

GET    /api/v1/jobs/{jobId}
POST   /api/v1/jobs/{jobId}:cancel
GET    /api/v1/events/stream?projectId=...

POST   /api/v1/projects/{projectId}/export-jobs
GET    /api/v1/publish-results/{publishResultId}
POST   /api/v1/assets/{assetId}/share-links
POST   /api/v1/share-links/{shareLinkId}:revoke
```

Webhook CRUD, rotation/test route và filter/pagination đầy đủ xem catalog chuẩn.
Baseline publish là export file và signed/revocable share link; external destination
chỉ được expose sau khi adapter được certified.

## 10.3 Agent tool policy

Tool definition được sinh/review từ OpenAPI và chỉ expose capability mà actor hiện
có quyền. Tên tham số dùng camelCase và resource ID có prefix chuẩn. Tool không nhận
local path, raw object-storage key, provider secret hoặc arbitrary callback URL.

Các tool cấp cao tối thiểu:

| Tool | Input chính | Output |
|---|---|---|
| `w5d_generate_script` | `projectId`, `idea`, `targetDurationMs`, style/language | Job resource |
| `w5d_upload_asset` | upload session ID, metadata, optional assignment | Asset/Job resource |
| `w5d_generate_asset` | `projectId`, requirement/entity IDs, prompt policy | Job resource |
| `w5d_compile_timeline` | `projectId`, config, strong ETag | Job resource |
| `w5d_render_video` | `projectId`, render profile ID, confirmation | Job resource |
| `w5d_create_share_link` | output Asset ID, TTL/policy | ShareLink resource |

Agent phải đọc readiness trước render, trình bày validation blocker cho user và giữ
các approval gate. Không tự approve script, final render hoặc external publish nếu
policy/owner chưa cấp quyền rõ ràng.

## 10.4 Tool execution sequence

```text
resolve identity/workspace
  → authorize + read current project/ETag
  → validate tool arguments and quota
  → submit idempotent mutation/job
  → observe Job via SSE/polling
  → refetch canonical artifact/resource
  → request human approval where required
```

Remote asset URL đi qua SSRF-safe fetch policy; upload lớn đi qua presigned multipart
session. Provider call, usage/cost và artifact provenance đều được audit nhưng log
không chứa secret, signed URL hoặc raw media mặc định.

> Tiếp theo: [11_tech_stack.md](./11_tech_stack.md)

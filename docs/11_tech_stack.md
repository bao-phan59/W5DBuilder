# 11 — Tech Stack

> Loại: Current-state inventory và target architecture  
> Cập nhật: 2026-10-05

## 11.1 Nguyên tắc đọc

Tài liệu này tách rõ:

- **Current**: những gì thực sự có trong repository.
- **MVP target**: stack được chốt cho vertical slice đầu tiên.
- **Production target**: stack bắt buộc của bản cuối; local/MVP adapters không thay đổi target này.

Việc một dependency xuất hiện trong `package.json` hoặc `requirements.txt` không có nghĩa chức năng tương ứng đã hoàn thành.

## 11.2 Current repository

### Frontend

- Vite + React + TypeScript.
- Framer Motion, Zustand, Radix UI, Lucide và Axios đã được khai báo.
- UI hiện vẫn là Vite starter.
- Chưa có Remotion Player, scene canvas, timeline editor hoặc API client của W5D.

### Backend

- Có `requirements.txt` với FastAPI và một số AI/media dependencies.
- Có prototype `services/image_gen/generators.py`.
- Chưa có application entrypoint, config module, routes, persistence, workers hoặc tests.
- Prototype image generator chưa được xác nhận với provider thật.

### Infrastructure

- Chưa có Dockerfile, Docker Compose, CI workflow, database migration hoặc deployment manifest.
- Chưa có Remotion project.

## 11.3 MVP target stack

```text
FRONTEND
├── React + TypeScript + Vite
├── Remotion Player: preview composition
├── Framer Motion: UI transitions, không làm video timeline
├── Zustand: editor/session state
├── Radix UI: accessible primitives
└── Typed API client sinh từ OpenAPI hoặc contract chung

BACKEND
├── Python 3.12+
├── FastAPI + Pydantic
├── Service/repository boundaries
├── Local filesystem storage adapter
├── SQLite hoặc file-backed repository cho local MVP
└── In-process/local render jobs với interface có thể thay thế

RENDER
├── Remotion composition dùng chung cho Player và CLI render
├── FFmpeg qua Remotion/media tooling
└── MP4 H.264, 1920×1080, 30 FPS
```

## 11.4 Thành phần chủ động chưa đưa vào MVP

| Thành phần | Khi nào mới thêm |
|---|---|
| Konva/Fabric canvas | Khi DOM interaction layer không đủ cho drag/resize |
| GSAP | Chỉ khi Remotion interpolation không đáp ứng một effect đã đo được |
| PostgreSQL | Bắt buộc cho production; local repository chỉ dùng dev/MVP |
| Redis/Celery | Bắt buộc cho durable production jobs; local runner chỉ dùng dev/MVP |
| S3/MinIO | Bắt buộc cho production object storage; filesystem chỉ dùng dev/test |
| WhisperX | Khi đã chọn TTS/alignment workflow production |
| CLIP/auto tagging | Sau khi Asset MVP ổn định |

## 11.5 Cấu trúc target

```text
W5DBuilder/
├── docs/
│   ├── 01_overview.md ... 12_roadmap.md
│   └── implementation/
├── contracts/                 # schema/versioned examples; tạo ở M0
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   ├── providers/
│   │   ├── workers/
│   │   └── main.py
│   ├── migrations/
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/
│       ├── api/
│       ├── features/
│       ├── editor/
│       └── test/
├── packages/
│   └── video/                # Remotion composition, Player và render runner
└── tests/e2e/
```

Đây là cấu trúc target, không phải mô tả cây thư mục hiện tại.

## 11.6 Quy tắc dependency

- Không thêm hai thư viện giải quyết cùng một vai trò nếu chưa có lý do và ADR.
- Preview và final render phải dùng cùng animation implementation.
- Provider SDK nằm sau adapter; domain model không chứa type của SDK.
- Dependency production phải được pin theo policy của dự án và có smoke test.
- Dependency nặng hoặc có native runtime phải được kiểm tra trên môi trường deploy trước khi đưa vào critical path.

> Tiếp theo: [12_roadmap.md](./12_roadmap.md)

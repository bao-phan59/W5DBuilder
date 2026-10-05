# Universal Tech Stack Discovery & Toolchain Reference

Cẩm nang nhận diện và kích hoạt công cụ tự động cho các hệ sinh thái ngôn ngữ và framework phổ biến.

---

## 1. Bảng tra cứu Toolchain đa ngôn ngữ

| Ngôn ngữ / Hệ sinh thái | Manifest & Lockfiles | Package Manager | Test Runner | Linter / Formatter | Typechecker | Build / Run |
|---|---|---|---|---|---|---|
| **TypeScript / Node.js** | `package.json`<br>`pnpm-lock.yaml`<br>`yarn.lock`<br>`bun.lockb`<br>`package-lock.json` | `pnpm`<br>`yarn`<br>`bun`<br>`npm` | `pnpm test`<br>`npm test`<br>`npx vitest run`<br>`npx jest` | `npx eslint .`<br>`npx oxlint`<br>`npx @biomejs/biome check .` | `npx tsc --noEmit` | `npm run build`<br>`npm run dev` |
| **Python** | `pyproject.toml`<br>`requirements.txt`<br>`poetry.lock`<br>`uv.lock`<br>`Pipfile` | `uv`<br>`poetry`<br>`pip`<br>`pipenv` | `pytest`<br>`poetry run pytest`<br>`uv run pytest`<br>`python -m unittest` | `ruff check .`<br>`flake8 .` | `mypy .`<br>`pyright` | `python main.py`<br>`uvicorn main:app --reload` |
| **Rust** | `Cargo.toml`<br>`Cargo.lock` | `cargo` | `cargo test` | `cargo clippy -- -D warnings`<br>`cargo fmt --check` | *(Included in `cargo check`)* | `cargo build`<br>`cargo run` |
| **Go** | `go.mod`<br>`go.sum` | `go` | `go test ./...` | `golangci-lint run`<br>`go vet ./...` | *(Native Go compiler)* | `go build ./...`<br>`go run .` |
| **Java / Kotlin** | `pom.xml`<br>`build.gradle`<br>`build.gradle.kts` | `mvn`<br>`gradle`<br>`./gradlew` | `mvn test`<br>`./gradlew test` | `mvn checkstyle:check`<br>`./gradlew check` | *(Native javac / kotlinc)* | `mvn package`<br>`./gradlew build` |
| **C# / .NET** | `*.sln`<br>`*.csproj` | `dotnet` | `dotnet test` | `dotnet format --verify-no-changes` | *(Native Roslyn compiler)* | `dotnet build`<br>`dotnet run` |
| **PHP** | `composer.json`<br>`composer.lock` | `composer` | `vendor/bin/phpunit`<br>`vendor/bin/pest` | `vendor/bin/phpcs`<br>`vendor/bin/phpstan` | `vendor/bin/phpstan analyse` | `php artisan serve`<br>`composer start` |

---

## 2. Cách phát hiện Monorepo và Cấu trúc dự án hỗn hợp

Khi một kho chứa bao gồm nhiều ngôn ngữ hoặc dịch vụ:

1. **Kiểm tra cấp thư mục gốc (Root level)**:
   - Nếu có `backend/` và `frontend/`: Phân chia ngữ cảnh và chạy commands tương ứng với thư mục con (`cwd: backend` hoặc `cwd: frontend`).
   - Nếu có `packages/` hoặc `apps/` (Turborepo, Nx, Lerna, Cargo workspace):
     - Dùng command quản lý cấp workspace (ví dụ: `pnpm --filter <app> test`, `cargo test -p <crate>`).
2. **Sử dụng Script hỗ trợ**:
   - Chạy: `python <skill-dir>/scripts/stack_detect.py --root . --json`
   - Nhận về cấu trúc tổng thể và các gợi ý command phù hợp mà không cần phỏng đoán.

---

## 3. Khám phá Tài liệu (Documentation Discovery)

Universal Code Runner ưu tiên tìm kiếm các nguồn tài liệu theo thứ tự:
1. `docs/` hoặc `documentation/`: Thư mục tài liệu kiến trúc, specs, API guides.
2. `specs/` hoặc `spec/`: Tài liệu đặc tả kỹ thuật và acceptance criteria.
3. `README.md`: Hướng dẫn tổng quan dự án, cách cài đặt, chạy tests.
4. `PROJECT_NOTES.md` hoặc `architecture/`: Ghi chú kỹ thuật, ADRs (Architectural Decision Records).
5. `contracts/` hoặc `schemas/`: OpenAPI YAML/JSON, JSON Schemas, Protobuf/gRPC specs.

Sử dụng `python <skill-dir>/scripts/doc_slice.py --root . --file <doc-path> --headings` để quét mục lục tài liệu trước khi đào sâu vào từng section.

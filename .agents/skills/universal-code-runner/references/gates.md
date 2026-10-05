# Universal Quality Gate và Verification

Tài liệu quy định tiêu chuẩn kiểm soát chất lượng (Quality Gate), tiêu chí nghiệm thu (Acceptance Criteria) và quản lý bằng chứng (Evidence) cho mọi dự án phần mềm.

---

## 1. Trạng thái Quality Gate

| Trạng thái | Ý nghĩa | Cho phép chuyển Phase? |
|---|---|---|
| `pending` | Chưa chạy kiểm tra hoặc chưa hoàn tất đủ acceptance criteria | **Không** |
| `pass` | Mọi kiểm tra bắt buộc (required) đều đạt PASS; evidence hợp lệ | **Có** |
| `fail` | Có ít nhất một kiểm tra bắt buộc bị lỗi hoặc hành vi sai khác | **Không** |
| `blocked` | Bị chặn do thiếu môi trường, dependency bên ngoài hoặc quyền hạn | **Không** |
| `needs_revalidation` | Code/config/fixtures đã thay đổi làm bằng chứng cũ bị lỗi thời | **Không** |

> **Nguyên tắc vàng**:
> - Không bao giờ sửa mock hoặc xóa assert để "ép" gate chuyển sang PASS.
> - Dự án không có test suite sẵn thì viết test suite là một task bắt buộc trong batch, không được coi việc thiếu test là PASS.
> - Build/biên dịch thành công không thay thế cho bài test kiểm tra hành vi (functional tests).

---

## 2. Các tầng kiểm tra tiêu chuẩn (Gate Verification Tiers)

Mỗi Phase/Batch cần trải qua các tầng kiểm tra phù hợp với phạm vi:

### Tầng 1: Static Quality (Cú pháp & Kiểu dữ liệu)
- **Linter**: `eslint`, `oxlint`, `biome`, `ruff`, `flake8`, `golangci-lint`, `clippy`... Đảm bảo không có lỗi cú pháp hoặc vi phạm convention nghiêm trọng.
- **Typechecker**: `tsc --noEmit`, `mypy`, `pyright`, `go vet`, `cargo check`... Bảo đảm an toàn kiểu dữ liệu (type-safety).

### Tầng 2: Unit & Domain Logic (Kiểm thử đơn vị)
- Kiểm tra các hàm thuần túy (pure functions), tính toán, chuyển đổi dữ liệu và logic nghiệp vụ cốt lõi.
- Chạy nhanh (trong vòng vài giây), độc lập với database hoặc mạng bên ngoài.

### Tầng 3: Contract & Boundary (Ranh giới & Giao diện)
- Kiểm tra tính tương thích của API schemas, serialized JSON, DTOs, cơ sở dữ liệu migration.
- Đảm bảo hợp đồng giữa client và server hoặc giữa các modules không bị phá vỡ.

### Tầng 4: Integration & Mock/Offline Flow (Tích hợp cục bộ)
- Kiểm thử luồng xử lý end-to-end với in-memory mock hoặc container cục bộ.
- Kiểm tra cả kịch bản thành công (happy path) và xử lý ngoại lệ (failure/error cases).

### Tầng 5: Build & Packaging (Đóng gói)
- Chạy lệnh build thực tế (`npm run build`, `mvn package`, `cargo build --release`, `go build`).
- Đảm bảo mã nguồn sau khi sửa không làm hỏng quy trình đóng gói.

---

## 3. Cấu trúc Bằng chứng Kiểm thử (Evidence Schema)

Mỗi lượt kiểm tra phải sinh ra một file bằng chứng JSON lưu tại:
`.coder/evidence/<phase>/<batch>/check_<id>.json`

```json
{
  "check_id": "CHK-P0-01",
  "requirement_ids": ["P0-AC01"],
  "phase": "P0",
  "batch": "P0-B01",
  "command": ["pytest", "tests/test_auth.py", "-v"],
  "cwd": "backend",
  "started_at": "2026-10-06T06:50:00Z",
  "finished_at": "2026-10-06T06:50:03Z",
  "duration_seconds": 3.2,
  "exit_code": 0,
  "status": "pass",
  "code_fingerprint": {
    "git_head": "a1b2c3d",
    "changed_files": ["backend/app/auth.py", "backend/tests/test_auth.py"]
  },
  "summary": "12 tests passed, 0 failed, 0 warnings",
  "log_tail": "tests/test_auth.py::test_password_hash PASSED\ntests/test_auth.py::test_jwt_encode PASSED"
}
```

---

## 4. Quy trình Xử lý khi Gate Thất bại hoặc Bị chặn

1. **Giữ nguyên log lỗi**: Đọc tối đa 50–80 dòng log liên quan trực tiếp đến lỗi. Không in ngập màn hình với full trace.
2. **Chẩn đoán nguyên nhân gốc (Root Cause Analysis)**:
   - Phân biệt giữa lỗi do code logic, lỗi do thiếu fixture/test setup, hay lỗi do môi trường.
3. **Quy tắc 2-Retry Limit**:
   - Chỉ được thử sửa tối đa 2 lần cho cùng một lỗi.
   - Nếu sau 2 lần vẫn fail: Dừng lại, ghi nhận nguyên nhân, giả thuyết hiện tại và chuyển trạng thái task/gate thành `blocked` hoặc `fail`.
   - Báo cáo rõ ràng cho người dùng, không bao giờ rơi vào vòng lặp vô tận (infinite retry loop).
4. **Môi trường thiếu dependencies**:
   - Nếu thiếu dịch vụ (Docker, Redis, PostgreSQL, external API key, GPU): đánh dấu check là `blocked`, hoàn thành các task độc lập trước; không tự tiện đổi thành mock rồi công bố pass.

# Universal Checkpoint, Resume và Crash Recovery

Tài liệu hướng dẫn quản lý trạng thái thực thi (state management), ghi nhận bằng chứng (evidence) và cơ chế khôi phục sau sự cố (crash recovery) cho **bất kỳ dự án phần mềm nào**.

Runtime state nằm trong thư mục làm việc của dự án (mặc định `.coder/` hoặc `.agent-runner/`), hoàn toàn độc lập với skill.

---

## 1. Cấu trúc thư mục Runtime State

```text
<project-root>/
└── .coder/
    ├── state.json                 # Trạng thái tổng quát, compact index (mục tiêu ≤ 12.000 ký tự)
    ├── journal.jsonl              # Nhật ký tuần tự dạng append-only, ghi nhận mỗi batch/gate
    ├── phases/
    │   ├── P0.json                # Kế hoạch chi tiết, tasks và requirements của Phase 0
    │   ├── P1.json                # Phase 1 ...
    │   └── Pn.json
    └── evidence/
        └── Pn/
            └── <batch-id>/
                ├── check_<id>.json    # Bằng chứng kết quả test, exit code, log tóm tắt
                └── summary.txt        # Tóm tắt output ngắn gọn
```

---

## 2. Invariants bất biến

1. **Schema Version**: `schema_version = 1`. Mọi thay đổi cấu trúc phải tương thích ngược hoặc có migration rõ ràng.
2. **Current Pointer**: `current_phase` (ví dụ `P0`, `P1`, `Phase-1`, `auth-feature`) và `current_batch` (ví dụ `P0-B01`).
3. **Status Enums**:
   - Task / Phase: `pending`, `in_progress`, `done`, `blocked`.
   - Gate: `pending`, `pass`, `fail`, `blocked`, `needs_revalidation`.
4. **Không suy diễn DONE**:
   - Một task chỉ được chuyển sang `done` khi có bằng chứng test/linter thực tế (`evidence`).
   - Một phase chỉ được coi là `pass` khi toàn bộ required requirements đã có evidence hợp lệ và gate tổng hợp đạt PASS.
5. **Next Action cụ thể**: Trường `next_action` luôn là một hành động kỹ thuật thực thi được ngay (ví dụ: `Chạy pytest tests/test_auth.py và triển khai hàm hash_password`), không viết chung chung như "làm tiếp".
6. **Bảo mật tuyệt đối**: Tuyệt đối không ghi credentials, passwords, private keys, JWT tokens hoặc file `.env` thô vào `state.json`, `journal.jsonl` hay `evidence/`.

---

## 3. Quy chuẩn Cập nhật Atomic (Atomic State Update)

Để chống hỏng dữ liệu khi gặp sự cố đột ngột (mất điện, kill process, gián đoạn mạng, context full):

1. **Serialize JSON** trong bộ nhớ và kiểm tra tính toàn vẹn (validate fields).
2. **Ghi vào file tạm**: `state.json.tmp` trong cùng thư mục với `state.json`.
3. **Flush & Sync**: Đảm bảo toàn bộ nội dung đã được ghi xuống đĩa.
4. **Atomic Rename / Replace**: Đổi tên `state.json.tmp` thành `state.json`. (Trên POSIX: `os.replace`, trên Windows: `os.replace` nguyên tử trong cùng phân vùng).
5. **Append Journal**: Ghi 1 dòng JSON vào `journal.jsonl` ghi nhận sự kiện:
   ```json
   {"timestamp": "2026-10-06T06:45:00Z", "phase": "P0", "batch": "P0-B01", "event": "batch_completed", "next_action": "..."}
   ```

---

## 4. Thuật toán Resume (Khôi phục & Tiếp tục)

Khi nhận lệnh tiếp tục (`continue` hoặc phiên chat mới):

1. **Parse State**: Đọc `.coder/state.json`. Nếu file bị hỏng, khôi phục từ bản backup gần nhất hoặc tái thiết từ `journal.jsonl` và `evidence/`.
2. **Worktree Inspection**:
   - Nếu có Git: Kiểm tra `git status` và `git diff` để xác định các file đã sửa.
   - Nếu không có Git: So sánh hash file (`file_hashes`) của các file liên quan.
   - Giữ nguyên các thay đổi của người dùng; chỉ quản lý các file trong phạm vi batch hiện tại.
3. **Evidence Reconcile**:
   - Nếu source code hoặc config đã thay đổi kể từ lần chạy test gần nhất: đánh dấu check đó là `needs_revalidation`.
   - Không đọc lại toàn bộ tài liệu specs; chỉ đọc section cần thiết cho batch kế tiếp.
4. **Crash State Recovery**:
   - Nếu state trước đó bị dừng giữa chừng (`in_progress`): kiểm tra code hiện hữu, chạy lại test tương ứng. Nếu test đã pass, chuyển task thành `done`; nếu lỗi, sửa tiếp.
5. **Thực thi `next_action`**: Đọc spec/requirements liên quan và bắt đầu batch mới.

---

## 5. Cấu trúc Task và Requirement

```json
{
  "task": {
    "id": "P0-T01",
    "batch": "P0-B01",
    "status": "pending",
    "goal": "Tạo BaseModel và unit test cho User schema",
    "depends_on": [],
    "requirement_ids": ["P0-AC01"],
    "source_refs": ["docs/architecture.md#User-Model"],
    "changed_files": ["src/models/user.py", "tests/test_user.py"],
    "check_ids": ["CHK-P0-01"],
    "evidence_paths": [".coder/evidence/P0/P0-B01/check_01.json"]
  },
  "requirement": {
    "id": "P0-AC01",
    "assertion": "User schema từ chối email không hợp lệ và mã hoá mật khẩu",
    "required": true,
    "status": "pending",
    "task_ids": ["P0-T01"],
    "check_ids": ["CHK-P0-01"]
  }
}
```

---

## 6. Ví dụ Lệnh Khởi động và Resume

- `Dùng $universal-code-runner lập kế hoạch triển khai từ tài liệu docs/`
- `Dùng $universal-code-runner bắt đầu P0, triển khai một batch rồi checkpoint.`
- `Dùng $universal-code-runner tiếp tục từ .coder/state.json, làm batch kế tiếp.`
- `Dùng $universal-code-runner kiểm thử quality gate của phase hiện tại.`

---
name: universal-code-runner
description: Triển khai code và tính năng cho bất kỳ dự án phần mềm nào (đa ngôn ngữ/framework) theo quy trình phase-driven: chia batch nhỏ (1–3 tasks), test-driven verification, kiểm soát quality gate và tự động checkpoint phục hồi khi gián đoạn. Dùng khi cần lập kế hoạch implementation, sinh code mới, tiếp tục tính năng đang dở, chạy test gates hoặc kiểm tra tiến độ codebase.
---

# Universal Code Runner

Sinh mã nguồn và triển khai phần mềm có cấu trúc cho **bất kỳ ngôn ngữ, framework hay kiến trúc nào**. Giữ context gọn gàng bằng cách chia nhỏ thành các batch kiểm chứng được, kiểm soát chất lượng qua Quality Gate và đảm bảo khả năng phục hồi (crash recovery) nhờ atomic checkpoint. Việc cài đặt skill không tự khởi động code khi chưa có lệnh.

---

## 1. Phạm vi và Chế độ hoạt động

Skill hỗ trợ 4 chế độ chính:

- `start` / `continue`: Đối chiếu trạng thái hiện tại, tự động nhận diện tech stack nếu chưa có, chọn batch kế tiếp, implement mã nguồn và chạy verification tests.
- `test [phase]`: Chạy kiểm thử Quality Gate của phase được chỉ định hoặc phase hiện tại; ghi nhận bằng chứng (evidence); không tự chuyển phase nếu người dùng chỉ yêu cầu test.
- `status`: Đọc checkpoint và evidence reports, báo cáo tiến độ và công việc kế tiếp; không thay đổi code.
- `plan`: Khám phá dự án từ tài liệu (docs, specs, PRD, README) hoặc mô tả yêu cầu, lập danh sách Phases/Tasks vào state; chưa viết code triển khai.

**Quy tắc một lượt chạy (Turn Budget)**:
- Mặc định mỗi lượt xử lý **một batch** trong phase hiện tại (1–3 atomic tasks có liên quan).
- Khi người dùng yêu cầu chạy liên tục, tiếp tục batch tiếp theo nếu còn đủ token budget và gate cho phép.
- Luôn checkpoint sau mỗi batch. Không hứa tự mở phiên chat mới. Khi dừng lượt do giới hạn context, cung cấp câu lệnh handoff chính xác để người dùng tiếp tục ở phiên sau.
- **An toàn**: Không tự ý commit, git push, deploy lên production, hoặc gọi các third-party API có tính phí nếu chưa có sự đồng ý rõ ràng trong phiên hiện tại.

---

## 2. Nguồn sự thật (Source of Truth) & Nhận diện Tech Stack

1. **Project Root**: Xác định root từ workspace hiện tại hoặc đường dẫn người dùng cung cấp. Không hardcode ổ đĩa hay hệ điều hành.
2. **Ưu tiên kỹ thuật**:
   - `contracts/` / schemas / type definitions / interfaces (nếu có)
   - Tài liệu kỹ thuật chi tiết (`docs/`, `specs/`, `architecture/`)
   - Tài liệu tổng quan (`README.md`, `PRD.md`, `PROJECT_NOTES.md`)
   - Yêu cầu trực tiếp từ prompt của người dùng.
3. **Phát hiện Stack & Công cụ tự động**:
   Trước khi lập kế hoạch hoặc sinh code, chạy helper:
   ```powershell
   python <skill-dir>/scripts/stack_detect.py --root . --json
   ```
   Helper sẽ tự động phát hiện ngôn ngữ (TypeScript, Python, Go, Rust, Java, C#, PHP...), framework (React, FastAPI, Next.js, Spring...), package manager (`pnpm`, `npm`, `poetry`, `uv`, `cargo`...), và đề xuất chính xác các câu lệnh test/lint/typecheck cho cả repo đơn lẫn monorepo.
4. **Không suy diễn DONE**: Một tính năng chỉ được xem là hoàn thành khi có bằng chứng test/build thực tế chạy thành công; không dựa vào việc "code nhìn có vẻ đúng" hoặc test chưa chạy.

---

## 3. Giới hạn Context & Đọc tài liệu an toàn (Bounded Reads)

Để tránh làm tràn hoặc loãng context window của mô hình:

- **Mục tiêu 1 Batch**: Một vertical slice nhỏ, độc lập và kiểm chứng được (thường 1–3 tasks).
- **Nguyên tắc đọc tài liệu**:
  - Không đọc toàn bộ thư mục docs hay in toàn bộ source tree.
  - Dùng helper `doc_slice.py` để duyệt mục lục hoặc trích xuất đúng section cần thiết:
    ```powershell
    python <skill-dir>/scripts/doc_slice.py --root . --file docs/spec.md --headings
    python <skill-dir>/scripts/doc_slice.py --root . --file docs/spec.md --section "## Feature Auth" --max-chars 10000
    ```
- **Giới hạn Test Logs**: Chỉ trích xuất phần tóm tắt kết quả và log lỗi trực tiếp (≤ 80 dòng). Tuyệt đối không in credentials hay dữ liệu nhạy cảm vào context/log.
- **Dừng an toàn khi cạn context**: Khi nhận thấy context đã lớn, không bắt đầu task mới; hoàn tất thao tác đang dở ở điểm an toàn, lưu checkpoint rồi trả handoff.

---

## 4. Quy trình 8 bước Universal Execution Engine

Trong mỗi batch, thực hiện tuần tự 8 bước:

```text
[1. Resume & Reconcile] ──> [2. Stack Discovery] ──> [3. Select Batch] ──> [4. Plan Before Edit]
                                                                                   │
[8. Phase Gate Check]   <── [7. Atomic Checkpoint] <── [6. Verify Tests]  <── [5. Implement Slice]
```

1. **Resume & Reconcile**:
   - Đọc `.coder/state.json` (hoặc khởi tạo từ [assets/state.template.json](assets/state.template.json) nếu chưa có).
   - Kiểm tra `git status` / diff hoặc file hashes.
   - Nếu code hoặc config đã đổi kể từ lần test trước, đánh dấu check liên quan là `needs_revalidation`.
2. **Stack Discovery**:
   - Đảm bảo `tech_stack` và các lệnh `test`, `lint`, `typecheck` trong state khớp với codebase thực tế (tham khảo [references/discovery.md](references/discovery.md)).
3. **Select Batch**:
   - Đọc phase hiện tại trong [assets/phase.template.json](assets/phase.template.json) hoặc file `phases/Pn.json`.
   - Chọn 1–3 tasks kế tiếp; đảm bảo các điều kiện tiên quyết (prerequisites) đều đã đạt.
4. **Plan before edit**:
   - Xác định rõ: Mục tiêu batch, task IDs, files cần tạo/sửa, contracts liên quan, deliverables và lệnh kiểm thử cụ thể.
   - Gán mã định danh ổn định (ví dụ `P0-T01`, `P0-AC01`).
5. **Implement (Vertical Slice)**:
   - Viết code theo lát cắt: Data types/Schemas → Business logic → Services/Handlers → Tests.
   - Giữ pure domain logic độc lập với external frameworks; mock/offline các dịch vụ bên ngoài (database, third-party APIs) trước khi kết nối môi trường thật.
6. **Verify Tests & Batch Checks**:
   - Chạy lệnh test thực tế cho các thay đổi vừa tạo.
   - Chạy linter và typechecker liên quan.
   - Ghi nhận `exit_code`, câu lệnh, thời gian chạy và lưu bằng chứng vào `.coder/evidence/`.
   - **Xử lý khi test fail**: Tìm nguyên nhân gốc, sửa chữa. **Tối đa 2 lần retry cho 1 lỗi**; nếu vẫn không đạt, checkpoint giả thuyết/blocker, không lặp vô hạn và tuyệt đối không xóa/skip test để vượt gate.
7. **Atomic Checkpoint**:
   - Cập nhật tiến độ vào `.coder/state.json` thông qua file tạm `.tmp` rồi replace để chống corrupt file khi crash (tham khảo [references/checkpoint.md](references/checkpoint.md)).
   - Ghi 1 dòng nhật ký vào `journal.jsonl`.
8. **Phase Gate Check**:
   - Khi toàn bộ tasks và requirements của phase đã có bằng chứng PASS: tham khảo [references/gates.md](references/gates.md) và chạy kiểm tra gate tổng hợp.
   - Gate PASS → chuyển sang phase tiếp theo.
   - Gate Fail/Blocked → giữ nguyên phase hiện tại, ghi rõ blocker.

---

## 5. Quy tắc Bất biến khi gặp Sự cố

- **Mã nguồn người dùng đang có (Dirty Tree)**: Tuyệt đối không chạy `git reset --hard` hoặc `git clean -fd`. Phân biệt rõ ràng giữa file người dùng đang làm và file agent tạo/sửa.
- **Thiếu dịch vụ môi trường (Docker, Database, API Key)**: Đánh dấu check là `blocked`, hoàn thành các phần logic độc lập với mock; không thay test thật bằng mock giả vờ rồi công bố PASS.
- **Tài liệu/Yêu cầu thay đổi giữa chừng**: Ghi nhận thay đổi, invalidate các requirements cũ bị ảnh hưởng, mở lại task cần cập nhật dù trước đó đã DONE.
- **Xung đột phạm vi (Scope Conflict)**: Tiếp tục các phần độc lập; chỉ đặt câu hỏi làm rõ khi một quyết định kiến trúc thực sự ngăn cản tiến độ.

---

## 6. Định dạng Bàn giao (Handoff)

Sau mỗi lượt, luôn trả lời ngắn gọn, súc tích bằng tiếng Việt theo cấu trúc:

1. **Trạng thái**: Phase hiện tại, Batch ID vừa hoàn thành.
2. **Mã nguồn**: Các file chính đã tạo/chỉnh sửa.
3. **Kiểm thử**: Lệnh test đã chạy, số test PASS, test nào fail/chưa chạy, trạng thái Quality Gate.
4. **Việc kế tiếp**: Mô tả chính xác 1 bước kỹ thuật có thể làm ngay.
5. **Lệnh Resume mẫu**:
   `Dùng $universal-code-runner tiếp tục từ .coder/state.json, thực hiện batch kế tiếp của <Phase>.`

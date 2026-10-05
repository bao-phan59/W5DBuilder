---
name: w5d-phase-runner
description: Triển khai W5D Builder theo docs/implementation/codebase bằng các batch nhỏ có checkpoint và quality gate từng WP0–WP6. Dùng khi yêu cầu bắt đầu, tiếp tục, kiểm thử hoặc kiểm tra tiến độ implementation theo docs; không dùng chỉ để viết kịch bản video hoặc chỉnh tài liệu.
---

# W5D Phase Runner

Triển khai dần blueprint thành code chạy được, giữ context nhỏ và chỉ chuyển phase khi acceptance có bằng chứng. Việc tạo/cài skill không tự khởi động implementation.

## Phạm vi và chế độ

- `start` / `continue`: đối chiếu trạng thái thật, chọn batch kế tiếp, implement và test.
- `test phase WPn`: kiểm thử gate của phase, sửa lỗi trong phạm vi được giao; không tự chạy phase mới nếu người dùng chỉ yêu cầu test.
- `status`: đọc checkpoint và bằng chứng, báo tiến độ; không thay code.
- `plan`: tạo plan/checkpoint từ docs và inventory, không implement.

Mặc định mỗi lượt xử lý **một batch** trong phase hiện tại. Khi người dùng yêu cầu chạy liên tục, tiếp tục batch sau nếu còn đủ context và gate cho phép; checkpoint sau mỗi batch, không hứa tự mở phiên chat hoặc chạy nền. Khi kết thúc lượt do giới hạn context, ghi lệnh tiếp tục cụ thể. Không tự commit/push/deploy/provider trả phí nếu chưa được yêu cầu hoặc được cho phép trong phiên hiện tại.

## Nguồn sự thật

Áp dụng AGENTS.md tại root và các thư mục sắp sửa. Resolve project root từ workspace hoặc đường dẫn người dùng cung cấp; không hardcode ổ đĩa.

Ưu tiên kỹ thuật: executable contracts trong `contracts/` → `docs/implementation/codebase/` → `docs/implementation/` → design docs `docs/01–12`. Nếu executable contract và spec xung đột, giữ tương thích hiện tại, ghi conflict và migration/ADR cần thiết; không âm thầm coi contract cũ là lý do bỏ requirement mới.

`docs/12_roadmap.md` là nguồn status sản phẩm, `docs/implementation/10_delivery_plan.md` định nghĩa acceptance WP. File checkpoint chỉ là con trỏ công việc và evidence, không thay roadmap. Không suy ra DONE từ docs, dependencies, prototype, hoặc test chưa chạy.

## Giới hạn context

Mặc định là **budget vận hành**, không phải phép đo token chính xác:

- Một batch: một mục tiêu kiểm chứng được, thường 1–3 task có liên quan; không gộp cả phase lớn.
- Doc input mục tiêu ≤ 6.000 token ước lượng/batch; mỗi output đọc ≤ 12.000 ký tự; tổng doc text ≤ 24.000 ký tự. Văn bản tiếng Việt/code có thể dùng nhiều token hơn, giảm budget khi context đã lớn.
- Lần đầu chỉ lấy index README, heading roadmap/delivery plan và inventory source đã lọc. Đọc section WP hiện tại và spec liên quan theo nhu cầu. Không cat toàn bộ docs hoặc mọi reference.
- Chỉ đọc 1–2 spec section mỗi lần; mở thêm khi cần giải quyết dependency cụ thể, lưu lý do.
- Dùng `rg --files -g '!node_modules' -g '!.venv' -g '!dist' -g '!build' -g '!.git'`; `rg -n` tìm symbols/headings. Nếu output bị truncate, thu hẹp truy vấn trước khi tiếp tục.
- Test log đầy đủ để ngoài context; đọc tóm tắt và phần lỗi ≤ 80 dòng. Không in secrets/provider response chứa thông tin nhạy cảm.
- Khi context sắp đầy hoặc không biết phần còn lại: không bắt đầu task mới; hoàn thành thao tác đang dở ở điểm an toàn, ghi checkpoint rồi trả handoff. Không dừng giữa migration, transaction hoặc thao tác ghi không thể phục hồi.

Helper đọc giới hạn dùng Python standard library:

```powershell
python <skill-dir>/scripts/doc_slice.py --root . --file docs/implementation/codebase/02_contracts_and_artifacts.md --headings
python <skill-dir>/scripts/doc_slice.py --root . --file docs/implementation/10_delivery_plan.md --section "## 2. WP0" --max-chars 10000
python <skill-dir>/scripts/doc_slice.py --root . --file docs/implementation/codebase/02_contracts_and_artifacts.md --start 40 --lines 90 --max-chars 10000
```

Resolve `<skill-dir>` thành đường dẫn skill thật và quote trên Windows. Helper trả số dòng tiếp theo, SHA-256 doc và cảnh báo khi vượt hạn mức; output budget không phải token budget. Chế độ `--headings` không coi heading trong fenced code là section.

## Quy trình mỗi batch

1. **Resume:** đọc `.w5d/implementation/state.json` nếu có và tail journal cần thiết. Kiểm tra source, manifests, fixtures, diff hiện tại và evidence liên quan. Nếu chưa có state, đọc [references/checkpoint.md](references/checkpoint.md), copy [assets/state.template.json](assets/state.template.json) vào project và lập WP0 sau khi inventory; không overwrite state có sẵn.
2. **Reconcile:** kiểm tra doc hash của phần đã dùng, thay đổi code/manifests/fixtures kể từ evidence. Evidence bị stale → gate `needs_revalidation`, xác định phạm vi regression cần chạy. Nếu không có Git, dùng hash file; thiếu evidence thì đánh dấu chưa xác minh. Không đọc lại toàn bộ docs để reconcile.
3. **Select:** từ [references/phases.md](references/phases.md) đọc **section WP hiện tại**, lấy acceptance gốc tương ứng. Bảo đảm prerequisites DONE có gate hợp lệ. Phase A–F trong `12_end_to_end_execution.md` là bước runtime, không phải delivery phase. Nếu phase quá rộng, tách task nhỏ giữ cùng WP.
4. **Plan before edit:** ghi mục tiêu batch, task ID, source file + section/hash, contracts ảnh hưởng, dependencies, deliverables, acceptance và commands kiểm thử. Requirement ID ổn định như `WP0-AC01`; map mỗi requirement đến code/test/evidence, không chỉ checklist tổng quát. Chưa biết command thì inspect manifest, thêm runner/test cần thiết vào scope thay vì tưởng tượng command đã tồn tại.
5. **Implement:** hoàn thành vertical slice nhỏ, mock/offline trước provider thật. Giữ pure domain, application-owned transaction, worker session riêng; generated types phải regenerate từ schema. Hạ tầng local MVP phải có adapter boundary để thay production ở WP6. Tránh dựng toàn bộ production layer ngay WP1.
6. **Batch checks:** chạy targeted tests và lint/type/build liên quan thay đổi. Bổ sung test hành vi cho happy path/failure path quan trọng. Chưa có test suite là task cần làm, không phải PASS. Chỉ mở rộng kiểm thử khi integration/contract impact hoặc lỗi mới đòi hỏi. Ghi exit code, command, cwd, thời gian, fixture/output và fingerprint code được test.
7. **Checkpoint:** lưu task đã xong/dở, findings, changed files, tests, gate, blocker và task kế tiếp. Viết JSON atomically qua file tạm cùng thư mục rồi rename/replace; giữ state cũ nếu serialize lỗi. Append journal ngắn, không chép transcript/log vào state.
8. **Phase gate:** chỉ khi mọi task và acceptance của WP đã có evidence, đọc [references/gates.md](references/gates.md) và chạy gate tổng hợp. Gate PASS → cập nhật roadmap đúng milestone mapping và lưu next WP. Gate fail/blocked → giữ phase hiện tại. Nếu scope cho phép và còn budget, bắt đầu batch mới; không chuyển phase chỉ vì code build được.

## Trường hợp cần xử lý

- Interrupted task: inspect thay đổi và rerun test liên quan trước khi nhận DONE; không làm lại mọi thứ.
- Test fail: giữ log, sửa nguyên nhân, rerun test lỗi và regression chịu ảnh hưởng. Sau hai lần sửa cùng lỗi không tiến triển, checkpoint nguyên nhân/giả thuyết còn lại; không vòng lặp vô hạn, không xóa/skip test để vượt gate.
- Thiếu Docker/Postgres/Redis/MinIO/browser/FFmpeg/key: ghi `blocked` cho check tương ứng, hoàn thành task độc lập còn được phép; không thay production test bằng mock rồi tuyên bố PASS.
- Docs đổi: lưu source mới và invalidation của requirement bị ảnh hưởng; mở lại phase/task cần sửa dù trước đó DONE. Không tự giữ PASS cũ.
- Dirty tree: giữ nguyên thay đổi người dùng; phân biệt phần mình sửa. Không reset/clean hoặc stage mọi thứ.
- Scope conflict/migration breaking: ghi evidence cụ thể, tiếp tục phần độc lập; chỉ hỏi khi quyết định còn thiếu thực sự ngăn tiến độ.

## Handoff

Trả ngắn bằng tiếng Việt: WP/batch hiện tại, kết quả và files chính, tests đã chạy/thất bại/chưa chạy, gate, đường dẫn checkpoint, task tiếp theo. Ví dụ lệnh: `Dùng $w5d-phase-runner tiếp tục từ .w5d/implementation/state.json, làm batch kế tiếp của WP0.` Nêu rõ skill cần người dùng gọi tiếp ở phiên mới; checkpoint giúp resume, không bảo đảm context tự động không bao giờ đầy.

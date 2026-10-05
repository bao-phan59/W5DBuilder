# Quality gate và evidence

Đọc khi chuẩn bị chuyển phase hoặc revalidate gate. Test command phải lấy từ scripts/manifests/CI thật. Nếu repo chưa có runner, triển khai runner với tests trong batch phù hợp; không ghi command ví dụ thành evidence.

## Gate decision

| Trạng thái | Ý nghĩa | Có chuyển WP? |
|---|---|---|
| pending | Chưa chạy hoặc chưa đủ acceptance | Không |
| pass | Mọi required acceptance đạt, evidence còn hợp lệ | Có |
| fail | Required check fail hoặc acceptance sai | Không |
| blocked | Required check không chạy được vì môi trường/authorization | Không |
| needs_revalidation | Code/docs/fixture/config đổi làm evidence stale | Không |

Một check `not_applicable` chỉ hợp lệ khi requirement thực sự không áp dụng theo source/scope có ghi lý do. Required check không được đổi thành optional để vượt gate. Failed check rồi rerun pass giữ cả evidence cũ và mới; gate dùng lần mới nhất phù hợp fingerprint. Known flaky test phải sửa/triage; không rerun vô hạn cho đến xanh.

## Cách chạy

1. Đối chiếu tất cả requirement IDs với tests/deliverables; phần chưa được batch tests cover vẫn cần test hoặc kiểm chứng thích hợp.
2. Chạy lint/type/schema/generated drift/build cho packages liên quan. Build xanh không thay acceptance test.
3. Chạy targeted unit/contract và integration cross-boundary của phase. Chạy cumulative golden path đạt tới WP hiện tại để bắt regression giữa phase; không chạy live provider tốn phí khi scope chưa cho phép.
4. Phase render thêm actual media probe/visual parity; frontend thêm browser; production thêm real services/security/recovery/load theo spec.
5. Kiểm tra clean-environment reproducibility bằng dependencies/lockfiles/startup instructions; dùng workspace/container tạm khi cần, không xoá môi trường người dùng.
6. Lưu report trước khi đổi gate/roadmap. Nếu task DONE nhưng milestone acceptance còn thiếu, để milestone ở trạng thái thích hợp chưa DONE.

## Evidence tối thiểu mỗi check

- `id`, `requirement_ids`, `command` (argument array ưu tiên), `cwd` tương đối root.
- `started_at`, `finished_at` ISO 8601 có timezone, `exit_code`; dùng timezone user cho báo cáo.
- `status`: pass/fail/blocked/not_applicable; blocked có reason và không có exit code giả.
- `source_fingerprints`: SHA-256 docs sections/files được dùng; `code_fingerprint`: Git commit + dirty diff hash hoặc hashes source/manifests/fixtures/config liên quan.
- Runtime versions/profile, mocks vs real services và sanitized config fingerprint; không lưu key/token/raw .env.
- `log_path`, `output_paths`, concise assertions (frame count, duration, conflict status...), không copy cả log.

Evidence paths nằm trong `.w5d/implementation/evidence/<WP>/<batch>/`. Với test report lớn giữ summary riêng; chỉ đọc summary ở resume. Sau khi sửa code, fingerprint mới cần evidence mới cho phần ảnh hưởng. Docs-only roadmap/checkpoint updates không tự làm stale runtime test nếu không ảnh hưởng acceptance; ghi rõ phạm vi fingerprint.

## Khi fail/blocked

Không mở WP sau, không cập nhật roadmap thành TESTED/DONE. Ghi check nào thiếu, nguyên nhân thật, command cần rerun và task độc lập còn có thể làm. Giữ failure artifacts; không xóa assertions hoặc thay real dependency bằng fake để đổi gate. Chỉ hỏi người dùng quyết định còn thiếu; không xin phép lại các bước đã được scope cho phép.

## Release khác phase completion

Gate WP6 PASS xác nhận readiness dựa trên evidence, không tự cho phép publish/deploy. Không push secrets, render/audio blobs lớn hoặc logs chứa dữ liệu khách. Git commit/push chỉ khi được yêu cầu; stage paths thuộc công việc, inspect diff và remote/branch trước push, không force push.

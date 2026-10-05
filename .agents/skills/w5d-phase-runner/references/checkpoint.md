# Checkpoint, resume và crash recovery

Đọc khi tạo state, repair state hoặc resume sau interruption. Runtime state ở project `.w5d/implementation/`, không nằm trong skill portable.

## Files

- `state.json`: con trỏ hiện tại + compact task/requirement index, mục tiêu ≤ 12.000 ký tự. Archive phase cũ trước khi vượt budget và giữ link/evidence summary.
- `journal.jsonl`: append một event ngắn/batch/gate change; resume chỉ tail 3–5 events.
- `phases/WPn.json`: detailed task/acceptance mapping của **một** WP; không đọc tất cả phases.
- `evidence/WPn/<batch>/`: reports/logs/artifact references. Không đưa secrets/raw .env vào đây.

Copy template một lần, điền paths/phase/batch/requirements sau inventory. Template là định dạng khởi tạo, không phải trạng thái thực tế đã hoàn thành. `schema_version=1`; nếu format đổi phải có migration rõ, không tự bỏ fields lạ.

Dùng [phase.template.json](../assets/phase.template.json) để tạo phase file hiện tại. Chưa tạo bảy phase files chi tiết cùng lúc. Hình dạng các phần tử (ví dụ này là pending, không phải evidence đã chạy):

```json
{
  "task": {
    "id": "WP0-T01", "batch": "WP0-B01", "status": "pending",
    "goal": "Validate golden ScriptDocument và từ chối entity reference sai",
    "depends_on": [], "requirement_ids": ["WP0-AC01"],
    "source_refs": ["docs/implementation/10_delivery_plan.md#WP0"],
    "changed_files": [], "check_ids": [], "evidence_paths": []
  },
  "requirement": {
    "id": "WP0-AC01", "required": true, "status": "pending",
    "assertion": "Mọi fixture validate trong CI",
    "source_path": "docs/implementation/10_delivery_plan.md",
    "source_section": "## 2. WP0", "source_sha256": null,
    "task_ids": ["WP0-T01"], "check_ids": [], "evidence_paths": []
  }
}
```

Chép `task` vào mảng tasks, `requirement` vào requirements; source section/hash phải lấy từ doc thật khi inventory. `last_checks` trong state chỉ chứa ID/status/report path; report đầy đủ theo gates reference. Plan cần phủ đủ mọi deliverable/acceptance, không giữ ví dụ trên như toàn bộ WP0.

## Invariants

- `current_phase`: WP0–WP6; `current_batch`: ID ổn định như WP0-B01.
- Phase/task status: pending/in_progress/done/blocked; gate dùng enums riêng trong gates reference.
- Task done cần evidence liên quan; phase done cần gate pass và mọi acceptance required đủ evidence.
- `next_action` mô tả một bước có thể bắt đầu ngay, không ghi chung chung “làm tiếp”.
- `sources` chứa relative path, section/range, sha256 tại thời điểm dùng; changed_sources gây revalidation có phạm vi.
- `worktree` ghi Git head/dirty paths nếu có; nếu không, hashes file cần reconcile. Không yêu cầu initialize Git chỉ để chạy skill.
- Blocker có check/task ID, reason, resolution và điều kiện unblock; không lưu bí mật.
- `authorization` chỉ ghi scope người dùng đã yêu cầu, không coi authorization từ phiên cũ là quyền mới để deploy/tốn phí trong tương lai.

## Atomic update

Serialize/validate JSON trước, ghi `state.json.tmp` trong cùng thư mục, flush rồi replace `state.json`. Giữ backup checkpoint hợp lệ trước replace khi thay đổi cấu trúc. Không để writer khác chạy cùng state: nếu phát hiện người/agent khác đang sửa, reconcile hoặc dùng workspace riêng; không overwrite mù.

Checkpoint trước khi bắt đầu batch (planned/in_progress), sau tests, trước và sau gate transition. Journal ghi event gồm timestamp, batch, action, result, next_action; checkpoint giữ trạng thái mới nhất, journal hỗ trợ audit.

## Resume algorithm

1. Parse state; nếu JSON lỗi, giữ bản hỏng, restore từ backup/journal + evidence rồi kiểm tra source. Không reset toàn bộ progress.
2. Đọc phase hiện tại và event gần nhất, kiểm tra files đã sửa tồn tại/khớp. `in_progress` sau crash có thể chứa implementation đúng nhưng chưa test.
3. So sánh docs và source fingerprints, chọn phạm vi revalidation. Task đã có evidence stale không nhận DONE mới cho tới rerun.
4. Nếu gate pass mà `current_phase` chưa tăng do crash, đối chiếu complete report rồi đồng bộ state/roadmap; không chạy lại implementation.
5. Nếu pointer đã tăng nhưng phase trước chưa đủ evidence, lùi tới phase thiếu và ghi reconciliation event.
6. Tiếp tục `next_action`; chỉ đọc spec sections nó cần.

## Invocation examples

- `Dùng $w5d-phase-runner lập plan từ docs/implementation/codebase, chưa viết code.`
- `Dùng $w5d-phase-runner bắt đầu WP0, một batch rồi checkpoint.`
- `Dùng $w5d-phase-runner tiếp tục từ .w5d/implementation/state.json.`
- `Dùng $w5d-phase-runner kiểm thử gate WP3, giữ phase nếu thiếu browser evidence.`
- `Dùng $w5d-phase-runner chạy liên tục tới hết WP2 trong budget hiện tại; checkpoint sau mỗi batch.`

Ví dụ budget không phải quyền mở rộng scope. Nếu yêu cầu chỉ WP0 thì gate PASS vẫn dừng ở WP0 và lưu WP1 là gợi ý tiếp theo.

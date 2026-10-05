# 08 — Testing và Quality Gates

## 1. Mục tiêu

Test phải chứng minh contract và vertical slice hoạt động, không chỉ tăng coverage. CI mặc định không gọi internet, provider tốn phí hoặc phụ thuộc secret cá nhân.

## 2. Test pyramid

### Unit tests

- Domain validators.
- Entity lifecycle.
- Time/frame conversion.
- Normalized coordinate conversion.
- Layout selection và animation preset interpolation.
- Error classification và retry policy.

### Contract tests

- Mọi fixture validate với schema version tương ứng.
- Backend serialization round-trip.
- TypeScript/Python generated types không drift.
- Provider adapters đáp ứng capability contract bằng mock/fake transport.

### Integration tests

- API + repository + storage temp directory.
- Project revision conflict.
- Asset upload/probe/derivative lifecycle.
- Job creation, progress, cancel và terminal states.
- Timeline compose từ golden ScriptDocument.

### Component/browser tests

- Script validation display.
- Player load/play/scrub.
- Canvas/timeline selection sync.
- Autosave/conflict/error states.
- Golden project happy path.

### Render tests

- Composition smoke test.
- Key-frame snapshots có tolerance.
- Output media probe.
- Preview/final parity tại selected frames.

## 3. Golden project

Fixture “Ba Chú Voi” phải bao gồm:

- Canonical ScriptDocument.
- Estimated TimingDocument cho offline mode.
- Placeholder/local assets với checksum.
- Expected ScenePlan invariants.
- Expected TimelineDocument invariants.
- Expected render metadata.

Fixture không chứa absolute path, secret hoặc dependency vào CDN. Mọi duration tổng phải được tính và kiểm tra tự động.

## 4. Semantic test cases bắt buộc

- Duplicate sentence/entity IDs.
- Non-contiguous sentence order.
- Instance idle/exit trước enter.
- Duplicate enter khi instance đang active.
- Unknown `connectTo` target.
- Declared duration khác tổng sentence duration.
- Frame range âm/rỗng/vượt total frames.
- Missing asset assignment.
- Unsupported preset/provider capability.
- Text hoặc object ngoài normalized bounds.
- Stale project revision.

## 5. Determinism

- Random effect dùng fixed seed trong tests.
- Clock và ID generator injectable.
- Network provider dùng fake transport/recorded minimal fixture phù hợp license.
- Snapshot chỉ dùng cho output ổn định; không snapshot toàn document nếu assertion ngữ nghĩa rõ hơn.

## 6. CI quality gates

Mỗi change phải chạy phù hợp với vùng ảnh hưởng:

1. Markdown/local-link validation.
2. Contract/schema validation.
3. Backend formatting/lint/type check/tests.
4. Frontend formatting/lint/type check/tests/build.
5. Remotion composition smoke test.
6. Golden E2E cho main branch hoặc khi pipeline contract thay đổi.

Không đánh dấu hạng mục `TESTED` nếu test chỉ tồn tại nhưng đang skip hoặc không chạy trong CI.

## 7. Coverage và mutation risk

Không đặt coverage phần trăm làm mục tiêu duy nhất. Bắt buộc coverage cao cho:

- Validators và migration.
- Revision/idempotency.
- Billing/provider retry boundary.
- Render readiness.
- Security-sensitive upload/path/URL handling.

UI presentational component đơn giản có thể test ít hơn, nhưng user workflow chính cần browser test.

## 8. Release evidence

Mỗi milestone lưu:

- Commit/version.
- Commands đã chạy.
- Test summary.
- Golden artifact hoặc media metadata.
- Known limitations.
- Migration notes nếu contract đổi.

Evidence có thể là CI artifacts; không dùng checklist thủ công không truy vết được làm bằng chứng duy nhất.

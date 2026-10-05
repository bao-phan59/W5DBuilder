# Executable contracts

Canonical ScriptDocument 1.0 nằm tại [schemas/script-document.schema.json](schemas/script-document.schema.json); golden fixture là [examples/script-document.elephants.json](examples/script-document.elephants.json).

Schema và fixture trong `.agents/skills/w5d-script/` là mirror portable. Tests kiểm tra byte-for-byte; sửa canonical trước, đồng bộ mirror, không phát triển hai contract khác nhau. Xem [ADR 0001](../docs/implementation/decisions/0001-contract-baseline.md).

Chạy từ root, không cần API key:

```powershell
python -m pip install -r contracts/requirements.txt
python -m unittest discover -s backend/tests/contract -v
python contracts/scripts/validate.py
python contracts/scripts/validate.py path/to/script-document.json
```

CLI trả JSON `ValidationReport {errors, warnings, infos}` cho từng file và exit 1 khi dữ liệu không hợp lệ. File/config schema lỗi là lỗi hạ tầng. Structural validation chạy trước semantic validation, tránh truy cập fields sai kiểu. Domain validator nhận schema registry tường minh, không đọc file/database/network.

Batch đầu chỉ bao phủ ScriptDocument: IDs/references, sentence order, Unicode code-point ranges, lifecycle và duration/tolerance. Nội dung có trừu tượng hay không vẫn cần review authoring; validator không đánh giá chất lượng ngôn ngữ. TimingDocument, ScenePlan, AssetMap, TimelineDocument, RenderJob, generated Python/TypeScript types và round-trip fixtures đang pending; CI hiện chỉ kiểm tra ScriptDocument.

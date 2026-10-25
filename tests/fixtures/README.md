# fixtures/

静态 golden fixtures（由版本控制跟踪，测试只读使用）：

- `golden_complete_repo/`：包含全部 12 条存在性规则目标的完整最小仓库；引擎应产出零 finding（exit 0）。
- `golden_empty_repo/`：空仓库（仅 `.gitkeep` 以便 git 跟踪空目录）；应产出全部 12 条 finding（exit 1）。
- `golden_empty_report.json`：空仓库报告的 summary + findings 快照，锁定 JSON 输出结构；有意修改规则文案时必须同步更新此文件。

运行时构建的临时 fixture 仍在 `tests/fixture_builders.py`（不使用本目录，也不检查真实用户目录，见 `docs/spec/01-architecture-rules.md` §7）。

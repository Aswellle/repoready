# RepoRead 实施前的默认决策与差距锁定

本文件用于补足原蓝图中少量尚未完全收敛的实施细节。Agent 应按以下默认值先完成 MVP，不要在实现过程中临时扩大范围。

## 命名

品牌名定为 **RepoReady**（2026-10-26 维护者确定）。代码与本地开发标识保持 `reporead`（包名、模块路径、CLI 命令）；发布用名称在发布前由维护者单独决策并重新核验占用情况。当日已核实事实：GitHub 已存在 `kanuwrld/repoready` 与 `OpenSource-Communities/RepoReady`（即 npm `repoready@1.0.0`，2025-09-23 发布）；`shidesheng0218/repo-ready` 为近名；PyPI `reporead`/`repoready` 均未注册（404，非预留）。本轮只按内部标识实现，不注册远端仓库、不发布包、不声称任何名称已最终可用。代码中集中管理版本与命令名。差异化定位与竞品对比见 `IMPLEMENTATION_READINESS_REVIEW.md`（2026-10-26 已审定）。

## MVP CLI 冻结

- 必须实现：`reporead check [PATH]`、`--help`、`--version`、`--format text|json`、`--strict`、`--output PATH`。
- 稳定退出码按 `01-architecture-rules.md` §4 决策表：`0` 无 error 且（strict 下）无 warning；`1` 存在 error，或 strict 模式下存在 warning；`2` CLI 参数、配置、路径访问或输出写入错误。
- **不实现分数、`--min-score` 或复杂配置覆盖。** 文档中的这些能力视为后续候选项，避免用缺乏依据的评分表示仓库质量。
- `--config` 可延后；若实现，必须有明确 TOML schema、未知键错误、路径忽略规则测试，不可接受执行代码的配置。
- `--output PATH` 不创建缺失父目录；写入失败返回 2，stderr 含目标路径与 OS 错误类别。
- Markdown 链接规则 MVP 范围冻结为 README；扩展到其他 Markdown 属 `--config` 之后的候选项。
- Text 和 JSON 必须由同一个内部 Report 模型生成。JSON 以 `report.schema.json` 为契约，示例见 `report-example.json`（须与 schema 及自身 summary 自洽）。

## 实施细节

- 文件存在性规则、README 结构规则和链接规则分别有稳定 `rule_id`；同一 fixture 的 finding 顺序必须确定。
- 对 README 安装说明的判断是启发式，只能写“未检测到”，不能写“没有安装说明”作为绝对结论。
- 本地链接解析需忽略 fenced code blocks；对 Markdown 扩展语法暂不承诺完全覆盖，限制必须记录。
- Python runtime 无第三方依赖。构建/打包可以采用标准的 PEP 517 build backend，但必须把构建工具归类为开发/发布依赖，不得混入运行时依赖。
- GitHub Action 先提供可复制的 workflow 示例；不把自托管 Action 或 marketplace 发布当作 MVP 门槛。

## Phase 0 完成门槛

- [ ] pyproject package metadata、入口点、版本策略和安装路径确定。
- [ ] 文本与 JSON report model 的字段冻结。
- [ ] exit code decision table 有单元测试。
- [ ] `python -m unittest discover -s tests -v` 可执行。
- [ ] 至少覆盖空目录、缺 LICENSE、不可读文件、无效 root、symlink、超大 Markdown、Windows 路径行为的 fixtures。
- [ ] 不联网、不执行目标仓库内容的约束被测试或明确检查。

Phase 0 / Phase 1 通过后再继续实现 Markdown 链接和配置能力。

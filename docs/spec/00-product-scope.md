# RepoReady 产品简报与 PRD

> 品牌名：**RepoReady**（2026-10-26 由维护者确定）。源码、包名与本地 CLI 使用内部开发标识 `reporead`；发布用品牌、PyPI 包名与 CLI 命令在发布前由维护者单独决策，不得宣称已可用。近名项目事实与决策记录见 `IMPLEMENTATION_READINESS_REVIEW.md` §9 与 `../PROJECT_NAMING_AND_RELEASE.md`。

## 一句话定位

推送前最后一道离线、只读的仓库就绪度检查：像 linter 一样用稳定 rule_id 和证据说话，输出可执行的修复清单——不打分。

## 差异化定位（2026-10-26 审定）

与三个近名竞品（`kanuwrld/repoready`、`OpenSource-Communities/RepoReady`、`shidesheng0218/repo-ready`）及已归档的 Repolinter 相比，本项目的主打差异：

1. **README 内部链接与图片完整性检查**：离线校验相对链接/图片路径的存在性，排除 fenced code block 误报。三个竞品均不覆盖。这是头牌功能。
2. **发布元数据一致性**：`pyproject.toml`/`package.json` 关键字段存在性、CHANGELOG 当前版本条目。竞品只检查"文件存在"。
3. **无评分的证据链契约**：稳定 `rule_id` 注册表、schema 版本化 JSON、可复现输出、冻结退出码。与竞品的加权分数制形成反向定位。

Essential files 存在性检查是门槛基础，不作为营销卖点。功能级对比与依据见 `IMPLEMENTATION_READINESS_REVIEW.md`。

## 目标用户

- 刚准备开源个人项目的开发者；
- 独立维护者和小团队；
- 在 PR/Release 前需要快速检查仓库完整性的 CI 管理者。

## 核心任务

`我准备把项目公开给陌生人使用。请告诉我有哪些明显的缺项，优先修复哪些，并让我在本机或 CI 中重复运行检查。`

## MVP 功能

- `reporead check [PATH]` 检查指定目录（默认当前目录）。
- Essential files 存在性：README、LICENSE、.gitignore、依赖/项目 manifest、测试目录或测试配置、CI workflow、CONTRIBUTING、SECURITY、CODE_OF_CONDUCT、CHANGELOG、Issue/PR 模板。
- README 结构提示：H1、安装/运行、使用示例（启发式；结论一律写"未检测到"，不写绝对判断）。
- README 内部链接与图片路径检查（MVP 范围仅 README；fenced code block 排除；外链不联网、只列为未检查）。
- 发布元数据一致性三条规则：pyproject 必填字段、package.json 必填字段、CHANGELOG 条目（只查存在性与格式，不判断语义正确性）。
- 规则注册表：每条规则有稳定 `rule_id`、severity 默认值与一句话 rationale（见 `01-architecture-rules.md` §2a）。
- 输出 text 与 JSON：`--format text|json`、`--strict`、`--output PATH`；JSON 可被 CI 直接读取。
- 退出码决策表冻结（见 `01-architecture-rules.md` §4）：`0` 达标；`1` 存在 error（或 strict 下存在 warning）；`2` CLI 参数/路径/配置/输出写入错误。
- `--version`、`--help`、`--config PATH`（TOML：`rules.disable` 与 `ignore.paths`；未知键、未注册 rule_id 或越界路径返回退出码 2）。
- 没有 token、不上传代码、不安装服务、不自动改写仓库、不联网。

**评分说明**：MVP 不实现分数、权重或 `--min-score`。评分只能作为未来候选由维护者重新决策；当前理由是避免用缺乏依据的数字营造仓库质量精确性。

## 不做

- 评分、权重体系与 `--min-score`。
- AI review、GitHub API、账户登录、云端分析服务、agent-readiness 叙事（若未来加入 AGENTS.md 等检查，仅作为普通存在性规则，不声称"agent 就绪"）。
- 自动生成/覆盖文件、自动修复、fix PR。
- 评判项目商业价值、代码正确性或安全性；文件存在只代表形式检查通过。
- 外链可达性检查（离线约束）。
- 远端仪表盘、SARIF、marketplace 发布。

## 规则结果

每条 finding：`rule_id`、`severity`（error/warning/info）、`title`、`detail`、`path`、`evidence`（只含必要片段/行号）、`suggestion`。JSON 契约为 `report.schema.json`（schema_version 1.0），自洽示例见 `report-example.json`；`rule_id` 全集与 severity 默认值见 `01-architecture-rules.md` §2a 注册表。

## 工程栈

- Python 3.11+ 标准库：`argparse`、`pathlib`、`tomllib`（3.11+，`--config` 启用时）、`json`、`unittest`。
- 零运行时依赖。构建/打包用 PEP 517（setuptools），归类为构建/发布依赖，不混入运行时依赖。
- 可在 Windows、macOS、Linux 运行；路径语义、大小写不敏感文件系统与换行行为需测试。

## 成功标准

- `pip install -e .` 可运行；无需安装时 `python -m reporead` 可运行。
- 同一仓库重复检查输出字节级一致；JSON 报告机器可读且符合 schema。
- 对符号链接、权限错误、超大文件和无效路径安全处理；扫描不逃出仓库 root、不执行目标代码。
- CI 能使用退出码而不是解析人类可读文本。
- 报告不会把整个源码或敏感 token 写到输出中。

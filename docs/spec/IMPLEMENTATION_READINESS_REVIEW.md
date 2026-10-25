# RepoReady 实施就绪复审：竞品差异审计与文档修订计划

> 状态：**待维护者审阅**。本文档是 2026-10-26 审计轮的交付物，只做分析、竞品差异定位与文档修订计划；未实现任何功能代码，未创建远端仓库，未发布包，未推送代码。
> 结论生效前，现有 spec 文档**不应**直接进入 Phase 0 实施。

## 0. 审计范围与方法

- 日期：2026-10-26（竞品与注册表数据为当日快照，均注明来源）。
- 输入：`README_AGENT_START_HERE.md`、`docs/AI_AGENT_WORKING_RULES.md`、`docs/spec/00-product-scope.md`、`docs/spec/01-architecture-rules.md`、`docs/spec/02-implementation-and-acceptance.md`、`docs/spec/IMPLEMENTATION_READINESS_AUDIT.md`、`docs/spec/report.schema.json`、`docs/spec/03-agent-master-prompt.md`，以及包内另两份相关文档 `docs/PROJECT_NAMING_AND_RELEASE.md`、`docs/TECHNICAL_REFERENCES.md`、`docs/spec/report-example.json`。
- 竞品核查方式：读取三个指定 GitHub 仓库的公开 README/仓库元数据（URL 见 §3）；PyPI/npm 占用情况通过官方 JSON API 的 HTTP 状态码核实；Repolinter 通过其 GitHub 仓库核实。
- 基线核查方式：本地命令实际执行（见 §2）。

## 1. 执行摘要

1. **最大竞争风险是 `kanuwrld/repoready`，不是"近名混淆"那么简单。** 它与本包原计划的 MVP 几乎同构：Python 标准库、离线本地扫描、零依赖、无 token、文件存在性规则（README/许可证/CI/manifest/社区文件全套）、text/JSON 输出、退出码 0/1/2、连 `--min-score` 都有。原计划"按现有文档直接实施"在本功能面上**不构成任何差异化**。
2. **市场空缺是真实的。** 该领域此前唯一的成熟离线工具 Repolinter（TODO Group，465 stars）已于 2026-02-06 归档停维；三个指定竞品均极早期（1–28 stars）。需求存在信号，但"又一个文件存在性检查器"不足以承接它。
3. **推荐定位：离线、只读、证据链优先的发布前检查清单，主打三竞品都不覆盖的两类规则**——① Markdown 内部链接与图片完整性（离线防误报），② 发布元数据一致性（manifest 字段、CHANGELOG 条目）；并以"无评分、按 `rule_id` 断言、可复现输出"作为面向 CI 的反向定位。
4. **文档包存在 6 处冲突、4 处含糊、6 项遗漏**（§7），最严重的是：`--min-score` 三处矛盾、退出码触发条件三处表述不一、`report-example.json` 与自身 summary 不自洽、`rule_id` 注册表缺失。
5. **命名事实（当日核查）**：品牌定为 RepoReady，但 GitHub 已有两个同名仓库、npm `repoready` 已被发布占用；PyPI `reporead`/`repoready` 均未注册。内部开发标识保留 `reporead`，发布名延后决策，任何名称不得声称"已可用"（§9）。

## 2. 基线核查结果

| 项 | 结果 |
|---|---|
| Git | 本会话初始化的新仓库，`main` 分支，**零提交**；未跟踪：`README_AGENT_START_HERE.md`、`docs/` |
| 工作区文件 | 仅文档包；无 `src/`、无 `pyproject.toml`、无 `tests/`、无 LICENSE |
| 测试基线 | `python -m unittest discover -s tests -v` 失败：`ImportError: Start directory is not importable: 'tests'` —— 属"尚无测试"而非"已有失败"；不存在可被覆盖的既有实现 |
| Python | 本机 3.11.1，满足 spec 的 3.11+（`tomllib` 可用） |
| 用户修改 | 未发现任何需保护的未提交人工修改（全部文件为文档包本身）；本轮仅新增本文件，未改动任何现有文档 |

## 3. 竞品功能级对比

### 3.1 kanuwrld/repoready（Python，MIT，1 star / 7 commits，极早期）

来源：https://github.com/kanuwrld/repoready （2026-10-26 读取）

- 架构：**Python 3.10+ 标准库、零依赖、离线本地扫描、无 token、不上传代码** —— 与本包原计划的工程约束逐条相同。
- 检查：13 项加权规则（README 15、自动测试 12、CI 12、License 10、依赖 manifest 10、SECURITY 8、CONTRIBUTING 7、Issue 模板 6、COC 5、PR 模板 5、Changelog 5、.gitignore 3、依赖更新策略 2），manifest 生态覆盖 Python/JS/TS/Go/Rust/Java/Ruby/PHP/.NET/Swift 十种。
- 输出：text / JSON / Markdown（GitHub job summary）；**0–100 加权分数**；`--min-score` 阈值；`--output` 写文件；退出码 0/1/2；附带 GitHub Action（`uses: kanuwrld/repoready@v0.1.0`）。
- 路线图：可配置权重、SARIF、按生态的规则包。

**与本包原计划重合度：约 90%（MVP 功能面几乎完全一致，且对方已实现并挂了 Action）。**

### 3.2 OpenSource-Communities/RepoReady（TypeScript / Node 16+，MIT，2 stars，npm 已发布）

来源：https://github.com/OpenSource-Communities/RepoReady ；npm `repoready@1.0.0`，发布于 2025-09-23（registry API 核实）。

- 形态：**联网工具**。`rr evaluate owner/repo` 走 GitHub API（未认证 60 req/h，token 5k/h）；另有 `rr create` 交互式建仓。
- 检查：12 项加权（README 20、CONTRIBUTING 15、License 15、COC 12、Description 10、Good first issues 10、Topics 8、Issue 模板 8、Help wanted 8、PR 模板 7、仓库名 5、未归档 5），社区健康文件可回退到 org 级 `.github` 默认文件。
- 输出：分数 + 五档评级 + Top-5 优先建议；README 未提及退出码、报告文件或机器可读 JSON。
- 特性上有一半依赖 API 才能拿到（issues/topics/归档状态），**与"离线、只读本地"定位天然不冲突**；但仓库与 npm 包同名，构成品牌混淆主体。

### 3.3 shidesheng0218/repo-ready（JavaScript / Node 20+，MIT，28 stars）

来源：https://github.com/shidesheng0218/repo-ready （2026-10-26 读取）

- 形态：**"AI 编码代理就绪度"检查与修复器**（pnpm monorepo：CLI + GitHub Action + 可选自托管 web）。默认离线静态分析，不执行仓库脚本；可选 AI 增强需 API key。
- 检查：AGENTS.md / CLAUDE.md / Cursor rules 存在性；验证命令（test/build/lint/typecheck）；README 质量信号（安装/使用/测试/贡献）；CI 存在；上下文卫生（生成物、缓存、大文件、忽略目录）；安全信号（危险脚本、force push、DB reset、生产部署）。
- 输出：Overall + Agent Ready + Safety 三个分数、Agent Failure Risk 高/中/低、PASS/REVIEW 证据链、分级修复计划（safe-auto / review / manual）；`--ci --min-score 80`、`--json`/`--markdown`、双语输出、`--profile codex|claude|cursor`；`doctor --write`、`fix --apply-safe`、fix PR。
- 重合点：README 质量启发式、CI/测试存在性、仓库卫生；**不重合且不打算重合**：agent 就绪叙事、自动修复/生成文件、评分。

### 3.4 补充背景（非指定竞品，但影响定位判断）

- **Repolinter**（todogroup/repolinter，Node，Apache-2.0，465 stars）：老牌规则制仓库 linter，本地离线、YAML/JSON 规则集、JSON/Markdown 输出、可自动修复。**2026-02-06 已归档（read-only，停维）**——来源：其 GitHub 仓库。事实含义：离线规则制仓库检查器这一生态位目前**无在维护的成熟占位者**；其用户群是潜在的迁移来源。
- **GitHub 内置 Community Standards 面板**（平台常识，未另行取证）：仓库页 Insights 已免费展示 README/License/COC/CONTRIBUTING/Issue 模板/安全策略等存在性。含义：**推送到 GitHub 之后**的存在性检查价值被平台吸收；本工具的价值窗口在"推送前"（本地/CI 内）与"存在性之外的内容级检查"。README 定位话术必须直面这一点。
- **lychee（Rust 链接检查器）、markdown-link-check（Node）**：链接检查需求存在的一般性证明；据公开资料 lychee 支持 `--offline`（本轮未验证）。含义：链接检查不是空白市场，但"零依赖 Python、仓库就绪证据链的一部分、CI 输出契约统一"是可辩护的差异。

## 4. 功能盘点：已有同类 / 独特价值 / 缺证据假设

### 4.1 竞品已覆盖（我们做了也不构成差异）

- 文件存在性全套（README/LICENSE/manifest/CI/CONTRIBUTING/SECURITY/COC/CHANGELOG/模板/.gitignore）——三家竞品均覆盖，kanuwrld 与本包规则面几乎一致。
- 多生态 manifest 识别——kanuwrld 覆盖 10 种。
- JSON 输出、稳定退出码 0/1/2、`--min-score`、GitHub Action 示例——kanuwrld 全部已有。
- README 结构启发式（安装/使用信号）——repo-ready 已有更细的信号集。
- 离线、本地、不执行目标代码——三家的默认行为即如此。

### 4.2 本包独有或领先的点（当前真实存在的差异）

1. **无评分哲学**：三竞品全部以加权分数为核心叙事；本包以"必需项阈值 + 证据 + 建议"替代（且与用户技术约束一致）。这是反向定位，但需要营销上能自洽（见假设 A3）。
2. **Markdown 内部链接/图片完整性检查（离线、fenced code block 防误报）**：三竞品均无；已有 spec（01 §5）与 Phase 2 安排。目前是最硬的功能差异。
3. **`rule_id` + evidence + suggestion + schema 版本化的严格 JSON 契约**：竞品的 JSON 停留在"结果转储"，无 rule 注册与契约演进承诺；对 CI 断言方有价值，但需先补注册表（§7 O1）才能兑现。
4. **跨平台路径语义与安全边界测试的明确要求**（symlink containment、大小写不敏感 FS、2 MiB 上限、权限错误不崩溃）：竞品未展示同等工程纪律——这是质量差异而非功能差异，传播价值有限，但决定口碑。

### 4.3 缺乏证据的假设（实现前必须标注，不得当卖点写）

- **A1 "开发者会在推送前本地跑就绪检查"**：三个指定竞品采纳量都极小（1–28 stars），可能说明需求被 GitHub 面板吸收或 CLI 形态需求弱；Repolinter 的长期存在与归档则是相反信号。验证方式：发布后观察自然搜索/install 数据与 issue 渠道，不做预先宣称。
- **A2 "只查本地链接"有人愿意装**：链接检查需求已被 lychee 等证明存在，但用户是否需要"零依赖 Python 子集"未证实。机会窗口是零安装成本与统一 JSON 契约。
- **A3 "无评分"被接受为优点**：三竞品都用分数，说明分数有传播力；本取舍面向 CI/审计者，可能牺牲社区传播。用稳定退出语义 + 每规则 severity 替代分数，作为可辩护的立场而非掩饰。
- **A4 "发布元数据一致性"需求强度**：Python 打包侧已有 pyroma、check-manifest 等邻域工具（本轮未逐一核查覆盖面），冻结具体规则前需在实现期做一轮核对，避免重造。
- **A5 "结构检查 ≠ 质量保证"被用户正确理解**：措辞已规划（"未检测到"而非"没有"），真实误读率未知；输出文案与 README 需持续兑现。

## 5. 差异化切入点评估（标准库可实现）

评估维度：用户价值 / 实现成本 / 竞争重合 / 可测试性。均满足：Python 3.11+ 标准库、离线、只读、可解释证据。

### D1（推荐·头牌）：Markdown 内部链接与图片完整性检查

- 内容：README（MVP 范围建议冻结为 README，见 §7 C7）中的本地相对链接、引用式链接、本地图片路径存在性；URL 编码、fragment、空格、Windows 分隔符；排除 fenced code block；symlink 目标 containment；锚点校验降为 info 级。
- 用户价值：**高**。发布前 README broken link 是高频、可行动、可客观判定的缺陷；GitHub 渲染暴露但无推送前检查。
- 实现成本：**中高**。链接解析子集（内联/引用/autolink）、编码、路径边界都要测试；纯 `re` + `urllib.parse` + `pathlib` 可行，无需依赖。
- 竞争重合：**三指定竞品为零**；lychee 等通用链接工具属不同安装形态与定位。
- 可测试性：**极好**。纯函数 + 合成 fixtures，天然契合 01 §7 的测试原则。
- 结论：**升格为本项目头牌功能**。原计划已有 Phase 2，但应从"顺手实现"改为"主打卖点"（文档、README 首屏、演示均以此为首例）。

### D2（推荐·纳入但可裁剪）：发布元数据一致性检查（manifest 内容级）

- 内容：MVP 限 3 条规则——① `pyproject.toml` 关键字段存在性（name/version/description/license 或 license-files/readme）；② `package.json` 同类关键字段；③ CHANGELOG 含 Unreleased 或最近版本条目。只查存在性与格式，不判语义正确性，不承诺"包能正确发布"。
- 用户价值：**高**。竞品全部停留在"manifest 文件存在 +2 分"；字段缺失直接造成 PyPI/npm 页面信息缺失，是发布前真实痛点且修复建议可精确到字段。
- 实现成本：**中**。`tomllib` 读 pyproject、`json` 读 package.json、CHANGELOG 行级正则；生态扩展（Cargo/go.mod）留后续。
- 竞争重合：与三指定竞品为零；与 pyroma/check-manifest 等打包邻域工具有潜在部分重合（A4，实现期核对后冻结）。
- 可测试性：**极好**（tomllib/json fixtures 正反例）。
- 结论：**建议纳入首版**（Phase 2.5），若维护者希望首版更薄，可整体移至 v0.2，不阻塞 Phase 0–2。

### D3（推荐·定位主张而非功能）：无评分的证据链契约

- 内容：稳定 `rule_id` 注册表（单一事实源 + 唯一性测试）、每规则 severity 默认值表、schema 版本化 JSON、同输入同环境**字节级可复现**输出、退出码决策表锁定。明确不引入分数与权重。
- 用户价值：**中高**（面向 CI 集成者与审计场景，不面向普通传播）；"checklist, not horoscope"是与三竞品分数制形成鲜明对比的立场。
- 实现成本：**低**——是纪律不是功能，但必须先补 §7 的 O1/O2/C4，否则承诺无法兑现。
- 竞争重合：竞品均为分数制，反向定位清晰；规则制的 Repolinter 已归档，无活跃对位者。
- 可测试性：**好**（决策表测试、JSON 稳定性测试、注册表唯一性测试均已可列）。
- 结论：作为定位主张写入 README 与文档，配套补齐契约基础设施。

### 明确不进入的竞品领地

- 评分/权重体系（三竞品主打，且用户约束禁止无依据精确性）。
- GitHub API / 联网评估 / org 级默认文件回退（OpenSource-Communities 领域）。
- AGENTS.md/CLAUDE.md/agent profiles/simulate（repo-ready 领域；未来若加，仅作为普通文件存在性规则，不得声称"agent readiness"）。
- 自动修复、生成文件、fix PR（违反本项目只读原则）。
- 交互式建仓（完全不同的任务）。
- 外链可达性检查（技术约束禁网）。

## 6. 推荐定位与修订后 MVP 范围

**定位一句话（建议稿）**：推送前最后一道离线检查——像 linter 一样用稳定规则 ID 和证据说话，专查文件存在性检查不覆盖的 README 内部链接完整性与发布元数据一致性，不打分。

**修订后 MVP 范围**：

1. Phase 0（骨架）与 Phase 1（essential files 存在性）**保留原样**——存在性规则是门槛基础，但营销上不作为差异点。
2. Phase 2 = D1 链接检查（升格为主打）；扫描范围 MVP 冻结为 README（理由与待决点见 C7）。
3. Phase 2.5 = D2 三条元数据规则（建议纳入，维护者可裁剪至 v0.2）。
4. CLI 冻结面：`reporead check [PATH]`、`--format text|json`、`--strict`、`--help`、`--version`；**建议新增 `--output PATH`**（见 C3 决策）；`--config` 延后；`--min-score` 明确移出。
5. 退出码决策表（统一三处矛盾表述，建议稿，待维护者确认）：

| 情形 | 默认 | `--strict` |
|---|---|---|
| 无 error 且无 warning | 0 | 0 |
| 有 warning、无 error | 0 | 1 |
| 有 error | 1 | 1 |
| CLI 参数/配置/路径访问/输出写入错误 | 2 | 2 |

6. severity 默认值建议（待维护者确认后写入规则注册表）：error = README 缺失、LICENSE 缺失、有代码但无任何 manifest、README 内本地链接目标不存在；warning = .gitignore、CI workflow、CONTRIBUTING/SECURITY/COC/CHANGELOG 缺失、README 无 H1/安装/使用信号、manifest 关键字段缺失；info = 模板缺失、锚点不存在、CHANGELOG 无当前版本条目、外链"未检查"提示。

**明确不做（首版冻结）**：评分、`--min-score`、网络请求（含 GitHub API 与外链可达性）、AI/agent 叙事规则、自动修复与文件生成、远端仪表盘、SARIF、多生态 manifest 内容级检查（只做 pyproject/package.json）。

## 7. 文档冲突、模糊与遗漏清单

### 冲突（C）

| # | 问题 | 位置 | 建议 |
|---|---|---|---|
| C1 | `--min-score` 三处矛盾：MVP 功能清单与 Phase 3 均包含它，审计文件却冻结"不实现分数" | `00-product-scope.md` MVP 段；`02-implementation-and-acceptance.md` Phase 3；`IMPLEMENTATION_READINESS_AUDIT.md` 冻结段 | 以审计文件为准回改 00/02，把 `--min-score` 与评分整体挪入"后续候选"并注明取舍理由 |
| C2 | 退出码触发条件三处表述不一："1 检查未达标"（00）、"error 或低于阈值"（01，引用已冻结的阈值概念）、"阻断问题或 strict 下 warning"（审计） | 三份 spec 各自的退出码段 | 采用 §6 的统一决策表，三处引用同一张表；"低于阈值"措辞删除 |
| C3 | 01 §7 要求"输出文件写入失败时返回 2"并列为验收，但 CLI 冻结面（审计）与 00 的 CLI 清单中**没有 `--output` 参数**——该退出路径当前不可实现也不可测 | `01-architecture-rules.md` §7；`IMPLEMENTATION_READINESS_AUDIT.md` CLI 冻结 | 决策二选一：MVP 纳入 `--output PATH`（CI 常见需求，kanuwrld 亦有），或从验收中删除该退出路径。**建议纳入** |
| C4 | `report-example.json` 与自身 summary 不自洽：声明 `warning_count=2`、`failed_rule_count=3`，但 findings 仅 1 条 error；且通过规则不产生 finding，`passed_rule_count` 如何得出无任何文档定义 | `report-example.json`；`report.schema.json` | 修复示例使 summary 与 findings 一致；在规则注册表文档中定义"通过/失败/跳过"的计数语义 |
| C5 | `rule_id` 命名约定缺失：schema 仅约束非空字符串，点分命名风格只出现在示例中；无注册表、无稳定性承诺、无变更策略——而"稳定 rule_id"正是给 CI 断言用的核心承诺 | `report.schema.json`；`01-architecture-rules.md` §2 | 新增规则注册表（`docs/rules.md` 或源内常量表 + 唯一性测试）：`rule_id`、severity 默认、类别、一句话 rationale、状态 |
| C6 | 品牌与内部标识不一致：全套文档用 RepoRead/reporead；品牌已定为 RepoReady；同时 npm `repoready` 已被占用（OpenSource-Communities 项目，2025-09-23 发布）、GitHub 已有两个同名仓库，而命名文档仍把 RepoRead 标为"暂定" | 全部文档；`PROJECT_NAMING_AND_RELEASE.md` §1 | 品牌统一为 RepoReady（含近名共存风险的 README 消歧句）；内部开发标识保留 `reporead`；发布名延后决策；按 §9 事实更新命名文档。本轮不改代码标识 |
| C7 | 链接规则扫描范围模糊：00 说"检查 Markdown 本地相对链接"未限定文件面；01/02 未明确是仅 README 还是全仓库 `*.md`。全仓扫描会放大误报面与性能面 | `00-product-scope.md`；`01-architecture-rules.md` §5 | 建议 MVP 冻结为 README + 显式列出扩展路径（`docs/` 白名单列入 `--config` 后续能力），写死默认值 |
| C8 | 锚点校验深度两处口径不一：01 说锚点为 informational、首版不必覆盖全插件规则；02 Phase 2 验收要求"fragment…测试通过"但未定义 fragment 与锚点的边界 | `01-architecture-rules.md` §5；`02-implementation-and-acceptance.md` Phase 2 | 写死定义："fragment"指 `path#frag` 的 path 部分存在性（可测）；锚点与标题匹配为 info 级、非阻断、允许不完整 |

### 模糊（除上表外的含糊点）

- **M1** 一个规则产生多条 finding 时 `failed_rule_count` 的口径；规则"不适用/跳过"（如仓库无 manifest 时 manifest 内容规则）在 schema 中无状态可表达。→ 随注册表一并定义；schema 本版可不动，但要在文档声明"跳过不计入 passed/failed"。
- **M2** `00-product-scope.md` 的成功标准提到"后续提供 `python -m reporead`"，而架构要求 `__main__.py`——两者一致，但"零安装运行"未列为验收项。→ 建议把 `python -m reporead` 在源码目录可运行写进 Phase 0 验收。

### 遗漏（O）

| # | 缺失项 | 影响 |
|---|---|---|
| O1 | 规则注册表（单一事实源） | C4/C5/M1 无法闭环；"稳定 rule_id"承诺无载体 |
| O2 | 每规则 severity 默认值表 | exit code 语义悬空（C2 的根因） |
| O3 | `--output` 决策 | C3；CI 消费 JSON 的标准姿势缺失 |
| O4 | 误报清单的维护载体 | 02 验收要求"误报场景写在文档"但未指定文件（建议 `docs/false-positives.md`，每规则一节） |
| O5 | 竞品对比与定位话术 | `TECHNICAL_REFERENCES.md` 的 RepoRead 节仅一句近名提醒，未记录 kanuwrld 的高重合度与 Repolinter 归档事实；README 将无法回答"为什么不是它" |
| O6 | "不联网"的可验证声明方式 | 01/02 要求不联网但未规定验证手段（建议：代码层无网络模块导入断言 + fixtures 层显式说明，避免夸大"已证明"） |

## 8. 文档修订计划（本轮不执行，待维护者批准）

按文件列出需要的改动；全部为计划，未落笔：

1. **`00-product-scope.md`**：移除 `--min-score` 出 MVP（C1）；CLI 面与审计冻结对齐并含 `--output` 决策（C3）；链接规则范围冻结为 README（C7）；定位段加入差异化卖点（D1/D2）与"与近名项目的区别"一段（O5）；品牌表述统一。
2. **`01-architecture-rules.md`**：退出码改为引用统一决策表（C2）；新增"规则注册表与 severity 默认值"节（O1/O2）；写死 fragment/锚点边界（C8）；明确跳过计数语义（M1）；补"不联网"验证方式（O6）。
3. **`02-implementation-and-acceptance.md`**：Phase 3 移除 `--min-score`、加入 `--output`（C1/C3）；Phase 1 验收加入注册表唯一性与 example 自洽（C4/C5）；Phase 2 验收对齐 C8 定义；Phase 2.5 增补 D2 的三条规则与正反 fixtures 验收；验收清单补 O4/O6。
4. **`IMPLEMENTATION_READINESS_AUDIT.md`**：命名段更新为"品牌 RepoReady 已定、内部标识 reporead、发布名延后"（C6）；CLI 冻结加入 `--output` 与链接范围默认值（C3/C7）。
5. **`report.schema.json`**：v1.0 契约字段**保持不变**（避免未发布先破坏契约）；可选的 `meta`（禁用规则列表、strict 标志）列为 v1.1 候选并记录。**`report-example.json` 修复为自洽示例**——属错误修复，不构成契约变更（C4）。
6. **`03-agent-master-prompt.md`**：开头加入"先读 `IMPLEMENTATION_READINESS_REVIEW.md`"；差异化规则（D1/D2）的优先级说明；品牌措辞统一。
7. **`README_AGENT_START_HERE.md`**：品牌统一；按当前现状（就地初始化的 git 仓库）更新"推荐操作"表述（C6/C11 性质）。
8. **`PROJECT_NAMING_AND_RELEASE.md`**：§1 名称表更新为已核实事实与日期（§9）；保留"发布前重查"要求。
9. **`TECHNICAL_REFERENCES.md`**：RepoRead 节扩充为竞品表（三个指定竞品 + Repolinter 归档 + GitHub 面板与 lychee 备注），并加"实现期需重新核验"标记（O5）。

## 9. 命名决策记录（不宣称可用）

> **更新（2026-10-26，维护者决策）**：发布名定为 RepoReady，PyPI 包名、import 包名与 CLI 命令统一为 `repoready`（代码标识已由 `reporead` 更名）；MIT 许可证已确认。本节以下内容为决策前的历史记录，"内部标识 reporead"等表述已过时。

| 名称 | 当日事实（2026-10-26 核查） | 决策 |
|---|---|---|
| 品牌 RepoReady | GitHub 已存在 `kanuwrld/repoready` 与 `OpenSource-Communities/RepoReady`；npm `repoready` 已被发布（v1.0.0，2025-09-23） | **采用**（维护者已定）。接受近名共存风险：README 发布稿必须含消歧说明（区别于 npm 上那款联网评估工具）。不得在任何文档声称该名称"可注册/已可用" |
| PyPI `reporead` | 404（未注册，非预留） | **暂留为内部开发标识**（包名、CLI 命令、模块路径）。发布前重查，不构成可用性承诺 |
| PyPI `repoready` | 404（未注册，非预留） | 发布名候选，由维护者在发布决策时单独确定 |
| npm `reporead` | 404（未注册） | 本项目不发布 npm 包；仅记录事实 |
| GitHub 仓库名 | 两个同名仓库已存在 | 本轮**不创建**远端仓库；最终仓库名由维护者决定 |

以上均系时点核查，发布时必须重新核验；本轮无任何注册、发布、推送动作。

## 10. 修订后验收门槛（合并 02 清单，新增项加粗）

- [ ] 只读静态检查，不执行目标仓库代码；**无任何网络模块导入（O6 规定的验证方式）**
- [ ] 无 runtime dependency；`pip install -e .` 与 `python -m reporead` 均可运行
- [ ] Path traversal / symlink 不逃出仓库 root；链接规则目标 containment 有测试
- [ ] 大文件上限；权限错误降级为 finding 不崩溃
- [ ] Markdown link check 不联网，fenced code block 排除有测试
- [ ] **规则注册表存在且被唯一性测试覆盖；每条规则有 severity 默认值（O1/O2）**
- [ ] **`report-example.json` 与 schema 及自身 summary 自洽（C4）**
- [ ] JSON 含 schema version、稳定排序、明确 path 与 remediation；**同输入同环境两次运行字节级一致**
- [ ] **退出码决策表（§6）被单元测试覆盖：default/strict × error/warning/CLI error 至少 6 个用例（C2）**
- [ ] **D1 fixtures 覆盖：URL 编码、空格、fragment、Windows 分隔符、symlink containment、fenced block 误报（若 D1 纳入首版）**
- [ ] **D2 fixtures 覆盖：pyproject/package.json/CHANGELOG 正反例（若 D2 纳入首版）**
- [ ] **`--output` 写入失败返回 2 并给出路径与 OS 错误类别（若按建议纳入）**
- [ ] exit codes documented and tested；误报场景集中在 `docs/false-positives.md`（O4）
- [ ] 不把"文件存在"表述为"代码质量/安全已保证"；启发式结论一律用"未检测到"措辞
- [ ] **README 草稿含与近名项目的消歧说明（C6）**

## 11. 本轮边界与下一步

本轮已完成：全量文档阅读、基线核查（git/文件/测试/Python）、三个指定竞品功能级对比、注册表占用核查（PyPI/npm）、差异化切入点评估（D1–D3）、文档冲突/模糊/遗漏清单（C1–C8/M1–M2/O1–O6）、修订计划与验收门槛。

本轮未做（按指示）：修改任何现有 spec 文档、实现功能代码、创建远端仓库、发布包、推送代码、提交 git commit。

**待维护者决策的四个问题**：
1. 是否接受推荐定位（D1 头牌 + D2 纳入首版 + D3 无评分主张），还是裁剪 D2 至 v0.2？
2. `--output` 是否纳入 MVP（建议：纳入）？
3. §6 退出码决策表与 severity 默认值建议是否照准（尤其：README 缺失定 error、LICENSE 缺失定 error）？
4. 批准后是否按 §8 顺序执行文档修订，再进入 Phase 0？

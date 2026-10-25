# 误报场景与规则边界

规则是结构启发式检查；本文记录每条规则的已知误报（false positive）、
漏报（false negative）与 MVP 子集边界。修改规则文案时必须同步更新
`tests/fixtures/golden_empty_report.json` 快照与本文件。

## 存在性规则（`repo.*`）

- 只验证"存在"，不验证内容正确性。有 LICENSE 不代表许可证选择正确。
- README 识别 `readme.md`/`readme`/`readme.rst`/`readme.txt`/`readme.markdown`
  （大小写不限）。**注意**：RST/TXT 格式的 README 只查存在性——其中的链接
  使用 RST 语法，link 规则只解析 Markdown 链接，对 rst 文件不产出链接类
  finding（已知漏报方向）。
- License 识别 `LICENSE(.md/.txt)`、`LICENSE-<后缀>`/`licence-<后缀>`（如
  ripgrep 的 `LICENSE-MIT`）、`COPYING(.txt/.lesser)` 与 `UNLICENSE(.txt)`。
- `.gitignore` 要求精确小写文件名：git 在大小写敏感文件系统上只读
  `.gitignore`，因此 `.Gitignore` 会被判缺失——在 Windows 本地看可能
  像误报，但跨平台发布时是真实风险。
- manifest 清单为冻结的 12 种文件名（见 `rules/repository_files.py`），
  未收录的生态（如 `cabal.project`、`deno.json`）会误报缺失；**只查根
  目录**，manifest 仅存在于子目录的 monorepo 会误报缺失。
- 测试规则识别冻结信号集：目录 `tests/`、`test/`、`e2e/`、`__tests__/`
  与 `src/test/`（Java/Maven 惯例，第二层）；Python 配置 conftest.py、
  pytest.ini、tox.ini、noxfile.py；JS/TS runner 配置
  （playwright/vitest/jest/cypress/karma 常见文件名）；根目录文件名
  `test_*.py`、`*_test.py`、`*_test.go`（Go 惯例）、`*.test.*`、
  `*.spec.*`。测试只存在于其他更深层级（如 `packages/*/src/**/*.spec.ts`
  且无任何根级信号）时会误报缺失——该规则的视野是根目录、冻结目录名与
  `src/test`，不做递归内容扫描。文件存在不证明测试能通过。
- CI 识别 GitHub Actions（`.github/workflows/*.yml|yaml`）与 4 种根级
  配置（`.gitlab-ci.yml` 等）；其他 CI 系统（Jenkinsfile、circleci 目录）
  会误报缺失。
- CONTRIBUTING/SECURITY/CODE_OF_CONDUCT 认可根目录与 `.github/` 两个位置
  （GitHub 官方行为），COC 额外认可 `CONDUCT.md`（cobra 风格）。
- CHANGELOG 识别根目录 `CHANGELOG.md`、`HISTORY.md`、`CHANGES.md/.rst`、
  `NEWS.md/.rst`、`RELEASES.md` 与 `docs/releases.md`；仅依赖 GitHub
  Releases 页而不落文件的仓库会误报缺失（如 cobra）。
- 模板规则要求 `.github/ISSUE_TEMPLATE/` 内至少一个文件；空目录算缺失。

## README 结构规则（`readme.*`）

- 全部为启发式：报"未检测到"不等于"没有"。非常规措辞（如把安装说明写
  成"How do I run this thing?"）会漏报。
- `readme.no-h1`：识别 ATX 标题（`# `，行首至多 3 个空格）、setext 标题
  （文字行 + `===` 为 H1、+ `---` 为 H2）与 HTML `<h1>`。**注意**：标题
  下划线用 `---`（如 ripgrep）按 CommonMark 是 H2，此类仓库确实没有 H1，
  告警属实；logo/图片当标题（无任何 H1 形式）也会告警——对成熟项目信号
  偏弱，属已知的低信号项。行首 4 空格视为缩进代码块而非标题。
- `readme.install-not-detected`：在围栏外按子串匹配关键词（install、
  setup、requirements 等）；"setup" 可能匹配到无关句子（宽进方向，
  即可能漏报缺失而非误报）。围栏内的安装命令不算信号。
- `readme.usage-not-detected`：usage/example/demo 等关键词或任意围栏
  代码块都算信号；存在代码块不代表那是可运行的使用示例。
- `readme.oversized`：README 超过 2 MiB 时只分析前 2 MiB 并告警；
  被截断部分的标题/链接不在分析范围内。
- 非 UTF-8 编码的 README 按错误替换方式解码，非 ASCII 内容可能失真。

## 链接规则（`link.*`，范围仅 README）

- 支持子集：内联链接/图片（含标题）、完整与折叠引用式链接、引用定义、
  `<目标>` 角括号形式、URL 解码、反斜杠分隔符、GitHub 风格标题 slug
  （重复标题 `-1`/`-2`），标题来源含 ATX 与 setext；HTML `<h1-6>`/`<a>`
  的 `name`/`id` 属性也作为锚点目标（GitHub 行为，ripgrep FAQ 用此形式）。
- 不支持并会漏检：HTML `<a>`/`<img>` 标签、隐式引用（`[label]` 裸写）、
  标签内嵌套方括号、未加 `<>` 或 URL 编码的带空格目标
  （`[x](my file.md)` 会被整体忽略）、目标内未转义的平衡括号
  （`[x](a_(b).md)`）、缩进代码块内的示例链接、转义写法 `\[x](y)`。
- 未定义的引用式写法（`[x][undefined]`）按渲染器行为视为普通文本，
  不检查也不报缺失。
- 目标存在性按文件系统 `exists()` 判定：在大小写敏感文件系统上，
  `[x](readme.md)` 指向 `README.md` 会报缺失，Windows 上则通过——
  指向其他文件时同理，跨平台仓库建议使用与磁盘一致的大小写。
- 目录目标视为有效（与 GitHub 渲染一致）；目录存在不代表其中内容正确。
- 锚点检查仅对 `.md`/`.markdown` 目标文件执行，且跳过超过 2 MiB 的
  目标；PDF 等其他格式带的 fragment 不检查。slug 算法对 emoji、非
  拉丁字符的处理可能与 GitHub 在个别字符上有差异。
- 外部链接（`scheme://`、`mailto:`）只计数、永不发起请求；数量正确
  不代表这些链接可达。
- 纯锚点链接（`#section`）只对 README 自身标题校验；指向渲染后生成
  的锚点（如 GitHub 自动目录）可能报 info 级未匹配。

## 发布元数据规则（`meta.*`）

- `meta.pyproject.required-fields`：仅在 pyproject.toml 存在时适用；冻结的必填集为
  name、version、description、readme，以及 license 或 license-files 之一。列在
  `dynamic` 中的字段视为已声明，但**不验证**动态来源（如 `[tool.setuptools.dynamic]`）
  是否真的存在。
- 仅识别 PEP 621 的 `[project]` 表：使用 `[tool.poetry]` 等非 PEP 621 布局的
  项目会报"无 [project] 表"——这是真实的 PyPI 发布信号，但对暂不迁移的项目
  观感偏严。setup.py/setup.cfg-only 项目不做任何字段检查（解析 setup.py 需要
  执行代码，违反只读约束）。
- TOML/JSON 解析失败各报一条格式 finding，证据只含解析错误摘要（≤200 字符），
  不回显文件内容。
- `meta.packagejson.required-fields`：仅查根目录 package.json，不进入 monorepo
  的子包；`"private": true` 不豁免字段检查（存在性规则不做发布意图判断）。
- `meta.changelog.current-entry`：识别 CHANGELOG 内 ATX 与 setext 标题中
  的 "Unreleased" 或 `v?主.次[.修订]` 版本号（含 keep-a-changelog 的
  `[1.2.3]` 括号形式；ripgrep 的纯文本 setext 格式已支持）。文件位置变体
  同 `repo.changelog.missing` 的冻结清单。纯日期式 changelog 不识别；
  不含任何标题行的纯文本列表不识别。标题**包含**版本号即算命中（如
  "## Fixes backported to 1.2" 也算），方向为宽进。
- 邻域说明（2026-10-26 经 PyPI 核对）：pyroma 5.0.1 做语义更深的打包友好度
  评级，check-manifest 0.51 校验 sdist 文件完整性；本组规则保持零依赖、
  仅存在性检查，与其不互换也不重复其语义判断。

## 配置语义（`--config`）

- `rules.disable` 中的规则按"跳过"处理，不计入 passed/failed——CI 退出码语义
  随之变化（禁用一条 error 规则可能让原本失败的检查变为通过），配置文件属于
  版本控制内可审计的决策，建议与仓库一起提交。
- `ignore.paths` 使匹配路径对**所有**检查不可见：忽略 `README.md` 会触发
  `repo.readme.missing`，忽略 `pyproject.toml` 会跳过其字段检查——忽略即"等同
  不存在"，不是"豁免"。
- 忽略匹配作用于快照层（root、`.github`、`.github/workflows`、
  `.github/ISSUE_TEMPLATE`、`docs` 顶层文件名）；更深层级当前不进入任何
  规则的视野，配置深层路径无效果。
- 配置中不存在阈值与输出格式键：无评分，输出格式由 CLI 参数控制。

## 计数与退出语义

- 无 README 时，7 条 README 依赖规则（`readme.*`、`link.*`）跳过，
  不计入 passed/failed 规则数；`--strict` 的退出码只由已评估规则的
  finding 决定。
- 只产出 info 的规则按设计计入 passed；因此"passed"含义是"未发现
  error/warning 级问题"，不是"该方面无任何可改进项"。

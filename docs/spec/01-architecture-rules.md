# RepoReady 架构与检查规则

> 品牌 RepoReady；代码内部标识 `reporead`（发布名由维护者发布前决策）。定位与竞品依据见 `IMPLEMENTATION_READINESS_REVIEW.md`。

## 1. 目录

```text
src/reporead/
  __init__.py         # __version__ 单一来源
  __main__.py         # python -m reporead
  cli.py              # argparse CLI
  models.py           # finding/report 模型、summary 计数、退出码决策
  scanner.py          # root 校验与只读枚举
  rules/              # 存在性规则与引擎
    __init__.py        # CHECKS 顺序与 run_checks 引擎（不适用即跳过）
    registry.py        # 规则注册表（与 §2a 表一致）与 make_finding
    context.py         # ScanContext：root/.github/docs 顶层快照
    repository_files.py # essential files 存在性规则与 find_readme
    community_files.py  # community health 存在性规则
    readme_quality.py   # README 结构启发式规则
    markdown_links.py   # README 本地链接/图片/锚点/外链计数规则
    markdown_text.py    # 围栏过滤、行号迭代、大小上限读取
    release_metadata.py # pyproject/package.json 字段与 CHANGELOG 条目规则
  report_text.py      # text 渲染（无 ANSI、确定性）
  report_json.py      # JSON 渲染（schema 契约、确定性）
  config.py           # --config 支持；Phase 3 才加入
tests/
  fixtures/           # 静态 golden fixtures（golden_complete_repo / golden_empty_repo / 快照）
  fixture_builders.py # Phase 0 运行时 fixture 构建器
  test_cli.py
  test_models.py
  test_scanner.py
  test_output.py
  test_boundaries.py  # 不联网导入断言等边界测试
  test_rules.py       # 注册表、存在性规则与引擎
  test_readme_rules.py
  test_markdown_links.py
  test_markdown_text.py
  test_release_metadata.py
```

如果使用标准 `src/` 布局，pyproject 必须正确配置包发现；禁止同名顶级文件遮蔽包。

## 2. 规则类别

### Essential files

- README.md 或 README（大小写适配）。
- LICENSE / LICENSE.md / LICENSE.txt。
- `.gitignore`。
- 至少一个依赖/项目清单：`pyproject.toml`、`package.json`、`Cargo.toml`、`go.mod` 等常见 manifest。
- 测试目录或明确测试配置（不能仅凭文件名断言测试真的通过）。
- CI workflow（例如 `.github/workflows/*.yml`）。

### Community health

- CONTRIBUTING.md、CODE_OF_CONDUCT.md、SECURITY.md。
- CHANGELOG.md 或 `docs/releases.md` 作为可配置替代。
- `.github/ISSUE_TEMPLATE/`、`PULL_REQUEST_TEMPLATE.md`。

### README hygiene（MVP 仅检查 README）

- 包含项目标题（至少一个 H1）；
- 含安装/运行指引的关键词/章节之一；
- 含使用示例或最小命令。

这些只是在检查结构，不得把简单关键词存在说成文档质量充分；启发式结论一律写"未检测到"，不写绝对判断。

### Markdown links（Phase 2，MVP 范围仅 README）

- 本地相对链接与引用图片路径存在性；fenced code block 排除。
- 外部 `https://` 链接只列为未检查（info），不判断可达性。

### Release metadata（Phase 2.5）

- `pyproject.toml` / `package.json` 关键字段存在性；CHANGELOG 当前版本条目。
- 只查存在性与格式，不判断语义正确性，不承诺"包能正确发布"。

## 2a. 规则注册表（单一事实源）

所有可产出 finding 的规则必须先在此登记再实现；CLI、测试与文档不得使用未注册的 `rule_id`。`rule_id` 一经发布即冻结，后续变更必须在 CHANGELOG 中记录并说明迁移方式。测试必须断言注册表条目唯一。

| rule_id | 默认 severity | 类别 | Phase | 判定一句话 |
|---|---|---|---|---|
| `repo.readme.missing` | error | essential | 1 | 根目录无 README（大小写适配） |
| `repo.license.missing` | error | essential | 1 | 根目录无 LICENSE |
| `repo.manifest.missing` | error | essential | 1 | 无任何已知依赖/项目 manifest |
| `repo.gitignore.missing` | warning | essential | 1 | 无 `.gitignore` |
| `repo.tests.missing` | warning | essential | 1 | 无测试目录或测试配置 |
| `repo.ci.missing` | warning | essential | 1 | 无 CI workflow |
| `repo.contributing.missing` | warning | community | 1 | 无 CONTRIBUTING |
| `repo.security.missing` | warning | community | 1 | 无 SECURITY |
| `repo.coc.missing` | warning | community | 1 | 无 CODE_OF_CONDUCT |
| `repo.changelog.missing` | warning | community | 1 | 无 CHANGELOG |
| `repo.templates.issues.missing` | info | community | 1 | 无 Issue 模板 |
| `repo.templates.pr.missing` | info | community | 1 | 无 PR 模板 |
| `readme.no-h1` | warning | readme | 2 | 未检测到 H1 标题 |
| `readme.install-not-detected` | warning | readme | 2 | 未检测到安装/运行说明 |
| `readme.usage-not-detected` | warning | readme | 2 | 未检测到使用示例 |
| `readme.oversized` | warning | readme | 2 | README 超过 2 MiB 读取上限，仅分析前 2 MiB |
| `link.target.missing` | error | links | 2 | README 本地相对链接/图片目标不存在 |
| `link.anchor.not-found` | info | links | 2 | 锚点未匹配（提示级，不阻断） |
| `link.external-not-checked` | info | links | 2 | 外链离线未检查，仅列出 |
| `meta.pyproject.required-fields` | warning | metadata | 2.5 | pyproject 关键字段缺失 |
| `meta.packagejson.required-fields` | warning | metadata | 2.5 | package.json 关键字段缺失 |
| `meta.changelog.current-entry` | info | metadata | 2.5 | CHANGELOG 无 Unreleased/最近版本条目 |

**summary 计数语义**：规则产出至少一个 error 或 warning finding 即计为 failed；只产出 info（或无 finding）的已评估规则计为 passed；因不适用而跳过的规则不计入两者。`passed_rule_count = evaluated_rule_count - failed_rule_count`；出现负数为模型编程错误，必须抛错而不是静默钳制。

**severity 语义**：error 直接触发退出码 1；warning 仅在 `--strict` 下触发 1；info 永不触发退出码 1。

## 3. Path 与安全边界

- root resolve 后作为规则扫描边界；相对路径不得逃出 root；`Report.root` 记录解析后的绝对路径。
- 默认跳过目录（冻结清单）：`.git/`、`node_modules/`、`vendor/`、`dist/`、`build/`、`__pycache__/`、`.venv/`、`venv/`、`.tox/`、`.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/`。
- 目录 symlink 不跟随（`os.walk(followlinks=False)`）；文件 symlink 不在枚举期解引用，读取期（Phase 1 起）必须先 resolve 并确保目标仍在仓库根目录下。
- 文件读取加大小限制（README/Markdown 默认例如 2 MiB）；超出时报告 warning，不把整个文件读入内存。
- 权限错误应成为可读 finding，不让单个文件故障 crash 全部检查。
- 不执行仓库的任何脚本、构建配置或代码；只静态读取文本路径。
- 不联网，不调用 GitHub API，不需要 token。验证方式：导入期断言（测试内子进程导入包后检查 `sys.modules` 中无 `socket`/`http`/`urllib.request` 等网络模块）+ 代码评审确认只使用文件系统能力。该验证不宣称"运行期绝无网络行为"，README 与文档亦不得如此表述。

## 4. 退出码（冻结决策表）

| 情形 | 默认 | `--strict` |
|---|---|---|
| 无 error 且无 warning | 0 | 0 |
| 有 warning、无 error | 0 | 1 |
| 有 error | 1 | 1 |
| CLI 参数、配置、路径访问或输出写入错误 | 2 | 2 |

- `--output PATH` 写入失败（含父目录不存在、权限、磁盘错误）返回 2，stderr 给出目标路径与 OS 错误类别；不创建缺失的父目录。
- 退出码不因输出格式、终端颜色或 warning 顺序改变。
- `--version`、`--help` 返回 0。

## 5. Markdown link checker（MVP 范围：README）

- 默认仅检查 README 内的相对路径和同仓库锚点；不请求网络。扩展到其他 Markdown 属 `--config` 之后的候选项，MVP 不做。
- 处理 URL fragment、URL-encoded path、空格和 Windows separator。
- "fragment 检查"指 `path#fragment` 中 path 部分的文件存在性（可测；目标不存在记为 error 级 `link.target.missing`）；标题锚点匹配为 info 级 `link.anchor.not-found`，首版允许不覆盖全部 Markdown 标题插件规则，限制须写入 `docs/false-positives.md`。
- 忽略 fenced code block 中的示例 URL/路径，避免大量误报。

## 6. 配置文件（Phase 3）

采用 TOML。配置只能选择启用规则、阈值、忽略路径与输出格式，不接受可执行表达式/插件导入。未知字段报错；忽略模式不允许将 root 设为不受控的任意上级路径。`--config` 在配置能力测试完成后才加入 CLI。

## 7. 测试原则

- 对每条规则设计 pass/fail/edge fixtures；Phase 0 使用运行时构建器（`tests/fixture_builders.py`），Phase 1 起沉淀静态 golden fixtures。
- 使用临时目录和合成文件，不检查真实用户目录作为单元测试。
- 跨平台路径测试；测试大小写不敏感文件系统差异；symlink 测试在无权限平台显式跳过并在报告中记录。
- JSON 输出有 schema version、稳定排序和无终端色彩代码；text 与 JSON 渲染同输入字节级一致（重复渲染比对）。
- 渲染结果必须与 `report.schema.json` 的键集合做结构一致性断言（schema 为 `additionalProperties: false`）。
- 输出文件写入失败时返回 2 并给出具体路径与 OS 错误摘要。
- 模型与 schema 一致性、退出码决策表、summary 计数语义均有直接单元测试。

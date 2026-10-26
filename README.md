# RepoReady

[![ci](https://github.com/Aswellle/repoready/actions/workflows/ci.yml/badge.svg)](https://github.com/Aswellle/repoready/actions/workflows/ci.yml)

推送或发布前最后一道离线、只读的开源仓库就绪度检查：像 linter 一样用稳定的 `rule_id` 和证据说话，输出可执行的修复清单——**不打分**。

**设计承诺**

- **离线**：检查过程没有任何网络请求；不调 GitHub API，外链只计数、绝不请求可达性。
- **只读**：不执行目标仓库的任何代码，不修改、不上传目标内容；符号链接不跟随，路径全部做根目录包含校验。
- **证据链**：每条 finding 包含 `rule_id`、`severity`、`detail`、`evidence`（含行号）与可执行的 `suggestion`；severity 由规则注册表冻结，不会漂移。
- **确定性**：同一输入产生字节级相同的 text/JSON 输出，可直接在 CI 中断言。
- **零依赖**：核心仅用 Python 3.11+ 标准库，安装即用。

> **与近名项目无关**：GitHub 上已有 [kanuwrld/repoready](https://github.com/kanuwrld/repoready)（Python 加权评分工具）、[OpenSource-Communities/RepoReady](https://github.com/OpenSource-Communities/RepoReady)（走 GitHub API 的联网评估工具，占用 npm 包名 `repoready`）与 [shidesheng0218/repo-ready](https://github.com/shidesheng0218/repo-ready)（AI 编码代理就绪度检查器）。它们都以 0–100 分为核心叙事；本项目与它们没有任何关系，且刻意不评分，专做它们都不做的 **README 内部链接完整性**与**发布元数据一致性**检查。

## 检查什么

22 条规则、五个类别。注册表（rule_id、severity、理由）是唯一事实源，完整定义见 [docs/spec/01-architecture-rules.md](docs/spec/01-architecture-rules.md)（与代码的一致性由测试双向锁定）。

### 必备文件（essential）

| rule_id | severity | 检查内容 |
| --- | --- | --- |
| `repo.readme.missing` | error | 根目录无 README（大小写不敏感；认可 `.md`/`.rst`/`.txt`/`.markdown` 变体） |
| `repo.license.missing` | error | 根目录无 LICENSE（认可 `LICENSE.md/.txt`、`LICENSE-<后缀>`、`licence-<后缀>`、`COPYING*`、`UNLICENSE*`） |
| `repo.manifest.missing` | error | 无依赖清单，12 种：`pyproject.toml`、`setup.py`、`setup.cfg`、`requirements.txt`、`package.json`、`Cargo.toml`、`go.mod`、`pom.xml`、`build.gradle(.kts)`、`Gemfile`、`composer.json` |
| `repo.gitignore.missing` | warning | 无 `.gitignore` |
| `repo.tests.missing` | warning | 无测试信号：目录 `tests`/`test`/`e2e`/`__tests__`、`src/test`、多模块 `<模块>/src/test`；配置 `conftest.py`、`pytest.ini`、`tox.ini`、`noxfile.py` 与 JS/TS runner 配置；文件 `test_*.py`、`*_test.go`、`*.test.*`、`*.spec.*` |
| `repo.ci.missing` | warning | 无 CI workflow：`.github/workflows/*.yml`、`.gitlab-ci.yml`、`azure-pipelines.yml`、`.travis.yml`、`.drone.yml` |

### 社区文件（community）

| rule_id | severity | 检查内容 |
| --- | --- | --- |
| `repo.contributing.missing` | warning | 根目录或 `.github/` 无 CONTRIBUTING |
| `repo.security.missing` | warning | 根目录或 `.github/` 无 SECURITY |
| `repo.coc.missing` | warning | 根目录或 `.github/` 无 CODE_OF_CONDUCT / CONDUCT |
| `repo.changelog.missing` | warning | 无 CHANGELOG：`CHANGELOG.md`、`HISTORY.md`、`CHANGES.md(.rst)`、`NEWS.md(.rst)`、`RELEASES.md`、`docs/releases.md` |
| `repo.templates.issues.missing` | info | `.github/` 下无 Issue 模板 |
| `repo.templates.pr.missing` | info | `.github/` 下无 PR 模板 |

### README 质量（readme）

| rule_id | severity | 检查内容 |
| --- | --- | --- |
| `readme.no-h1` | warning | 未检测到 H1 标题（ATX `#` 与 setext `===` 均认可） |
| `readme.install-not-detected` | warning | 未检测到安装/运行说明信号（启发式） |
| `readme.usage-not-detected` | warning | 未检测到使用示例信号（启发式） |
| `readme.oversized` | warning | README 超过 2 MiB 读取上限，按截断内容分析并告警 |

### 链接完整性（links）

| rule_id | severity | 检查内容 |
| --- | --- | --- |
| `link.target.missing` | error | README 本地链接/图片目标不存在——离线校验：URL 解码、排除围栏代码块、引用式与折叠式链接、路径包含校验 |
| `link.anchor.not-found` | info | 本地锚点未找到：GitHub 风格 slug、重复标题 `-1/-2` 编号、HTML `name`/`id` 属性 |
| `link.external-not-checked` | info | 外链仅列出并计数，绝不请求（离线承诺） |

### 发布元数据（metadata）

| rule_id | severity | 检查内容 |
| --- | --- | --- |
| `meta.pyproject.required-fields` | warning | `pyproject.toml [project]` 缺 `name`/`version`/`description`/`readme` 或 `license`/`license-files`（`dynamic` 声明计入）；解析失败单独报告 |
| `meta.packagejson.required-fields` | warning | `package.json` 缺 `name`/`version`/`description`/`license`；JSON 解析失败单独报告 |
| `meta.changelog.current-entry` | info | CHANGELOG 无 Unreleased 或版本号条目 |

## 安装

要求 Python 3.11+，零运行时依赖。

```bash
pip install git+https://github.com/Aswellle/repoready
```

从 git 直装已在干净虚拟环境中实测；PyPI 包后续另行发布，**发布前请勿假设 `pip install repoready` 可用**。

开发方式安装：

```bash
git clone https://github.com/Aswellle/repoready
cd repoready
pip install -e .
```

不安装也可用模块入口 `python -m repoready`。

## 快速开始

对任意仓库做检查（只读，不修改目标）：

```console
$ repoready check path/to/repo
repoready 0.1.0 - repository readiness check
root: path/to/repo
rules evaluated: 12 (2 passed, 10 failed)
findings: 3 error(s), 7 warning(s), 2 info
findings:
[error] repo.license.missing: LICENSE file not found
  path: LICENSE
  detail: No LICENSE file was found at the repository root; without a license nobody can legally use or contribute to the code.
  evidence: Checked the repository root for LICENSE, LICENSE.md/.txt, LICENSE-<suffix>, COPYING*/UNLICENSE* files (case-insensitive); none found.
  suggestion: Add a LICENSE file with the license chosen by the project maintainers.
...（后续 findings 截取）
```

常用参数（完整列表见 `repoready check --help`）：

| 参数 | 作用 |
| --- | --- |
| `--strict` | warning 也算检查失败（退出码 1），适合发布前门禁 |
| `--format json` | 机器可读 JSON 输出 |
| `--output PATH` | 报告写入文件而非 stdout |
| `--config PATH` | TOML 配置文件（见下） |

## 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 通过：无 error（`--strict` 下也无 warning） |
| `1` | 未通过：存在 error（或 `--strict` 下存在 warning） |
| `2` | 工具自身错误：CLI 参数、配置、路径或输出写入失败 |

## 配置

可选 TOML 文件，仅两个键：

```toml
[rules]
disable = ["repo.templates.issues.missing", "repo.templates.pr.missing"]

[ignore]
paths = ["drafts/", "notes/*.md"]
```

```bash
repoready check . --config repoready.toml
```

`ignore` 命中的路径对一切检查不可见（等同文件不存在）。未知键、未注册的 rule_id、绝对路径或越界 `..` 都会以退出码 2 报错，不会静默忽略。

## 在 CI 中使用

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
- name: Install repoready
  run: pip install git+https://github.com/Aswellle/repoready
- name: Repository readiness check
  run: repoready check . --strict
```

完整可复制 workflow 见 [docs/examples/github-actions.yml](docs/examples/github-actions.yml)。首次接入建议先不加 `--strict` 观察基线，再决定哪些规则在 `[rules].disable` 中关闭。

## JSON 输出

`--format json` 输出的每条 finding：

```json
{
  "rule_id": "repo.changelog.missing",
  "severity": "warning",
  "title": "CHANGELOG not found",
  "detail": "No changelog file was found; release changes are not traceable.",
  "path": "CHANGELOG.md",
  "evidence": "Checked the repository root for CHANGELOG.md, HISTORY.md, CHANGES.md/.rst, NEWS.md/.rst, RELEASES.md (case-insensitive) and docs/releases.md; none found.",
  "suggestion": "Add a CHANGELOG.md (or docs/releases.md) and record user-visible changes per release."
}
```

顶层为 `schema_version`（当前 `1.0`）、`root`、`summary`、`findings`，字段契约见 [docs/spec/report.schema.json](docs/spec/report.schema.json)。输出按字段排序，同一输入字节级可复现。

## 明确不做

不评分、不给仓库排名；不联网（不调 GitHub API、不检查外链可达性）；不执行目标仓库的任何代码；不自动修复或生成文件；不做 AI/agent 叙事规则。**文件存在只代表形式检查通过，不等于代码质量或安全。**已知的边界与误报场景全部记录在 [docs/false-positives.md](docs/false-positives.md)。

## 开发

```bash
pip install -e .
python -m unittest discover -s tests   # 216 项测试
python -m build                        # 构建验证
```

CI 矩阵：Ubuntu/Windows/macOS × Python 3.11–3.14。新增规则必须先登记 [规则注册表](docs/spec/01-architecture-rules.md) 并补齐正反测试；流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 安全

安全漏洞请勿公开提交 issue，按 [SECURITY.md](SECURITY.md) 中的联系方式私下报告。

## License

[MIT](LICENSE)。

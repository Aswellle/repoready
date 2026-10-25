# RepoReady

推送前最后一道离线、只读的仓库就绪度检查：像 linter 一样用稳定 rule_id 和证据说话，输出可执行的修复清单——**不打分**。

> **与近名项目的区别**：GitHub 上已有 [kanuwrld/repoready](https://github.com/kanuwrld/repoready)（Python 加权评分工具）、[OpenSource-Communities/RepoReady](https://github.com/OpenSource-Communities/RepoReady)（走 GitHub API 的联网评估工具，npm 包 `repoready`）与 [shidesheng0218/repo-ready](https://github.com/shidesheng0218/repo-ready)（AI 编码代理就绪度检查器）。它们都以 0–100 分为核心叙事；本项目与它们**无任何关系**，且刻意不评分：只输出带 rule_id、证据和修复建议的结构化结果，专做它们都不做的 README 内部链接完整性与发布元数据一致性检查。

## 它检查什么

22 条规则，三大类（完整注册表见 [docs/spec/01-architecture-rules.md](docs/spec/01-architecture-rules.md) §2a）：

- **必备文件**：README、LICENSE、.gitignore、依赖清单（pyproject.toml/package.json 等 12 种）、测试目录或配置、CI workflow。
- **README 质量**：H1/安装/使用信号（启发式）；**本地相对链接与图片存在性**（离线、排除围栏代码块、URL 解码、GitHub 风格锚点）；外链只计数、绝不请求。
- **发布元数据**：pyproject.toml/package.json 必填字段（name、version、description、license 等）；CHANGELOG 是否有 Unreleased/版本条目。

每条 finding 包含 `rule_id`、`severity`（error/warning/info）、`title`、`detail`、`path`、`evidence`（含行号）、`suggestion`。文件存在只代表形式检查通过，不等于代码质量或安全——已知的边界与误报场景全部记录在 [docs/false-positives.md](docs/false-positives.md)。

## 安装与使用

**从 git 安装**（无需 PyPI，已实测）：

```bash
pip install git+https://github.com/Aswellle/repoready
```

或克隆后可编辑安装（适合开发）：

```bash
git clone https://github.com/Aswellle/repoready
cd repoready
pip install -e .
```

无需安装时可用模块入口：`python -m repoready`。PyPI 包（`repoready`）将另行发布。

对任意仓库做检查（只读，不修改目标）：

```console
$ repoready check path/to/repo --strict
rules evaluated: 21 (14 passed, 7 failed)
findings: 1 error(s), 6 warning(s), 3 info
findings:
[error] repo.license.missing: LICENSE file not found
  path: LICENSE
  detail: No LICENSE file was found at the repository root; without a
      license nobody can legally use or contribute to the code.
  evidence: Checked the repository root for LICENSE, LICENSE.md or
      LICENSE.txt (case-insensitive); none found.
  suggestion: Add a LICENSE file with the license chosen by the project
      maintainers.
...
```

JSON 输出机器可读、字节级可复现，可直接被 CI 断言：

```bash
repoready check . --format json --output report.json
```

**退出码**：`0` 无 error（且 `--strict` 下无 warning）；`1` 存在 error（或 strict 下存在 warning）；`2` CLI 参数、配置、路径或输出写入错误。

**配置**（可选，TOML）：

```toml
[rules]
disable = ["repo.templates.issues.missing", "repo.templates.pr.missing"]

[ignore]
paths = ["drafts/", "notes/*.md"]
```

```bash
repoready check . --config repoready.toml
```

## 明确不做

不评分、不联网（不调 GitHub API、不检查外链可达性）、不执行目标仓库的任何代码、不自动修复或生成文件、不做 AI/agent 叙事规则。离线优先：检查过程没有任何网络请求。

## 开发

```bash
pip install -e .
python -m unittest discover -s tests -v   # 193 项测试
python -m build                            # 构建验证
```

零运行时依赖（Python 3.11+ 标准库）；`build`/`setuptools` 属构建依赖。新增规则必须先登记 [规则注册表](docs/spec/01-architecture-rules.md) 并补齐正反测试，见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License

MIT —— 见 [LICENSE](LICENSE)（2026-10-26 由维护者确认）。

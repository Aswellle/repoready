# RepoReady 实施计划与验收

> 品牌 RepoReady；代码内部标识 `reporead`。差异化定位与修订决策见 `IMPLEMENTATION_READINESS_REVIEW.md`；实施时先读该文件。

## Phase 0 — 工程骨架与契约冻结

- 建立 `pyproject.toml`（PEP 517、setuptools、版本单一来源 `reporead.__version__`）、src 布局包、`__main__.py`、`argparse` CLI。
- 首版 CLI 面冻结：`check [PATH]`、`--format text|json`、`--strict`、`--output PATH`、`--help`、`--version`。
- 定义 finding/report 数据模型（`models.py`），并与 `report.schema.json` 做双向结构一致性测试；text/JSON 渲染确定性（同输入字节级一致）。
- 冻结退出码决策表（`01-architecture-rules.md` §4）并单元测试。
- `scanner.py`：root 解析校验、只读枚举、默认跳过目录、目录 symlink 不跟随；"不执行目标代码"有负向测试。
- fixture 构建器：空目录、缺 LICENSE、不可读文件、无效 root、symlink 逃逸、超大 Markdown、Windows 路径（空格/中文/括号）。

验收：`pip install -e .`（或 `PYTHONPATH=src`）后 `python -m unittest discover -s tests -v` 全部通过；CLI 参数错误产生稳定退出码 2。

## Phase 1 — 规则模型与 essential files

- 实现 `rules/` 中的存在性规则并接入 §2a 注册表；finding/severity/report 模型沿用 Phase 0 冻结结果。
- 检查 README、LICENSE、`.gitignore`、manifest、测试、CI 文件存在性。
- 沉淀静态 golden fixtures；结果稳定排序；输出 text + JSON。

验收：fixtures 里每条规则有通过与失败案例；JSON 结构稳定；`rule_id` 注册表唯一性测试通过。

## Phase 2 — README 与本地链接（范围冻结为 README）

- H1/安装/运行/使用示例结构提示（启发式，"未检测到"措辞）。
- README 内 Markdown 本地相对链接、图片路径检查；排除 fenced code block 的明显误报。
- "fragment 检查"指 path 部分存在性；标题锚点匹配为 info 级，覆盖限制写入 `docs/false-positives.md`。

验收：URL 编码、空格、fragment、Windows 路径、符号链接和不存在文件测试通过。

## Phase 2.5 — 发布元数据一致性

- `meta.pyproject.required-fields`、`meta.packagejson.required-fields`、`meta.changelog.current-entry` 三条规则（severity 默认值见注册表）。
- 只查存在性与格式；实现前先核对 pyroma/check-manifest 等邻域工具的覆盖面，避免重造与误报。

验收：pyproject/package.json/CHANGELOG 的正反例 fixtures 全部通过；误报边界记录在案。

## Phase 3 — 配置与 CI 完整性

- `--config`（只有 TOML schema、未知键错误、路径忽略规则测试完成后才加入）。
- GitHub Action 示例和可复制 YAML。
- 加 CI workflow，验证测试、`compileall`、安装包构建。

验收：exit code 0/1/2 可在 shell/CI 中确定使用；`--config` 未知字段返回 2。

## Phase 4 — 文档和发布

- README（含与近名项目的消歧说明）、LICENSE、CONTRIBUTING、SECURITY、CODE_OF_CONDUCT、CHANGELOG。
- 安装/使用演示、fixture 说明、限制列表（`docs/false-positives.md`）。
- 仓库命名与包名检查（重新核验 PyPI/npm/商标）后再发布；发布动作由维护者授权。

## 验收清单

- [ ] 只读静态检查，不执行目标仓库代码。
- [ ] 无 runtime dependency；标准库 CLI 能运行。
- [ ] Path traversal / symlink 不会使扫描逃出仓库 root。
- [ ] 大文件有上限；权限错误不崩溃。
- [ ] Markdown link check 不联网；"不联网"有导入期断言验证（不宣称"运行期绝无网络"）。
- [ ] JSON 包含 schema version、稳定 findings、明确 path 和 remediation；同输入两次运行字节级一致。
- [ ] 规则注册表存在且唯一性有测试；`report-example.json` 与 schema 及自身 summary 自洽。
- [ ] exit codes documented and tested（决策表全覆盖）。
- [ ] 误报场景与规则边界写在 `docs/false-positives.md`。
- [ ] 不把"文件存在"解释成"代码质量/安全已保证"。

## 首版范围冻结

不加 AI/agent 叙事、不访问 GitHub API、不联网、不自动写入文件、不做远端仪表盘、**不实现评分与 `--min-score`**（未来候选，需维护者重新决策）。任何扩展都应在 MVP 发布后基于 issue/使用反馈设计。

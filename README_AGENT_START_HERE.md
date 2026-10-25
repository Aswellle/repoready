# RepoReady Agent 启动包

这是一个**独立项目实施包**。品牌名与发布名 **RepoReady**（2026-10-26 确定）：包名与 CLI 命令为 `repoready`，发布前重查占用。本目录已是独立 Git 仓库（main 分支），可直接在此实施。

## 目录契约

- `docs/AI_AGENT_WORKING_RULES.md`：通用代理工作协议。
- `docs/spec/00-product-scope.md`：产品需求与差异化定位。
- `docs/spec/01-architecture-rules.md`：架构、规则注册表与退出码决策表。
- `docs/spec/02-implementation-and-acceptance.md`：阶段与验收。
- `docs/spec/03-agent-master-prompt.md`：可直接交给编码代理的总控提示词。
- `docs/spec/IMPLEMENTATION_READINESS_AUDIT.md`：收敛首版歧义的实施默认决策。
- `docs/spec/IMPLEMENTATION_READINESS_REVIEW.md`：竞品差异审计与已审定定位（实施前必读）。
- `docs/spec/report.schema.json`：机器可读 JSON 报告契约。
- `docs/spec/report-example.json`：与 schema 及自身 summary 自洽的示例报告。

## 当前状态（2026-10-26）

Phase 0–4 已全部实施并通过验收，v0.1.0 已发布（tag 与 GitHub Release），CI 在 ubuntu/macos/windows × Python 3.11–3.14 上全绿。后续工作以 issue/使用反馈驱动，不再按阶段推进。

## 给 Agent 的操作约定

1. 确认 `git status --short --branch`，检查未提交修改。
2. 遵守 `docs/AI_AGENT_WORKING_RULES.md`；改动前读 CONTRIBUTING.md 的验证门槛与新增规则六步清单。
3. 任何新规则先登记 `docs/spec/01-architecture-rules.md` §2a 注册表；spec 文档是设计记录，改动须与代码同步。
4. 每次改动保持测试全绿并如实报告实际结果；不引入网络、评分或目标代码执行。
5. 不授予自动发布 PyPI、推送 release 的权限；外部动作须由维护者逐次授权。

## 目标实现结构

```text
README.md
LICENSE
pyproject.toml
src/repoready/      # 包名与 CLI 命令 repoready（发布名决策 2026-10-26）
tests/
docs/AI_AGENT_WORKING_RULES.md
docs/spec/
```

## 范围纪律

首版只做静态、只读、可解释的仓库就绪度检查。不得执行目标仓库代码，不联网检查外链，不把文件存在等同于代码质量或安全性保证，不实现评分。

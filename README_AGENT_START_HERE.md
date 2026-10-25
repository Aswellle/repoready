# RepoReady Agent 启动包

这是一个**独立项目实施包**。品牌名 **RepoReady**（2026-10-26 确定）；代码与本地开发使用内部标识 `reporead`，发布名由维护者发布前决策。本目录已是独立 Git 仓库（main 分支），可直接在此实施。

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

## 推荐操作

1. 确认 `git status --short --branch`，检查未提交修改。
2. 先阅读 `docs/spec/IMPLEMENTATION_READINESS_REVIEW.md`，再读其余 spec 文档。
3. 把 `docs/spec/03-agent-master-prompt.md` 的全部内容交给 Codex / Claude Code。
4. 要求 Agent 每次只执行一个 Phase；Phase 0 完成后根据验收报告决定是否继续。
5. 不授予自动创建远端仓库、发布包或推送 release 的权限。

## 目标实现结构

```text
README.md
LICENSE
pyproject.toml
src/reporead/      # reporead 为内部开发标识
tests/
docs/AI_AGENT_WORKING_RULES.md
docs/spec/
```

## 范围纪律

首版只做静态、只读、可解释的仓库就绪度检查。不得执行目标仓库代码，不联网检查外链，不把文件存在等同于代码质量或安全性保证，不实现评分。

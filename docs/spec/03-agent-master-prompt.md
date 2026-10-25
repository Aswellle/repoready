# RepoReady Agent 总控提示词

实现本文档定义的 RepoReady 轻量开源仓库就绪度检查工具（代码内部标识 `reporead`）。优先做到只读、可解释、零运行时依赖、可复现，不把项目扩展成 AI 审计 SaaS。

## 开始前

1. 检查当前目录、Git 状态和未提交修改。
2. 阅读 `docs/spec/00-product-scope.md`、`docs/spec/01-architecture-rules.md`、`docs/spec/02-implementation-and-acceptance.md`、`docs/spec/IMPLEMENTATION_READINESS_AUDIT.md`，并遵守 `docs/AI_AGENT_WORKING_RULES.md`。
3. **先阅读 `docs/spec/IMPLEMENTATION_READINESS_REVIEW.md`**（差异化定位、修订后 MVP 范围、文档决策），再按其冻结结论实施。
4. 查看现有文件；不得覆盖用户未提交修改。若已有实现，先做差距分析而非重建。
5. 给出简短现状报告、文件改动计划、风险和验证命令，然后继续执行第一阶段。

## 实施约束

- Python 3.11+，核心仅使用标准库。
- 目录扫描范围不得超出用户给定仓库根目录；默认不跟随符号链接，不联网，不执行任何被检查代码。
- 规则模型和 CLI 输出分离；文本与 JSON 共享同一 Report 模型。
- Exit code 0/1/2 按架构文档 §4 决策表执行，并由测试锁定。
- Markdown 链接检查只看 README 内的本地相对链接，外链不联网。
- 规则需要可解释的证据和修复建议；不要用简单关键词冒充完整质量审查。
- **不得实现评分、`--min-score` 或未在 `01-architecture-rules.md` §2a 注册的 rule_id。**
- 做完每个 Phase 必须运行测试并报告实际结果。

## 最终报告

列出完成规则、文件路径、实际命令与结果、未覆盖检查、已知误报和下一阶段建议。不得声称仓库“安全”或“质量优秀”；只报告被具体规则检查过的内容。

现在先审计工作区，再按 `docs/spec/IMPLEMENTATION_READINESS_AUDIT.md` 中锁定的默认决策开始 Phase 0。先完成 Phase 0 与 Phase 1；每阶段通过验收后再进入下一阶段。

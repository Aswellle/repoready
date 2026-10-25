---
name: Feature request
about: 新规则或新能力建议
labels: enhancement
---

**要解决的问题**：什么场景下现有 22 条规则不够用？

**建议方案**：期望的检查行为与输出形态

**规则归属**：建议的 rule_id、severity（error/warning/info）与类别；新规则必须先登记
`docs/spec/01-architecture-rules.md` §2a 注册表（见 CONTRIBUTING.md 的六步清单）。

**离线约束确认**：该规则是否只依赖本地文件？不联网、不执行目标代码是硬边界。

**误报风险**：哪些合法仓库形态会被误判？计划如何写入 `docs/false-positives.md`？

**替代方案**：

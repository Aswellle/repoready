# 贡献指南

## 开发环境

```bash
python -m venv .venv
.venv/Scripts/pip install -e .        # Windows；POSIX 为 .venv/bin/pip
.venv/Scripts/python -m unittest discover -s tests -v
```

要求 Python 3.11+。零运行时依赖是硬约束：核心代码只允许标准库；`build`/`setuptools` 仅作为构建/发布依赖。

## 验证门槛

每个改动提交前必须全绿：

1. `python -m unittest discover -s tests -v`
2. `python -m compileall -q src tests`
3. `python -m build`（改动打包元数据时）

CI（`.github/workflows/ci.yml`）在三个操作系统 × 两个 Python 版本上运行同一组命令。

## 如何新增一条规则

1. 先在 `docs/spec/01-architecture-rules.md` §2a 注册表加行（rule_id、默认 severity、类别、一句话判定），并同步 `src/repoready/rules/registry.py` 的 `REGISTRY`——测试会强制两处一致。
2. 在对应 `rules/` 模块实现检查函数：只读、可解释，返回 `list[Finding]`（不适用时返回 `None`），通过 `make_finding()` 创建 finding 以钉死 severity。
3. 在 `src/repoready/rules/__init__.py` 的 `RULE_CHECKS` 登记 rule_id → 函数映射。
4. 补测试：每条规则至少一个通过案例、一个失败案例；边界与误报场景写进用例。
5. 有意改变输出文案时，重新生成 `tests/fixtures/golden_empty_report.json` 快照并说明理由。
6. 新发现的误报/漏报边界写入 `docs/false-positives.md`。

## 约定

- 输出文案用"未检测到（not detected）"措辞，禁止把启发式结论写成绝对判断。
- 不引入评分、权重或网络请求；不执行目标仓库代码。约束依据见 `docs/spec/` 各文档。
- 提交信息只描述改动本身；一次提交一个自洽改动，保持测试全绿。

## 报告问题

提交 issue 时请附：`repoready --version`、完整命令行、目标仓库的最小复现片段（可合成，不要附敏感内容）、期望与实际输出。误报类问题请注明目标文件系统的平台与大小写行为。

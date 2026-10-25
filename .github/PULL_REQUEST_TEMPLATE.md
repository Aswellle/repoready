# Pull Request

## 改动说明

（一段话说清改了什么、为什么）

## 验证

- [ ] `python -m unittest discover -s tests -v` 全绿
- [ ] `python -m compileall -q src tests` 通过
- [ ] 改动打包元数据时：`python -m build` 成功

## 规则改动（如适用）

- [ ] 规则已登记 §2a 注册表与 `RULE_CHECKS` 映射
- [ ] 每条规则有通过与失败测试
- [ ] 有意改变输出文案时已更新 `tests/fixtures/golden_empty_report.json` 快照
- [ ] 误报/漏报边界已写入 `docs/false-positives.md`

## 边界确认

- [ ] 未引入运行时依赖、网络请求、评分或目标代码执行
- [ ] 输出保持确定性（同输入字节级一致）

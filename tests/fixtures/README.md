# fixtures/

静态 golden fixtures 将从 Phase 1 起沉淀在这里（每条规则的 pass/fail/edge 目录）。

Phase 0 的 fixture 由 `tests/fixture_builders.py` 在每个测试的临时目录中运行时构建，
不使用本目录，也不检查真实用户目录（`docs/spec/01-architecture-rules.md` §7）。

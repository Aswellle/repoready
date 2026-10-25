# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 约定；
尚未发布任何版本，以下为 Unreleased 条目。发布版本号与日期在发布决策时确定。

## Unreleased

### Changed

- 发布名决策落地：包名、import 路径与 CLI 命令由内部标识 `reporead` 统一更名为 `repoready`（维护者决策，2026-10-26）；npm 包因名称被占用而明确不发布，README 保留与近名项目的消歧说明。
- 许可证确认为 MIT 并添加 LICENSE；pyproject 声明 license 与 readme 字段；SECURITY.md 配置公开联系邮箱。

### Added

- 只读、离线的仓库就绪度检查引擎：22 条规则注册表（rule_id/severity/类别单一事实源，与架构文档 §2a 表一致性由测试锁定），按适用性自动跳过（不计入 passed/failed）。
- 必备文件存在性检查：README、LICENSE、.gitignore、依赖清单（12 种生态文件名）、测试目录或配置（Python 与 JS/TS runner 信号）、CI workflow、CONTRIBUTING/SECURITY/CODE_OF_CONDUCT/CHANGELOG、Issue/PR 模板。
- README 结构启发式：H1、安装/使用信号、超大文件上限（2 MiB 截断分析并告警）。
- README 内部链接与图片完整性检查（离线）：本地目标存在性（error，含行号证据）、GitHub 风格锚点匹配（info，支持重复标题编号）、外链计数（info，绝不请求）；支持引用式/折叠式链接、URL 解码、反斜杠分隔符、围栏代码块排除。
- 发布元数据一致性：pyproject.toml/package.json 必填字段（含 dynamic 与 license-files 备选）、CHANGELOG 版本条目；TOML/JSON 解析失败单独报告。
- CLI：`check [PATH]`、`--format text|json`、`--strict`、`--output PATH`、`--config PATH`、`--version`；冻结退出码决策表（0/1/2）。
- TOML 配置：`[rules].disable` 与 `[ignore].paths`；未知键、未注册 rule_id、绝对或越界路径返回退出码 2。
- 确定性输出：text/JSON 同输入字节级可复现，JSON 契约 schema_version 1.0（`docs/spec/report.schema.json`）。
- 测试与 CI：193 项单元测试；三平台 × 两 Python 版本矩阵 workflow（字节编译、测试、构建验证）；golden fixtures 与空仓库报告快照。
- 文档：规则误报边界清单（`docs/false-positives.md`）、可复制 GitHub Action 示例、规格文档包。

### Security

- 路径边界：目录符号链接不跟随，链接目标与 README 本体均做 root 包含校验；文件读取有大小上限；解析错误降级为 finding 而非崩溃。

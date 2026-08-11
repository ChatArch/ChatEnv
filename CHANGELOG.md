# 更新日志

本项目按版本记录对用户可见的 CLI、运行时和发布流程变更。

## 0.2.4 - 2026-08-11

- 新增顶层 `chatenv --tree`，从 Click 注册命令树生成当前命令面，包含 `--help`、`--version`、`--tree`、`--home` 和所有已注册命令的一行用途说明。
- 为 `--tree` 增加 CLI 合约测试，锁住 `init/new/paste/use/list/status/cat/get/set/save/delete/test` 等真实命令面，并确保没有模板 `hello` 泄漏。
- 将发布 workflow 从 Twine secret 上传迁移为 PyPI Trusted Publisher / GitHub OIDC；该项目的 PyPI Publisher 使用 `(Any)` environment，因此 workflow 不设置 GitHub environment。
- 收紧 MkDocs docs extras 上界，并补充 package URLs 的文档/仓库元数据。

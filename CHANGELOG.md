# 更新日志

本项目按版本记录对用户可见的 CLI、运行时和发布流程变更。

## 0.2.6 - 2026-08-11

- 收紧 runtime token-store profile 校验：拒绝空值、`.` / `..`、路径分隔符、前后空白和会别名到其他文件名的 profile，避免错误读取或清理其他 profile 的 token/session state。

## 0.2.5 - 2026-08-11

- 新增通用 runtime token-store API：`chatenv.TokenStore` / `chatenv.tokens.TokenStore`，按 `tokens/<Service>/<profile>.json` 管理动态 token/session JSON。
- 新增 `chatenv token refresh|status|list|clear` 通用 CLI；CLI 只输出 token 文件、profile、类型、时间戳和调用方传入的 safe summary，不输出 raw token/cookie/CSRF values。
- 新增 `ChatArchPaths.tokens_dir`，让 env profile 与 token profile 在同一 ChatArch home 下保持一一对应。

## 0.2.4 - 2026-08-11

- 新增顶层 `chatenv --tree`，从 Click 注册命令树生成当前命令面，包含 `--help`、`--version`、`--tree`、`--home` 和所有已注册命令的一行用途说明。
- 为 `--tree` 增加 CLI 合约测试，锁住 `init/new/paste/use/list/status/cat/get/set/save/delete/test` 等真实命令面，并确保没有模板 `hello` 泄漏。
- 将发布 workflow 从 Twine secret 上传迁移为 PyPI Trusted Publisher / GitHub OIDC；该项目的 PyPI Publisher 使用 `(Any)` environment，因此 workflow 不设置 GitHub environment。
- 收紧 MkDocs docs extras 上界，并补充 package URLs 的文档/仓库元数据。

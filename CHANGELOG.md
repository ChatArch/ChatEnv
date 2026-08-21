# 更新日志

本项目按版本记录对用户可见的 CLI、运行时和发布流程变更。

## 0.2.9 - 2026-08-21

- 放宽 ChatStyle runtime 依赖到 `chatstyle>=0.2.0,<0.3.0`，让 ChatDNS 和其他下游包可以使用 ChatStyle 0.2.0 的共享 Click tree renderer。

## 0.2.8 - 2026-08-12

- 将文档站点迁移到 ChatArch docs custom domain：`https://arch.gh.wzhecnu.cn/ChatEnv/`，并补齐 suffix-mode i18n 英文页面。
- 增加 MkDocs Material emoji renderer baseline 和生成站点 literal `:material-` gate。
- 强化 CI 为 Linux Python 3.10/3.11/3.12 matrix，并增加 installed `chatenv --version` / `chatenv --tree` smoke。
- 强化 PyPI Trusted Publishing workflow：tag 必须匹配包版本，release commit 必须是 `origin/main` ancestor，且使用 GitHub OIDC 发布。
- README / docs 同步真实 `chatenv --tree`，并移除旧 GitHub Pages 域名入口。

## 0.2.7 - 2026-08-11

- 新增 `chatenv.token_refreshers` provider hook：服务包可通过 `chatenv.token_refreshers` entry point 注册 refresh 函数，由 `chatenv token refresh SERVICE PROFILE` 调用并把返回的 opaque runtime values 写入 token-store。
- 将手工 JSON 写入从 `token refresh` 拆出为显式 `chatenv token import`，避免把 token-store 误用成第二个手工维护 secret/env 文件；`refresh` 现在表示由服务登录/刷新逻辑自动生成或更新 runtime token。
- `TokenRefreshResult` 暴露给 leaf package 作为标准返回对象；ChatEnv 仍只负责路径、原子写入、profile 校验和 safe metadata，不解释业务 token 语义。

## 0.2.6 - 2026-08-11

- 收紧 runtime token-store profile 校验：拒绝空值、`.` / `..`、路径分隔符、前后空白和会别名到其他文件名的 profile，避免错误读取或清理其他 profile 的 token/session state。

## 0.2.5 - 2026-08-11

- 新增通用 runtime token-store API：`chatenv.TokenStore` / `chatenv.tokens.TokenStore`，按 `tokens/<Service>/<profile>.json` 管理动态 token/session JSON。
- 新增 `chatenv token refresh|status|list|clear` 通用 CLI；CLI 只输出 token 文件、profile、类型、时间戳和调用方传入的 safe summary，不输出 raw token/cookie/CSRF values。
- 新增 `ChatArchPaths.tokens_dir`，让 env profile 与 token profile 在同一 ChatArch home 下保持一一对应。

## 0.2.4 - 2026-08-11

- 新增顶层 `chatenv --tree`，从 Click 注册命令树生成当前命令面，包含 `--help`、`--version`、`--tree`、`--home` 和所有已注册命令的一行用途说明。
- 为 `--tree` 增加 CLI 合约测试，锁住 `init/new/paste/use/list/status/cat/get/set/save/delete/test` 等真实命令面，并确保没有脚手架示例命令泄漏。
- 将发布 workflow 从 Twine secret 上传迁移为 PyPI Trusted Publisher / GitHub OIDC；该项目的 PyPI Publisher 使用 `(Any)` environment，因此 workflow 不设置 GitHub environment。
- 收紧 MkDocs docs extras 上界，并补充 package URLs 的文档/仓库元数据。

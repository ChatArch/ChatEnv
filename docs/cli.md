# CLI 用法

ChatEnv 的 CLI 入口是 `chatenv`。所有命令默认只读取一个根变量：

```bash
export CHATARCH_HOME=~/.chatarch
```

实际 env/profile 根目录为：

```text
$CHATARCH_HOME/envs/
```

也可以对单次命令使用 `--home`：

```bash
chatenv --home /tmp/chatarch cat -t example
```

## 交互策略

缺少必要命令参数时，ChatEnv 默认会在可交互终端中自动补问。例如缺少 profile name、key，或命令需要唯一 config type 但未传 `-t/--type` 时，会进入补参流程。

- `-i`：显式强制交互补问。
- `-I`：显式禁用交互补问，缺必要参数时报错。
- `CHATARCH_AUTO_PROMPT=false`：关闭默认自动补问；不影响显式 `-i`，也不影响必要参数已经足够的命令。

可识别的 false 值为 `false`、`0`、`no`、`off`：

```bash
export CHATARCH_AUTO_PROMPT=false
chatenv get          # 直接报错，不自动询问 key
chatenv get -i       # 仍然强制询问 key
```

## Schema 注册

`chatenv` 命令基于已注册 schema 工作。ChatEnv 内置少量 ChatArch 共享 schema（当前为 OpenAI / Feishu）；业务项目的私有变量仍应定义并注册自己的 `BaseEnvConfig` 子类。

```python
from chatenv import BaseEnvConfig, EnvField

class ExampleConfig(BaseEnvConfig):
    _title = "Example Configuration"
    _aliases = ["example"]
    _storage_dir = "Example"

    EXAMPLE_API_KEY = EnvField("EXAMPLE_API_KEY", is_sensitive=True)
```

## 初始化

```bash
chatenv init                  # 写入全部已注册类型的 active .env
chatenv init -t example       # 只写入 Example 类型
chatenv init -t example -i    # 初始化前逐项补问
```

## 查看

```bash
chatenv --version             # 查看当前 chatenv 版本
chatenv --tree                # 从已注册 Click 命令生成完整命令树
chatenv --tree-brief          # 从同一注册表生成省略参数签名的简略命令树
chatenv list                  # 按类型列出 active .env [default] 和 named profiles
chatenv list -t example
chatenv status                # 列出当前 Python 环境已注册的平台/schema
chatenv status --detail       # 展开每个平台的变量、敏感性、默认值和 provider 来源
chatenv status -t example --detail
chatenv cat                   # 输出所有 active values，敏感值默认打码
chatenv cat -t example
chatenv cat -t example work   # 输出 Example/work.env
chatenv cat -t example --no-mask
```

## Profile

```bash
chatenv new -t example work       # 从当前 active values 创建 work.env
chatenv save -t example work      # 保存当前 active values 到 work.env
chatenv use -t example work       # 将 work.env 激活为 .env
chatenv delete -t example work    # 删除 work.env
```

`new/save/delete` 遇到覆盖或删除会确认；自动化场景使用 `-y/--yes`。

## Key 操作

```bash
chatenv set EXAMPLE_API_KEY=sk-xxx
chatenv get EXAMPLE_API_KEY
```

`set` 会根据 key 所属 schema 写回对应类型的 active `.env`。

## Paste

`paste` 用于跨机器复制 typed env。输入不要求是严格 dotenv 文件，会从终端日志、shell prompt、复制文本里提取已注册 key；同一行里用空格分隔的多个 `KEY='VALUE'` 片段也会被逐个识别。

```bash
chatenv cat -t example --no-mask | chatenv paste --stdin --profile work --yes
chatenv paste --value "EXAMPLE_API_KEY='sk-xxx'" --yes
chatenv paste --value "EXAMPLE_MODEL='gpt example' EXAMPLE_API_KEY='sk-xxx'" --yes
chatenv paste
```

写入前会输出识别概要：识别到哪些类型、哪些 key、未知 key 被忽略。

## Runtime tokens

Token-store 是运行态，不是另一个手工维护 env 文件。日常刷新应由服务包注册 refresh provider 后执行：

```bash
chatenv token refresh PyPI RexWzh
chatenv token status PyPI RexWzh
chatenv token list PyPI
chatenv token clear PyPI RexWzh        # dry-run
chatenv token clear PyPI RexWzh --execute
```

服务包通过 `pyproject.toml` 注册：

```toml
[project.entry-points."chatenv.token_refreshers"]
PyPI = "chatpypi.session_ops:refresh_chatenv_token"
```

刷新函数返回 `chatenv.TokenRefreshResult` 或同形 mapping；ChatEnv 负责写入 `tokens/<Service>/<profile>.json` 并只输出 safe metadata。若确实需要迁移或接入外部刷新器，可显式导入：

```bash
external-refresh-command | chatenv token import PyPI RexWzh --stdin --token-type web_session
```

`token import` 是显式交接入口，不代表 ChatEnv 推荐用户手工维护 token JSON。

## 命令树 / Readback

`chatenv --tree` 从当前安装包的 Click 注册表实时生成带参数签名的命令树；`chatenv --tree-brief` 从同一注册表生成省略参数签名的版本。两者都适合发布验收、文档校对和自动化 readback。

```text
chatenv
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered command tree.
├── --tree-brief  # Print the registered command tree without parameter signatures.
├── --home HOME  # Override CHATARCH_HOME for this command.
├── init [--type CONFIG-TYPES] [--interactive]  # Create or update active typed env files.
├── new [NAME] [--type CONFIG-TYPES] [--yes] [--interactive]  # Create a named typed profile without activating it.
├── paste [--value VALUE] [--stdin] [--profile PROFILE] [--yes] [--interactive]  # Paste loose env text and import recognized keys.
├── use [NAME] [--type CONFIG-TYPES] [--interactive]  # Activate a named profile for one config type.
├── list [--type CONFIG-TYPES]  # List active default and named profiles grouped by config type.
├── status [--type CONFIG-TYPES] [--detail]  # Show registered config platforms and provider ownership.
├── token  # Manage generic runtime token profiles.
│   ├── status <SERVICE> [PROFILE] [--format OUTPUT-FORMAT]  # Show safe runtime token metadata for SERVICE/PROFILE.
│   ├── refresh <SERVICE> [PROFILE] [--format OUTPUT-FORMAT]  # Refresh SERVICE/PROFILE through a registered service refresh provider.
│   ├── import <SERVICE> [PROFILE] [--stdin] [--file VALUE-FILE] [--token-type TOKEN-TYPE] [--summary SUMMARY] [--expires-at EXPIRES-AT] [--format OUTPUT-FORMAT]  # Explicitly import externally refreshed runtime token JSON.
│   ├── list [SERVICE] [--format OUTPUT-FORMAT]  # List runtime token profiles grouped by service.
│   └── clear <SERVICE> [PROFILE] [--execute] [--format OUTPUT-FORMAT]  # Clear a generic runtime token file for SERVICE/PROFILE.
├── cat [NAME] [--no-mask] [--type CONFIG-TYPES]  # Print active values, or a named typed profile with -t TYPE NAME.
├── get [KEY] [--interactive]  # Get a configuration value from active typed env files.
├── set [KEY-VALUE] [--interactive]  # Set a configuration value in the matching active typed env file.
├── save [NAME] [--type CONFIG-TYPES] [--yes] [--interactive]  # Save current active values as a named profile.
├── delete [NAME] [--type CONFIG-TYPES] [--yes] [--interactive]  # Delete a named profile for one config type.
└── test [--target TARGET] [--interactive]  # Test a registered configuration schema.
```

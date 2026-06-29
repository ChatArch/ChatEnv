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
chatenv list                  # 按类型列出 named profiles
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

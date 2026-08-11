<div align="center">
    <a href="https://pypi.python.org/pypi/chatenv">
        <img src="https://img.shields.io/pypi/v/chatenv.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/ChatArch/ChatEnv/actions/workflows/ci.yml">
        <img src="https://github.com/ChatArch/ChatEnv/actions/workflows/ci.yml/badge.svg" alt="Tests" />
    </a>
    <a href="https://pypi.python.org/pypi/chatenv">
        <img src="https://img.shields.io/pypi/pyversions/chatenv.svg" alt="Python versions" />
    </a>
    <a href="LICENSE">
        <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
    </a>
</div>

<div align="center">

# ChatEnv

ChatArch typed env/profile runtime.

</div>

ChatEnv 是 ChatArch / chatxxx 系列项目共用的 typed env/profile 底层包。它提供字段描述、配置基类、registry、路径、profile 文件读写、mask 和 paste 解析等通用能力；同时内置少量跨工具共享 schema（当前为 OpenAI / Feishu）。工具私有变量仍由 ChatTool、ChatDNS 等项目自己定义并注册。

当前设计保持减法：只使用一个根变量 `CHATARCH_HOME`，只管理 env/profile 文件，不额外创建 config/cache/data/state。

支持 Python `>=3.10`。

## 安装

```bash
pip install chatenv --upgrade
pip install -e .[dev]       # 仓库开发
```

## 目录

```text
CHATARCH_HOME=${CHATARCH_HOME:-~/.chatarch}
$CHATARCH_HOME/envs/      # stable typed env/profile files
$CHATARCH_HOME/tokens/    # generated runtime tokens/sessions, parallel to env profiles
```

实际布局由业务项目注册的 schema 决定，例如：

```text
~/.chatarch/envs/
  Example/
    .env
    work.env
```

- `.env` 是当前 active profile；
- `name.env` 是 named profile；
- `use` 会把 named profile 复制为 active `.env`。

## CLI 概览

`chatenv` CLI 基于已注册 schema 工作。单独安装且没有项目注册 schema 时，它会提示需要先注册配置类型。业务项目通常会在自己的 CLI 中导入 schema 后复用这些能力。

```bash
chatenv --version
chatenv --tree
chatenv init -t example
chatenv status
chatenv status --detail
chatenv cat -t example
chatenv cat -t example --no-mask | chatenv paste --stdin --profile work --yes
chatenv set EXAMPLE_API_KEY=sk-xxx
chatenv get EXAMPLE_API_KEY
chatenv new -t example work
chatenv save -t example work
chatenv use -t example work
chatenv delete -t example work
```

单次命令可通过 `--home` 覆盖根目录：

```bash
chatenv --home /tmp/chatarch cat -t example
```

缺少必要命令参数时，ChatEnv 默认会在可交互终端中自动补问；显式 `-i` 始终强制补问，`-I` 始终禁用补问。自动化环境可设置：

```bash
export CHATARCH_AUTO_PROMPT=false
```

此时只有缺少必要参数的命令会直接报错；参数已经足够的命令行为不变。

`chatenv --tree` 可从当前安装包的 Click 注册表实时输出完整命令树，用于验收和脚本 readback。

更多用法见 `docs/cli.md`。

## Runtime tokens

ChatEnv 区分 stable env/profile 和动态 runtime token：

- `envs/<Service>/<profile>.env` 保存可长期维护的稳定配置，例如 base URL、账号、API key 或 refresh/login 所需输入；
- `tokens/<Service>/<profile>.json` 保存由登录或刷新流程生成的 access token、session、cookie/CSRF 等运行态；
- `chatenv token refresh SERVICE PROFILE` 会调用服务包通过 `chatenv.token_refreshers` 注册的刷新器，自动生成并更新 token-store；
- 手工 JSON 写入只保留为显式 `chatenv token import ... --stdin/--file`，用于迁移、调试或外部刷新器交接，不应作为日常维护入口。

ChatEnv 只负责路径、profile 校验、原子写入和 safe status/list/clear；具体登录、OAuth refresh、cookie 刷新等业务语义仍由 leaf package 负责。

## Paste

`paste` 是跨设备复制密钥的核心入口。输入不要求是严格 dotenv 文件，会从终端日志、shell prompt、复制文本里提取已注册 key；同一行里用空格分隔的多个 `KEY='VALUE'` 片段也会被逐个识别。

```bash
chatenv paste
chatenv paste --stdin --profile work
chatenv paste --value "EXAMPLE_API_KEY='sk-xxx'" --yes
chatenv paste --value "EXAMPLE_MODEL='gpt example' EXAMPLE_API_KEY='sk-xxx'" --yes
```

写入前会输出识别概要：识别到哪些类型、哪些 key、未知 key 被忽略。

## Python API

```python
from chatenv import BaseEnvConfig, EnvField, EnvStore, get_paths

class ExampleConfig(BaseEnvConfig):
    _title = "Example Configuration"
    _aliases = ["example"]
    _storage_dir = "Example"

    EXAMPLE_API_KEY = EnvField("EXAMPLE_API_KEY", is_sensitive=True)

paths = get_paths()
store = EnvStore(paths.envs_dir)
store.save_active(ExampleConfig, {"EXAMPLE_API_KEY": "sk-..."})
```

## 文档

- `docs/cli.md`：CLI 用法
- `docs/design.md`：路径、数据布局与注册策略
- `docs/developer-guide.md`：chatxxx 项目接入和 provider 开发指南
- `docs/development.md`：测试、构建与发布
- `mkdocs.yml`：Material for MkDocs 文档站点配置

## 开发

```bash
python -m pytest -q
python -m build
python -m twine check dist/*
python -m pip install -e .[docs]
python -m mkdocs serve
```

也可以用 ChatTool helper：

```bash
chattool pypi build --project-dir .
chattool pypi check --project-dir .
```

## 开源协议

MIT License

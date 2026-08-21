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

ChatEnv 是 ChatArch / chatxxx 系列项目共用的 typed env/profile 底层包。它提供字段描述、配置基类、registry、路径、profile 文件读写、mask、paste 解析，以及 runtime token-store 的通用能力；具体业务变量、登录刷新和连通性语义由各项目自己定义并注册。

文档入口：https://arch.gh.wzhecnu.cn/ChatEnv/

## 安装

```bash
pip install chatenv --upgrade
chatenv --version
chatenv --tree
chatenv --tree-brief
```

支持 Python `>=3.10`。

## 目录

```text
CHATARCH_HOME=${CHATARCH_HOME:-~/.chatarch}
$CHATARCH_HOME/envs/      # stable typed env/profile files
$CHATARCH_HOME/tokens/    # generated runtime tokens/sessions, parallel to env profiles
```

ChatEnv 只负责 stable env/profile 与 runtime token-store 的存储规则，不额外创建 config/cache/data/state，也不把 `tokens/` 当作第二个手工维护 secret/env 层。

## CLI 树

`chatenv --tree` 从当前安装包的 Click 注册表实时输出带参数签名的完整命令面；`chatenv --tree-brief` 读取同一注册表，但省略参数签名。

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

## 常用命令

```bash
chatenv init -t example
chatenv status --detail
chatenv cat -t example
chatenv paste --stdin --profile work --yes
chatenv set EXAMPLE_API_KEY=sk-xxx
chatenv get EXAMPLE_API_KEY
chatenv token refresh PyPI RexWzh
chatenv token status PyPI RexWzh
```

敏感值默认 mask；`token status/list/clear` 只输出 safe metadata，不输出 raw token/cookie/CSRF values。

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

- https://arch.gh.wzhecnu.cn/ChatEnv/
- `docs/cli.md`：CLI 用法
- `docs/design.md`：路径、数据布局与注册策略
- `docs/developer-guide.md`：chatxxx 项目接入和 provider 开发指南
- `docs/development.md`：测试、构建与发布

## 开发

```bash
python -m pip install -e .[dev,docs]
python -m pytest -q
python -m mkdocs build --strict
python -m build
python -m twine check dist/*
```

## 开源协议

MIT License

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

ChatArch typed env/profile manager.

</div>

ChatEnv 是 ChatArch 的底层 typed env/profile 管理包，用来把 OpenAI、DNS、Feishu 等工具密钥按“配置类型 + profile”存到统一位置，并提供 Python API 与 `chatenv` CLI。

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
$CHATARCH_HOME/envs/
```

实际布局：

```text
~/.chatarch/envs/
  OpenAI/
    .env
    work.env
  Aliyun/
    .env
  Tencent/
    .env
```

- `.env` 是当前 active profile；
- `name.env` 是 named profile；
- `chatenv use -t TYPE name` 会把 named profile 复制为 active `.env`。

## CLI 概览

```bash
chatenv init -t oai
chatenv cat -t oai
chatenv cat -t oai --no-mask | chatenv paste --stdin --profile work --yes
chatenv set OPENAI_API_KEY=sk-xxx
chatenv get OPENAI_API_KEY
chatenv new -t oai work
chatenv save -t oai work
chatenv use -t oai work
chatenv delete -t oai work
chatenv migrate chattool          # dry-run
chatenv migrate chattool --execute
```

单次命令可通过 `--home` 覆盖根目录：

```bash
chatenv --home /tmp/chatarch cat -t oai
```

更多用法见 `docs/cli.md`。

## Paste

`paste` 是跨设备复制密钥的核心入口。输入不要求是严格 dotenv 文件，会从终端日志、shell prompt、复制文本里提取已注册 key。

```bash
chatenv paste
chatenv paste --stdin --profile work
chatenv paste --value "OPENAI_API_KEY='sk-xxx'" --yes
```

写入前会输出识别概要：识别到哪些类型、哪些 key、未知 key 被忽略。

## Python API

```python
from chatenv import BaseEnvConfig, EnvField, EnvStore, get_paths

class OpenAIConfig(BaseEnvConfig):
    _title = "OpenAI Configuration"
    _aliases = ["oai", "openai"]
    _storage_dir = "OpenAI"

    OPENAI_API_KEY = EnvField("OPENAI_API_KEY", is_sensitive=True)

paths = get_paths()
store = EnvStore(paths.envs_dir)
store.save_active(OpenAIConfig, {"OPENAI_API_KEY": "sk-..."})
```

## 文档

- `docs/cli.md`：CLI 用法
- `docs/design.md`：路径、数据布局与兼容策略
- `docs/development.md`：测试、构建与发布

## 开发

```bash
python -m pytest -q
python -m build
python -m twine check dist/*
```

也可以用 ChatTool helper：

```bash
chattool pypi build --project-dir .
chattool pypi check --project-dir .
```

## 开源协议

MIT License

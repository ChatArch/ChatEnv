# 开发指南

本文面向想在 `chatxxx` 项目中接入 ChatEnv 的开发者。ChatEnv 只负责 typed env/profile 的通用运行时，具体变量、连通性测试和业务含义都留在各项目内部。

## 开发边界

ChatEnv 提供：

- `EnvField`：描述一个环境变量的 key、默认值、说明和敏感性；
- `BaseEnvConfig`：typed schema 基类和自动 registry；
- `EnvStore`：active `.env` 与 named profile 的读写；
- `chatenv` CLI：`init/new/paste/use/list/cat/get/set/save/delete/test`；
- `chatenv.configs` entry point discovery：加载外部项目注册的 schema provider。

业务项目负责：

- 定义自己的 `BaseEnvConfig` 子类；
- 给 schema 设置 `_aliases` 和 `_storage_dir`；
- 在 `pyproject.toml` 注册 `chatenv.configs` entry point；
- 如需验证服务可用性，在 schema 类里实现 `test()`；
- 不在 ChatEnv 中加入具体业务变量。

## 目录约定

ChatEnv 默认只读一个根变量：

```bash
export CHATARCH_HOME=~/.chatarch
```

env/profile 数据固定放在：

```text
$CHATARCH_HOME/envs/
```

例如 `ExampleConfig._storage_dir = "Example"` 时：

```text
~/.chatarch/envs/
  Example/
    .env
    work.env
```

不再提供 `CHATTOOL_ENV_FILE`、`CHATARCH_ENV_FILE`、platformdirs fallback 或自动迁移逻辑。需要迁移旧目录时，由上层项目提供显式脚本。

## 在 chatxxx 项目中接入

第一步，依赖 ChatEnv：

```toml
[project]
dependencies = [
    "chatenv>=0.2.0,<0.3.0",
]
```

第二步，定义 schema。建议放在业务项目自己的 `config` 包内，例如 `chatfoo/config.py`：

```python
from chatenv import BaseEnvConfig, EnvField


class FooConfig(BaseEnvConfig):
    _title = "Foo Configuration"
    _aliases = ["foo", "chatfoo"]
    _storage_dir = "Foo"

    FOO_API_BASE = EnvField("FOO_API_BASE", desc="Foo API base URL")
    FOO_API_KEY = EnvField("FOO_API_KEY", desc="Foo API key", is_sensitive=True)

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        # 这里写业务项目自己的连通性验证。
        print("✅ Success!")
```

第三步，注册 provider entry point：

```toml
[project.entry-points."chatenv.configs"]
chatfoo = "chatfoo.config"
```

安装 `chatfoo` 后，运行 `chatenv` 时会加载 `chatfoo.config`。模块 import 后，`FooConfig(BaseEnvConfig)` 会通过 `BaseEnvConfig.__init_subclass__` 自动进入 registry。

## CLI 如何找到 schema

`chatenv` 启动时会执行 provider discovery：

```python
from importlib.metadata import entry_points

for ep in entry_points(group="chatenv.configs"):
    ep.load()
```

它的含义是：从已安装包的 metadata 中找到所有声明在 `chatenv.configs` 组下的入口，然后 import 对应模块。

完整过程如下：

```text
chatenv cat -t foo
  -> load_config_providers()
  -> entry_points(group="chatenv.configs")
  -> ep.load() imports chatfoo.config
  -> FooConfig 自动注册到 BaseEnvConfig._registry
  -> -t foo 解析到 FooConfig
  -> EnvStore 读取 ~/.chatarch/envs/Foo/.env
```

因此，ChatEnv CLI 拥有固定命令；业务项目只提供 schema provider。不要在每个项目里重复实现一套 env CLI。

## 内置共享 schema

ChatEnv 内置少量 ChatArch 生态中会被多个工具交叉引用的共享 schema：

- `OpenAIConfig`：`OpenAI` / `oai` / `openai`
- `FeishuConfig`：`Feishu` / `feishu` / `lark`

这些 schema 可直接从 `chatenv.configs` 或 `chatenv` 导入。业务项目不要重复注册同一 logical config；若旧 provider 仍注册相同 `_storage_dir`，ChatEnv 会保留先注册的 canonical schema 并跳过重复注册。

工具私有 schema 仍应留在各自包中，通过 `chatenv.configs` entry point 注册。

## 本地联调

在两个本地仓库联调时，可以用 editable install：

```bash
python -m pip install -e /path/to/ChatEnv
python -m pip install -e /path/to/chatfoo
```

查看当前 Python 环境里有哪些 provider：

```bash
python - <<'PY'
from importlib.metadata import entry_points

for ep in entry_points(group="chatenv.configs"):
    print(ep.name, "=>", ep.value)
PY
```

验证 CLI：

```bash
chatenv list
chatenv init -t foo -i
chatenv cat -t foo
chatenv test -t foo
```

如果 provider 加载失败，可打开 debug 输出：

```bash
CHATENV_DEBUG=1 chatenv list
```

## ChatEnv 仓库开发

```bash
python -m pip install -e .[dev,docs]
python -m pytest -q
python -m mkdocs build --strict
```

构建发布包：

```bash
python -m build
python -m twine check dist/*
```

发布前检查：

- `src/chatenv/__init__.py` 中的 `__version__` 已更新；
- `README.md`、`docs/cli.md`、`docs/design.md`、本文档已同步；
- 没有把业务项目的具体变量写入 ChatEnv；
- 没有新增分散路径环境变量；
- 测试和 MkDocs strict build 通过。

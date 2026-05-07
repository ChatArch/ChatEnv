# 设计说明

ChatEnv 是 ChatArch / chatxxx 系列项目的 typed env/profile 底层模块。它的职责是提供通用的字段描述、配置基类、registry、路径、profile 文件读写、mask 和 paste 解析；具体 env 变量由各项目自己定义和注册。

## 目录原则

本阶段做减法，只保留一个根变量：

```text
CHATARCH_HOME=${CHATARCH_HOME:-~/.chatarch}
$CHATARCH_HOME/envs/
```

不新增以下状态面：

- 工具级 config 目录；
- cache 目录；
- data/state 目录；
- 细分路径环境变量。

ChatEnv 只负责 env/profile 存储规则，不负责业务工具自己的普通配置和缓存。

## 数据布局

```text
$CHATARCH_HOME/envs/
  Example/
    .env
    work.env
    apple.env
```

每个 schema 类型对应一个目录：

- `.env` 是 active profile；
- `name.env` 是 named profile；
- `use` 将 named profile 复制为 active `.env`。

目录名来自业务项目定义的 `_storage_dir` / `get_storage_name()`。

## 注册策略

ChatEnv 沿用注册式配置模型：

```python
from chatenv import BaseEnvConfig, EnvField

class ExampleConfig(BaseEnvConfig):
    _title = "Example Configuration"
    _aliases = ["example"]
    _storage_dir = "Example"

    EXAMPLE_API_KEY = EnvField("EXAMPLE_API_KEY", is_sensitive=True)
```

实际注册逻辑发生在业务项目中：业务项目 import 自己的配置模块后，配置类通过 `BaseEnvConfig.__init_subclass__` 进入 registry。ChatEnv 不内置 ChatTool、ChatDNS 等项目的具体变量清单。

## 分层

```text
chatenv.paths       # CHATARCH_HOME 与 envs_dir
chatenv.fields      # EnvField / BaseEnvConfig
chatenv.registry    # type / alias 解析
chatenv.store       # profile 文件读写
chatenv.paste       # 宽松 paste parser
chatenv.discovery   # entry point provider 加载
chatenv.cli         # click CLI / 可复用 command handler
```

core 模块不依赖 ChatTool，也不包含 ChatTool 的业务 schema 或连通性测试。

## ChatTool 7.0.0 接入策略

ChatTool 作为 consumer：

- `chattool.config` 兼容导出 `chatenv.BaseEnvConfig` / `EnvField`；
- ChatTool 在 `chattool.config` 包内定义具体 schema，后续可按配置类型拆文件；
- ChatTool 通过 `chatenv.configs` entry point 注册 `chattool.config`；
- `chatenv` 启动时加载 provider，并复用 ChatEnv 的 store/parser/registry 能力；
- `chattool.const` 默认读取 `$CHATARCH_HOME/envs`；
- 不做旧 `platformdirs` 路径 fallback，不提供 migrate 命令。

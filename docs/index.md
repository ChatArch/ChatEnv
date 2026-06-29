# ChatEnv

ChatEnv 是 ChatArch / chatxxx 系列项目共用的 typed env/profile 底层包。

它只提供字段描述、配置基类、registry、路径、profile 文件读写、mask 和 paste 解析等通用能力；具体变量由 ChatTool、ChatDNS 等项目自己定义并注册。

`chatenv status` 可以查看当前 Python 环境已注册的平台/schema；`chatenv status --detail` 会展开变量清单并标明每个变量来自哪个 provider 包。

## 最小路径

```text
CHATARCH_HOME=${CHATARCH_HOME:-~/.chatarch}
$CHATARCH_HOME/envs/
```

本包不额外管理 config/cache/data/state，也不保留 ChatTool 旧路径 fallback。

## 快速示例

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

更多命令用法见 [CLI](cli.md)，整体边界见 [设计](design.md)。

如果要在新的 `chatxxx` 项目里接入 ChatEnv，参考 [开发指南](developer-guide.md)。

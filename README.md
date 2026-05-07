# chatenv

ChatEnv is the typed env/profile manager for ChatArch. It stores profiles under a single root:

```text
CHATARCH_HOME=${CHATARCH_HOME:-~/.chatarch}
$CHATARCH_HOME/envs/
```

It intentionally does not create separate config/cache/data/state directories. The first version focuses on the env files that ChatTool already uses in practice.

## Install locally

```bash
pip install -e .
```

## CLI

```bash
chatenv init -t oai
chatenv set OPENAI_API_KEY=sk-xxx
chatenv get OPENAI_API_KEY
chatenv cat -t oai
chatenv save -t oai work
chatenv use -t oai work
chatenv paste --stdin --profile work
chatenv migrate chattool          # dry run
chatenv migrate chattool --execute
```

Use `--home /path/to/chatarch` on any command, or set `CHATARCH_HOME`, to redirect the root.

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

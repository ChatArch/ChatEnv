# Design

ChatEnv is the typed env/profile base layer for ChatArch packages. It owns reusable field descriptors, config base classes, registry lookup, paths, profile file IO, masking, paste parsing, and runtime token-store primitives.

## Directory principle

ChatEnv intentionally keeps one root variable:

```text
CHATARCH_HOME=${CHATARCH_HOME:-~/.chatarch}
$CHATARCH_HOME/envs/      # stable typed env/profile files
$CHATARCH_HOME/tokens/    # generated runtime token/session files
```

It does not add tool-level config directories, cache directories, data/state directories, or extra path environment variables. Leaf packages own their own service config/cache/data if needed.

## Data layout

```text
$CHATARCH_HOME/envs/
  Example/
    .env
    work.env
```

Each schema maps to one storage directory. `.env` is the active profile, and `name.env` is a named profile. `use` copies a named profile into `.env`.

Runtime tokens are parallel to env profiles:

```text
$CHATARCH_HOME/tokens/
  Service/
    default.json
    work.json
```

Token files contain opaque values plus safe metadata. ChatEnv never interprets service-specific token semantics.

## Registration

Leaf packages define `BaseEnvConfig` subclasses:

```python
from chatenv import BaseEnvConfig, EnvField

class ExampleConfig(BaseEnvConfig):
    _title = "Example Configuration"
    _aliases = ["example"]
    _storage_dir = "Example"

    EXAMPLE_API_KEY = EnvField("EXAMPLE_API_KEY", is_sensitive=True)
```

Installed packages expose providers through `chatenv.configs` and optional refresh hooks through `chatenv.token_refreshers`.

## Layers

```text
chatenv.paths       # CHATARCH_HOME, envs_dir, tokens_dir
chatenv.fields      # EnvField / BaseEnvConfig
chatenv.registry    # type / alias resolution
chatenv.store       # profile file IO
chatenv.tokens      # opaque runtime token-store and safe metadata
chatenv.token_refreshers  # service-owned refresh hook discovery
chatenv.paste       # loose paste parser
chatenv.discovery   # entry point provider loading
chatenv.cli         # Click CLI and reusable handlers
```

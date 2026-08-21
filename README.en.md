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

Typed env/profile runtime for ChatArch packages.

</div>

ChatEnv is the shared typed env/profile layer for ChatArch packages. It provides field descriptors, config base classes, registry discovery, paths, profile file IO, masking, paste parsing, and the runtime token-store. Service-specific variables, login refresh, and connectivity semantics stay in leaf packages.

Documentation: https://arch.gh.wzhecnu.cn/ChatEnv/en/

## Install

```bash
pip install chatenv --upgrade
chatenv --version
chatenv --tree
chatenv --tree-brief
```

Python `>=3.10` is supported.

## Layout

```text
CHATARCH_HOME=${CHATARCH_HOME:-~/.chatarch}
$CHATARCH_HOME/envs/      # stable typed env/profile files
$CHATARCH_HOME/tokens/    # generated runtime tokens/sessions, parallel to env profiles
```

ChatEnv manages only stable env/profile files and runtime token-store files. It does not create extra config/cache/data/state surfaces, and `tokens/` is not a second manually maintained secret/env layer.

## CLI tree

`chatenv --tree` renders the live Click command registry with parameter signatures. `chatenv --tree-brief` reads the same registry without parameter signatures.

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

## Common commands

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

Sensitive values are masked by default. `token status/list/clear` prints safe metadata only and never prints raw token/cookie/CSRF values.

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

## Docs

- https://arch.gh.wzhecnu.cn/ChatEnv/en/
- `docs/cli.en.md`: CLI usage
- `docs/design.en.md`: layout and registry design
- `docs/developer-guide.en.md`: integration guide for chatxxx packages
- `docs/development.en.md`: testing, build, and release

## Development

```bash
python -m pip install -e .[dev,docs]
python -m pytest -q
python -m mkdocs build --strict
python -m build
python -m twine check dist/*
```

## License

MIT License

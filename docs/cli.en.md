# CLI Usage

The CLI entrypoint is `chatenv`. Commands use one root variable by default:

```bash
export CHATARCH_HOME=~/.chatarch
```

Profiles are stored under:

```text
$CHATARCH_HOME/envs/
```

Use `--home` for a single command override:

```bash
chatenv --home /tmp/chatarch cat -t example
```

## Interactive behavior

When required arguments are missing, ChatEnv asks interactively in a TTY. Use `-i` to force prompts, `-I` to disable prompts, or `CHATARCH_AUTO_PROMPT=false` to disable default auto-prompting for automation.

## Schema registration

ChatEnv loads config providers through the `chatenv.configs` entry point. Leaf packages define their own `BaseEnvConfig` classes and register them in package metadata.

## Common commands

```bash
chatenv --version
chatenv --tree
chatenv init -t example
chatenv status --detail
chatenv list -t example
chatenv cat -t example
chatenv paste --stdin --profile work --yes
chatenv set EXAMPLE_API_KEY=sk-xxx
chatenv get EXAMPLE_API_KEY
```

## Runtime tokens

Runtime tokens are generated state, not manually maintained env files:

```bash
chatenv token refresh PyPI RexWzh
chatenv token status PyPI RexWzh
chatenv token list PyPI
chatenv token clear PyPI RexWzh        # dry-run
chatenv token clear PyPI RexWzh --execute
```

A service package registers a refresh provider through:

```toml
[project.entry-points."chatenv.token_refreshers"]
PyPI = "chatpypi.session_ops:refresh_chatenv_token"
```

ChatEnv writes `tokens/<Service>/<profile>.json` and prints safe metadata only.

## CLI tree / readback

```text
chatenv [--home <HOME>]  # Manage typed env profiles under $CHATARCH_HOME/envs.
├── --help  # Show this help message.
├── --version  # Show the installed package version.
├── --tree  # Print the registered command tree.
├── init [--type <CONFIG-TYPES>] [--interactive/--no-interactive]  # Create or update active typed env files.
├── new [NAME] [--type <CONFIG-TYPES>] [--yes] [--interactive/--no-interactive]  # Create a named typed profile without activating it.
├── paste [--value <VALUE>] [--stdin] [--profile <PROFILE>] [--yes] [--interactive/--no-interactive]  # Paste loose env text and import recognized keys.
├── use [NAME] [--type <CONFIG-TYPES>] [--interactive/--no-interactive]  # Activate a named profile for one config type.
├── list [--type <CONFIG-TYPES>]  # List active default and named profiles grouped by config type.
├── status [--type <CONFIG-TYPES>] [--detail]  # Show registered config platforms and provider ownership.
├── token  # Manage generic runtime token profiles.
│   ├── status <SERVICE> [PROFILE] [--format <OUTPUT-FORMAT>]  # Show safe runtime token metadata for SERVICE/PROFILE.
│   ├── refresh <SERVICE> [PROFILE] [--format <OUTPUT-FORMAT>]  # Refresh SERVICE/PROFILE through a registered service refresh provider.
│   ├── import <SERVICE> [PROFILE] [--stdin] [--file <VALUE-FILE>] [--token-type <TOKEN-TYPE>] [--summary <SUMMARY>] [--expires-at <EXPIRES-AT>] [--format <OUTPUT-FORMAT>]  # Explicitly import externally refreshed runtime token JSON.
│   ├── list [SERVICE] [--format <OUTPUT-FORMAT>]  # List runtime token profiles grouped by service.
│   └── clear <SERVICE> [PROFILE] [--execute] [--format <OUTPUT-FORMAT>]  # Clear a generic runtime token file for SERVICE/PROFILE.
├── cat [NAME] [--no-mask] [--type <CONFIG-TYPES>]  # Print active values, or a named typed profile with -t TYPE NAME.
├── get [KEY] [--interactive/--no-interactive]  # Get a configuration value from active typed env files.
├── set [KEY-VALUE] [--interactive/--no-interactive]  # Set a configuration value in the matching active typed env file.
├── save [NAME] [--type <CONFIG-TYPES>] [--yes] [--interactive/--no-interactive]  # Save current active values as a named profile.
├── delete [NAME] [--type <CONFIG-TYPES>] [--yes] [--interactive/--no-interactive]  # Delete a named profile for one config type.
└── test [--target <TARGET>] [--interactive/--no-interactive]  # Test a registered configuration schema.
```

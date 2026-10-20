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

When required arguments are missing, ChatEnv asks interactively in a TTY. `CHATARCH_AUTO_PROMPT` is a built-in, non-sensitive `ChatArch` typed field with the string default `true`; its active profile is stored at `$CHATARCH_HOME/envs/ChatArch/.env`, and its type alias is `chatarch`.

```bash
chatenv status -t chatarch --detail
chatenv set CHATARCH_AUTO_PROMPT=false
chatenv save -t chatarch automation-off
chatenv use -t chatarch automation-off
```

For default prompting, precedence is explicit `-i/-I`, process `CHATARCH_AUTO_PROMPT`, the active `ChatArch/.env` under the selected home, then `true`. `-i` still requires an interactive TTY; `-I` disables prompting. `0`, `false`, `no`, and `off` disable default prompting, while other strings remain enabled.

Active-profile integration is currently implemented by the ChatEnv CLI only. Other ChatArch CLIs still need to adopt it; the process environment variable remains a shared override for CLIs that support it.

## Schema registration

ChatEnv loads config providers through the `chatenv.configs` entry point. Its built-in shared schemas currently cover ChatArch, OpenAI, and Feishu. Leaf packages define their own `BaseEnvConfig` classes and register them in package metadata.

## Common commands

```bash
chatenv --version
chatenv --tree
chatenv --tree-brief
chatenv init -t example
chatenv status --detail
chatenv list -t example
chatenv cat -t example
chatenv paste --stdin --profile work --yes
chatenv set EXAMPLE_API_KEY=sk-xxx
chatenv get EXAMPLE_API_KEY
```

## Test configuration

```bash
chatenv test -t example             # Test the current active configuration
chatenv test -t example work        # Test only Example/work.env without activating it
chatenv --home /tmp/chatarch test -t example work
```

Without a profile, the command loads the target's active `.env` under the selected home, then falls back to process environment variables and schema defaults for missing fields. With a profile, it loads only that target's named profile and schema defaults. Missing fields never reuse active values, process environment variables, or values left by an earlier command. A missing profile fails before the provider's `test()` runs, and no configuration files are changed.

Each service package defines its test behavior, which may include live network requests. For example, with ChatGH installed, `chatenv test -t gh work` tests the GitHub `work` profile.

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

`chatenv --tree` renders the live Click registry with parameter signatures. `chatenv --tree-brief` reads the same registry without parameter signatures.

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
└── test [PROFILE] [--target TARGET] [--interactive]  # Test active configuration or a named PROFILE for one target.
```

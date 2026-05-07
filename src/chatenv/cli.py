from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any

import click

from .fields import BaseEnvConfig, EnvField, normalize_profile_name
from .paste import PasteResult, iter_fields_for_values, parse_pasted_env_text
from .paths import get_paths
from .registry import require_single_config, resolve_config_types
from .store import EnvStore
from .utils import mask_secret

# Register the compatibility schemas by default. Downstream packages may import
# their own schema modules before invoking cli() to extend the registry.
import chatenv.presets.chattool  # noqa: F401,E402


@click.group(name="chatenv")
@click.option("--home", type=click.Path(file_okay=False, path_type=Path), help="Override CHATARCH_HOME for this command.")
@click.pass_context
def cli(ctx: click.Context, home: Path | None):
    """Manage typed env profiles under $CHATARCH_HOME/envs."""
    paths = get_paths(home)
    ctx.obj = {"paths": paths, "store": EnvStore(paths.envs_dir)}


def _store(ctx: click.Context) -> EnvStore:
    return ctx.obj["store"]


def _envs_dir(ctx: click.Context) -> Path:
    return ctx.obj["paths"].envs_dir


def _matched_or_all(config_types: tuple[str, ...]) -> list[type[BaseEnvConfig]]:
    return resolve_config_types(config_types) if config_types else list(BaseEnvConfig._registry)


def _require_one(config_types: tuple[str, ...], action: str) -> type[BaseEnvConfig]:
    try:
        return require_single_config(config_types, action)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


def _field_line(field: EnvField, no_mask: bool = False) -> str:
    value = "" if field.value is None else str(field.value)
    if field.is_sensitive and not no_mask:
        value = mask_secret(value)
    return f"{field.env_key}='{value}'"


def _load_all(ctx: click.Context) -> None:
    BaseEnvConfig.load_all(_envs_dir(ctx))


def _write_active(ctx: click.Context, config_cls: type[BaseEnvConfig]) -> Path:
    return _store(ctx).save_active(config_cls)


def _configure_fields(config_cls: type[BaseEnvConfig]) -> None:
    click.echo(f"\n[{config_cls._title}]")
    for name, field in config_cls.get_fields().items():
        prompt = name if not field.desc else f"{name} ({field.desc})"
        default_value = field.value if field.value is not None else field.default
        if field.is_sensitive:
            hint = mask_secret(default_value) if default_value else ""
            suffix = f" [current: {hint}]" if hint else ""
            value = click.prompt(f"{prompt}{suffix}", default="", hide_input=True, show_default=False)
            if value:
                field.value = value
        else:
            value = click.prompt(prompt, default="" if default_value is None else str(default_value), show_default=default_value is not None)
            if value:
                field.value = value


@cli.command(name="init")
@click.option("--type", "config_types", "-t", multiple=True, help="Filter config types by title, storage name, or alias.")
@click.option("--interactive/--no-interactive", "interactive", "-i/-I", default=False, help="Prompt for values before writing files.")
@click.pass_context
def init_env(ctx: click.Context, config_types: tuple[str, ...], interactive: bool):
    """Create or update active typed env files."""
    configs = _matched_or_all(config_types)
    if config_types and not configs:
        raise click.ClickException(f"No configuration types matched: {', '.join(config_types)}")
    _load_all(ctx)
    if interactive:
        for config_cls in configs:
            _configure_fields(config_cls)
    for config_cls in configs:
        _write_active(ctx, config_cls)
    click.echo(f"Configuration saved to {_envs_dir(ctx)}")


@cli.command(name="list")
@click.option("--type", "config_types", "-t", multiple=True, help="Filter config types.")
@click.pass_context
def list_env(ctx: click.Context, config_types: tuple[str, ...]):
    """List available named profiles grouped by config type."""
    store = _store(ctx)
    configs = _matched_or_all(config_types)
    if config_types and not configs:
        raise click.ClickException(f"No configuration types matched: {', '.join(config_types)}")
    found = False
    for config_cls in configs:
        profiles = store.list_profiles(config_cls)
        if not profiles:
            continue
        found = True
        click.echo(f"[{config_cls.get_storage_name()}]")
        for profile in profiles:
            click.echo(f"- {profile}.env")
    if not found:
        click.echo(f"No profiles found under {_envs_dir(ctx)}")


@cli.command(name="cat")
@click.argument("name", required=False)
@click.option("--no-mask", is_flag=True, help="Show sensitive values in plain text.")
@click.option("--type", "config_types", "-t", multiple=True, help="Filter config types.")
@click.pass_context
def cat_env(ctx: click.Context, name: str | None, no_mask: bool, config_types: tuple[str, ...]):
    """Print active values, or a named typed profile with -t TYPE NAME."""
    if name:
        config_cls = _require_one(config_types, "cat")
        path = _store(ctx).profile_path(config_cls, name)
        if not path.exists():
            raise click.ClickException(f"Environment file '{path}' not found.")
        config_cls.load_from_dict(_store(ctx).load_path(path))
        for field in config_cls.get_fields().values():
            click.echo(_field_line(field, no_mask))
        return

    configs = _matched_or_all(config_types)
    if config_types and not configs:
        raise click.ClickException(f"No configuration types matched: {', '.join(config_types)}")
    _load_all(ctx)
    for index, config_cls in enumerate(configs):
        if len(configs) > 1:
            if index:
                click.echo("")
            click.echo(f"# {config_cls.get_storage_name()}")
        for field in config_cls.get_fields().values():
            click.echo(_field_line(field, no_mask))


@cli.command(name="new")
@click.argument("name")
@click.option("--type", "config_types", "-t", multiple=True, required=True, help="Target exactly one config type.")
@click.option("--yes", "yes", "-y", is_flag=True, help="Overwrite without prompting.")
@click.pass_context
def new_env(ctx: click.Context, name: str, config_types: tuple[str, ...], yes: bool):
    """Create a named typed profile without activating it."""
    config_cls = _require_one(config_types, "new")
    name = normalize_profile_name(name)
    store = _store(ctx)
    target = store.profile_path(config_cls, name)
    if target.exists() and not yes and not click.confirm(f"Profile '{name}' exists. Overwrite?", default=False):
        raise click.Abort()
    _load_all(ctx)
    store.save_profile(config_cls, name)
    click.echo(f"Created {config_cls.get_storage_name()} profile '{target.name}'")


@cli.command(name="save")
@click.argument("name")
@click.option("--type", "config_types", "-t", multiple=True, required=True, help="Target exactly one config type.")
@click.option("--yes", "yes", "-y", is_flag=True, help="Overwrite without prompting.")
@click.pass_context
def save_env(ctx: click.Context, name: str, config_types: tuple[str, ...], yes: bool):
    """Save current active values as a named profile."""
    config_cls = _require_one(config_types, "save")
    name = normalize_profile_name(name)
    store = _store(ctx)
    target = store.profile_path(config_cls, name)
    if target.exists() and not yes and not click.confirm(f"Profile '{name}' exists. Overwrite?", default=False):
        raise click.Abort()
    _load_all(ctx)
    store.save_profile(config_cls, name)
    click.echo(f"Saved current {config_cls.get_storage_name()} configuration to profile '{target.name}'")


@cli.command(name="use")
@click.argument("name")
@click.option("--type", "config_types", "-t", multiple=True, required=True, help="Target exactly one config type.")
@click.pass_context
def use_env(ctx: click.Context, name: str, config_types: tuple[str, ...]):
    """Activate a named profile for one config type."""
    config_cls = _require_one(config_types, "use")
    target = _store(ctx).use_profile(config_cls, name)
    click.echo(f"Activated {config_cls.get_storage_name()} profile '{Path(target).name}'")


@cli.command(name="delete")
@click.argument("name")
@click.option("--type", "config_types", "-t", multiple=True, required=True, help="Target exactly one config type.")
@click.option("--yes", "yes", "-y", is_flag=True, help="Delete without prompting.")
@click.pass_context
def delete_env(ctx: click.Context, name: str, config_types: tuple[str, ...], yes: bool):
    """Delete a named profile for one config type."""
    config_cls = _require_one(config_types, "delete")
    if not yes and not click.confirm(f"Delete {config_cls.get_storage_name()} profile '{name}'?", default=False):
        raise click.Abort()
    target = _store(ctx).delete_profile(config_cls, name)
    click.echo(f"Deleted {config_cls.get_storage_name()} profile '{target.name}'")


@cli.command(name="set")
@click.argument("key_value")
@click.pass_context
def set_env(ctx: click.Context, key_value: str):
    """Set a configuration value in the matching active typed env file."""
    if "=" not in key_value:
        raise click.ClickException("Invalid format. Use KEY=VALUE")
    key, value = key_value.split("=", 1)
    _load_all(ctx)
    match = BaseEnvConfig.find_field(key.strip())
    if match is None:
        raise click.ClickException(f"Key '{key.strip()}' not found")
    config_cls, _ = match
    BaseEnvConfig.set(key.strip(), value.strip())
    _write_active(ctx, config_cls)
    click.echo(f"Set {key.strip()}={value.strip()}")


@cli.command(name="get")
@click.argument("key")
@click.pass_context
def get_env(ctx: click.Context, key: str):
    """Get a configuration value from active typed env files."""
    _load_all(ctx)
    match = BaseEnvConfig.find_field(key)
    if match is None:
        raise click.ClickException(f"Key '{key}' not found")
    _, field = match
    click.echo("" if field.value is None else field.value)


@cli.command(name="unset")
@click.argument("key")
@click.pass_context
def unset_env(ctx: click.Context, key: str):
    """Unset a configuration value in the matching active typed env file."""
    _load_all(ctx)
    match = BaseEnvConfig.find_field(key)
    if match is None:
        raise click.ClickException(f"Key '{key}' not found")
    config_cls, _ = match
    BaseEnvConfig.set(key, "")
    _write_active(ctx, config_cls)
    click.echo(f"Unset {key}")


def _read_paste_text(value: str | None, read_stdin: bool) -> str:
    if value is not None and read_stdin:
        raise click.ClickException("--value and --stdin cannot be used together.")
    if value is not None:
        return value
    if read_stdin:
        return sys.stdin.read()
    click.echo("Paste env text. Finish with an empty line:")
    lines: list[str] = []
    while True:
        line = click.prompt(">", default="", show_default=False)
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def _summarize_paste(result: PasteResult) -> None:
    click.echo(
        f"Parsed {result.recognized_count} recognized value{'s' if result.recognized_count != 1 else ''} "
        f"in {len(result.grouped)} config type{'s' if len(result.grouped) != 1 else ''}:"
    )
    for config_cls, values in result.grouped.items():
        click.echo(f"- {config_cls.get_storage_name()}")
        for field, value in iter_fields_for_values(config_cls, values):
            shown = mask_secret(value) if field.is_sensitive else value
            click.echo(f"  - {field.env_key}='{shown}'")
    if result.unknown:
        click.echo(f"Ignored {len(result.unknown)} unknown key{'s' if len(result.unknown) != 1 else ''}:")
        for key in result.unknown:
            click.echo(f"- {key}")


def _apply_values(grouped: dict[type[BaseEnvConfig], dict[str, str]]) -> None:
    for config_cls, values in grouped.items():
        fields_by_key = {field.env_key: field for field in config_cls.get_fields().values()}
        for key, value in values.items():
            field = fields_by_key.get(key)
            if field is not None:
                field.value = value


@cli.command(name="paste")
@click.option("--value", help="Paste content passed as an argument.")
@click.option("--stdin", "read_stdin", is_flag=True, help="Read paste content from stdin.")
@click.option("--profile", help="Write to same-named typed profiles instead of active .env files.")
@click.option("--yes", "yes", "-y", is_flag=True, help="Confirm write operations without prompting.")
@click.pass_context
def paste_env(ctx: click.Context, value: str | None, read_stdin: bool, profile: str | None, yes: bool):
    """Paste loose env text and import recognized keys."""
    result = parse_pasted_env_text(_read_paste_text(value, read_stdin))
    if not result.grouped:
        raise click.ClickException("No registered configuration keys found in pasted text.")
    _summarize_paste(result)

    profile_name = normalize_profile_name(profile) if profile else None
    if not profile_name and not yes and sys.stdin.isatty():
        prompt = click.prompt("Profile name (blank writes active .env)", default="", show_default=False)
        profile_name = normalize_profile_name(prompt) if prompt.strip() else None
    target_desc = f"profile '{profile_name}.env'" if profile_name else "active env files"
    if not yes and not click.confirm(f"Write parsed values to {target_desc} for {len(result.grouped)} config type(s)?", default=False):
        raise click.Abort()

    _load_all(ctx)
    _apply_values(result.grouped)
    store = _store(ctx)
    click.echo("Written values:")
    for config_cls, values in result.grouped.items():
        target = store.save_profile(config_cls, profile_name) if profile_name else store.save_active(config_cls)
        click.echo(f"- {config_cls.get_storage_name()}: {target}")
        for field, _ in iter_fields_for_values(config_cls, values):
            click.echo(f"  - {field.env_key}")
    click.echo(f"Configuration saved to {_envs_dir(ctx)}")


def _legacy_chattool_config_dir() -> Path:
    if os.getenv("CHATTOOL_CONFIG_DIR"):
        return Path(os.environ["CHATTOOL_CONFIG_DIR"]).expanduser()
    try:
        import platformdirs

        return Path(platformdirs.user_config_dir("chattool"))
    except Exception:
        return Path("~/.config/chattool").expanduser()


@cli.group(name="migrate")
def migrate_group():
    """Migration helpers."""


@migrate_group.command(name="chattool")
@click.option("--source", type=click.Path(file_okay=False, path_type=Path), help="Old ChatTool config directory.")
@click.option("--execute", is_flag=True, help="Copy files. Without this, only show a dry run.")
@click.option("--yes", "yes", "-y", is_flag=True, help="Overwrite without prompting.")
@click.pass_context
def migrate_chattool(ctx: click.Context, source: Path | None, execute: bool, yes: bool):
    """Migrate old ChatTool envs into $CHATARCH_HOME/envs."""
    source_dir = source or _legacy_chattool_config_dir()
    source_envs = source_dir / "envs"
    target_envs = _envs_dir(ctx)
    if not source_envs.exists():
        raise click.ClickException(f"Source envs directory not found: {source_envs}")
    files = [path for path in source_envs.rglob("*.env") if path.is_file()]
    legacy_dotenv = source_dir / ".env"
    if legacy_dotenv.exists():
        files.append(legacy_dotenv)
    if not files:
        click.echo(f"No env files found under {source_envs}")
        return
    click.echo(f"Migrate ChatTool env files from {source_dir} to {target_envs}")
    for src in files:
        rel = src.relative_to(source_dir) if src != legacy_dotenv else Path(".env")
        dst = target_envs / rel.relative_to("envs") if rel.parts and rel.parts[0] == "envs" else target_envs / "legacy.env"
        click.echo(f"- {src} -> {dst}")
    if not execute:
        click.echo("Dry run only. Re-run with --execute to copy files.")
        return
    if not yes and not click.confirm("Copy these files now?", default=False):
        raise click.Abort()
    for src in files:
        rel = src.relative_to(source_dir) if src != legacy_dotenv else Path(".env")
        dst = target_envs / rel.relative_to("envs") if rel.parts and rel.parts[0] == "envs" else target_envs / "legacy.env"
        if dst.exists() and not yes and not click.confirm(f"Overwrite {dst}?", default=False):
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
    click.echo(f"Migration completed: {target_envs}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()

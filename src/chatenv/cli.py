from __future__ import annotations

import sys
import os
from pathlib import Path
import click

from chatstyle import (
    BACK_VALUE,
    CommandField,
    CommandSchema,
    abort_if_force_without_tty,
    add_interactive_option,
    ask_confirm,
    ask_select,
    ask_text,
    create_choice,
    resolve_command_inputs as _chatstyle_resolve_command_inputs,
    resolve_interactive_mode as _chatstyle_resolve_interactive_mode,
)

from .discovery import load_config_providers
from .fields import BaseEnvConfig, EnvField, normalize_profile_name
from .paste import iter_fields_for_values, parse_pasted_env_text
from .paths import get_paths
from .registry import resolve_config_types
from .store import EnvStore
from .utils import mask_secret


PROFILE_NAME_SCHEMA = CommandSchema(
    name="chatenv-profile-name",
    fields=(CommandField("name", prompt="profile name", required=True),),
)

NEW_PROFILE_NAME_SCHEMA = CommandSchema(
    name="chatenv-new-profile-name",
    fields=(CommandField("name", prompt="New profile name", required=True),),
)

KEY_SCHEMA = CommandSchema(
    name="chatenv-key",
    fields=(CommandField("key", prompt="key", required=True),),
)

KEY_VALUE_SCHEMA = CommandSchema(
    name="chatenv-key-value",
    fields=(CommandField("key_value", prompt="KEY=VALUE", required=True),),
)

TEST_TARGET_SCHEMA = CommandSchema(
    name="chatenv-test-target",
    fields=(CommandField("target", prompt="target", required=True),),
)


AUTO_PROMPT_ENV_VAR = "CHATARCH_AUTO_PROMPT"
FALSE_VALUES = {"0", "false", "no", "off"}


def auto_prompt_enabled() -> bool:
    value = os.getenv(AUTO_PROMPT_ENV_VAR)
    if value is None:
        return True
    return value.strip().lower() not in FALSE_VALUES


def resolve_interactive_mode(
    interactive,
    *,
    auto_prompt_condition,
    respect_auto_prompt_env: bool = False,
):
    effective_auto_prompt_condition = auto_prompt_condition
    if respect_auto_prompt_env:
        effective_auto_prompt_condition = auto_prompt_condition and auto_prompt_enabled()
    return _chatstyle_resolve_interactive_mode(
        interactive,
        auto_prompt_condition=effective_auto_prompt_condition,
    )


def _resolve_required_input_interactive_mode(interactive, *, auto_prompt_condition):
    return resolve_interactive_mode(
        interactive,
        auto_prompt_condition=auto_prompt_condition,
        respect_auto_prompt_env=True,
    )


def resolve_command_inputs(*, schema, provided, interactive, usage):
    return _chatstyle_resolve_command_inputs(
        schema=schema,
        provided=provided,
        interactive=interactive,
        usage=usage,
        interactive_resolver_override=_resolve_required_input_interactive_mode,
    )


COMMAND_ORDER = [
    "init",
    "new",
    "paste",
    "use",
    "list",
    "cat",
    "get",
    "set",
    "save",
    "delete",
    "test",
]


class OrderedGroup(click.Group):
    def list_commands(self, ctx: click.Context) -> list[str]:
        commands = set(self.commands)
        ordered = [name for name in COMMAND_ORDER if name in commands]
        ordered.extend(sorted(commands.difference(ordered)))
        return ordered


@click.group(name="chatenv", cls=OrderedGroup)
@click.option("--home", type=click.Path(file_okay=False, path_type=Path), help="Override CHATARCH_HOME for this command.")
@click.pass_context
def cli(ctx: click.Context, home: Path | None):
    """Manage typed env profiles under $CHATARCH_HOME/envs."""
    load_config_providers()
    paths = get_paths(home)
    ctx.obj = {"paths": paths, "store": EnvStore(paths.envs_dir)}


def _store(ctx: click.Context) -> EnvStore:
    return ctx.obj["store"]


def _envs_dir(ctx: click.Context) -> Path:
    return ctx.obj["paths"].envs_dir


def _matched_or_all(config_types: tuple[str, ...]) -> list[type[BaseEnvConfig]]:
    return _ordered_config_classes(resolve_config_types(config_types)) if config_types else _ordered_config_classes()


def _ensure_registered() -> None:
    if not BaseEnvConfig._registry:
        raise click.ClickException(
            "No configuration schemas registered. Import/register project schemas before using chatenv commands."
        )


def _require_one(config_types: tuple[str, ...], action: str) -> type[BaseEnvConfig]:
    matched = _resolve_config_types_or_prompt(
        config_types=config_types,
        action=action,
        interactive=False,
        allow_multi=False,
    )
    return matched[0]


def _ordered_config_classes(
    configs: list[type[BaseEnvConfig]] | None = None,
) -> list[type[BaseEnvConfig]]:
    registry = list(BaseEnvConfig._registry)
    target_configs = registry if configs is None else list(configs)
    registry_index = {config_cls: index for index, config_cls in enumerate(registry)}

    def sort_key(config_cls: type[BaseEnvConfig]) -> tuple[int, int]:
        default_order = registry_index.get(config_cls, len(registry))
        return int(getattr(config_cls, "_order", default_order)), default_order

    return sorted(target_configs, key=sort_key)


def _config_choice_title(config_cls: type[BaseEnvConfig]) -> str:
    aliases = getattr(config_cls, "_aliases", [])
    alias_text = f" ({', '.join(aliases)})" if aliases else ""
    return f"{config_cls.get_storage_name()}{alias_text}"


def _available_config_types_message() -> str:
    lines = ["Available types (and aliases):"]
    for config_cls in _ordered_config_classes():
        lines.append(f"  - {_config_choice_title(config_cls)}")
    return "\n".join(lines)


def _select_config_interactive(
    *,
    action: str,
    configs: list[type[BaseEnvConfig]] | None = None,
) -> type[BaseEnvConfig]:
    choices = [
        create_choice(title=_config_choice_title(config_cls), value=config_cls)
        for config_cls in _ordered_config_classes(configs)
    ]
    selected = ask_select(f"Select one config type for {action}:", choices=choices)
    if selected == BACK_VALUE:
        raise click.Abort()
    return selected


def _resolve_config_types_or_prompt(
    *,
    config_types: tuple[str, ...],
    action: str,
    interactive: bool | None,
    allow_multi: bool,
) -> list[type[BaseEnvConfig]]:
    _ensure_registered()
    usage = f"Usage: chatenv {action} [-t TYPE] [-i|-I]"
    matched = _ordered_config_classes(resolve_config_types(config_types) or [])
    needs_selection = not config_types or not matched or (not allow_multi and len(matched) != 1)
    resolution = resolve_interactive_mode(
        interactive,
        auto_prompt_condition=needs_selection,
        respect_auto_prompt_env=True,
    )
    abort_if_force_without_tty(
        resolution.force_interactive,
        resolution.can_prompt,
        usage,
    )

    if config_types and matched and (allow_multi or len(matched) == 1):
        return matched

    if resolution.need_prompt:
        if config_types and not matched:
            click.echo(f"No configuration types matched: {', '.join(config_types)}")
        elif config_types and len(matched) != 1:
            names = ", ".join(config_cls.get_storage_name() for config_cls in matched)
            click.echo(f"{action} requires exactly one config type. Matched: {names}")
        selectable = matched if config_types and len(matched) > 1 else None
        return [_select_config_interactive(action=action, configs=selectable)]

    if not config_types and allow_multi:
        return list(BaseEnvConfig._registry)
    if not config_types:
        raise click.ClickException(
            f"{action} requires --type/-t outside interactive mode.\n{_available_config_types_message()}"
        )
    if not matched:
        raise click.ClickException(
            f"No configuration types matched: {', '.join(config_types)}\n{_available_config_types_message()}"
        )
    names = ", ".join(config_cls.get_storage_name() for config_cls in matched)
    raise click.ClickException(
        f"{action} requires exactly one config type. Matched: {names}\n{_available_config_types_message()}"
    )


def _resolve_profile_name(
    *,
    name: str | None,
    action: str,
    interactive: bool | None,
    schema: CommandSchema = PROFILE_NAME_SCHEMA,
) -> str:
    inputs = resolve_command_inputs(
        schema=schema,
        provided={"name": name},
        interactive=interactive,
        usage=f"Usage: chatenv {action} [NAME] -t TYPE [-i|-I]",
    )
    return normalize_profile_name(inputs["name"])


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
            value = ask_text(
                f"{prompt}{suffix}",
                default="",
                password=True,
            )
            if value:
                field.value = value
        else:
            value = ask_text(
                prompt,
                default="" if default_value is None else str(default_value),
            )
            if value:
                field.value = value


@cli.command(name="init")
@click.option("--type", "config_types", "-t", multiple=True, help="Filter config types by title, storage name, or alias.")
@click.option("--interactive/--no-interactive", "interactive", "-i/-I", default=None, help="Auto prompt by default, -i forces interactive, -I disables interactive.")
@click.pass_context
def init_env(ctx: click.Context, config_types: tuple[str, ...], interactive: bool | None):
    """Create or update active typed env files."""
    configs = _resolve_config_types_or_prompt(
        config_types=config_types,
        action="init",
        interactive=interactive,
        allow_multi=True,
    )
    _load_all(ctx)
    resolution = resolve_interactive_mode(
        interactive,
        auto_prompt_condition=True,
    )
    abort_if_force_without_tty(
        resolution.force_interactive,
        resolution.can_prompt,
        "Usage: chatenv init [-t TYPE] [-i|-I]",
    )
    if resolution.need_prompt:
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
    _ensure_registered()
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
    _ensure_registered()
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
@click.argument("name", required=False)
@click.option("--type", "config_types", "-t", multiple=True, help="Target exactly one config type.")
@click.option("--yes", "yes", "-y", is_flag=True, help="Overwrite without prompting.")
@click.pass_context
@add_interactive_option
def new_env(ctx: click.Context, name: str | None, config_types: tuple[str, ...], yes: bool, interactive: bool | None):
    """Create a named typed profile without activating it."""
    config_cls = _resolve_config_types_or_prompt(
        config_types=config_types,
        action="new",
        interactive=interactive,
        allow_multi=False,
    )[0]
    prompt_for_values = name is None
    name = _resolve_profile_name(
        name=name,
        action="new",
        interactive=interactive,
        schema=NEW_PROFILE_NAME_SCHEMA,
    )
    store = _store(ctx)
    target = store.profile_path(config_cls, name)
    if target.exists() and not yes and not ask_confirm(f"Profile '{name}' already exists. Overwrite it?", default=False):
        raise click.Abort()
    _load_all(ctx)
    if prompt_for_values:
        _configure_fields(config_cls)
    store.save_profile(config_cls, name)
    click.echo(f"Created {config_cls.get_storage_name()} profile '{target.name}'")


@cli.command(name="save")
@click.argument("name", required=False)
@click.option("--type", "config_types", "-t", multiple=True, help="Target exactly one config type.")
@click.option("--yes", "yes", "-y", is_flag=True, help="Overwrite without prompting.")
@click.pass_context
@add_interactive_option
def save_env(ctx: click.Context, name: str | None, config_types: tuple[str, ...], yes: bool, interactive: bool | None):
    """Save current active values as a named profile."""
    config_cls = _resolve_config_types_or_prompt(
        config_types=config_types,
        action="save",
        interactive=interactive,
        allow_multi=False,
    )[0]
    name = _resolve_profile_name(name=name, action="save", interactive=interactive)
    store = _store(ctx)
    target = store.profile_path(config_cls, name)
    if target.exists() and not yes and not ask_confirm(f"Profile '{name}' already exists. Overwrite?", default=False):
        raise click.Abort()
    _load_all(ctx)
    store.save_profile(config_cls, name)
    click.echo(f"Saved current {config_cls.get_storage_name()} configuration to profile '{target.name}'")


@cli.command(name="use")
@click.argument("name", required=False)
@click.option("--type", "config_types", "-t", multiple=True, help="Target exactly one config type.")
@click.pass_context
@add_interactive_option
def use_env(ctx: click.Context, name: str | None, config_types: tuple[str, ...], interactive: bool | None):
    """Activate a named profile for one config type."""
    config_cls = _resolve_config_types_or_prompt(
        config_types=config_types,
        action="use",
        interactive=interactive,
        allow_multi=False,
    )[0]
    name = _resolve_profile_name(name=name, action="use", interactive=interactive)
    try:
        target = _store(ctx).use_profile(config_cls, name)
    except FileNotFoundError:
        click.echo(f"Error: Profile '{name}' not found.", err=True)
        return
    click.echo(f"Activated {config_cls.get_storage_name()} profile '{Path(target).name}'")


@cli.command(name="delete")
@click.argument("name", required=False)
@click.option("--type", "config_types", "-t", multiple=True, help="Target exactly one config type.")
@click.option("--yes", "yes", "-y", is_flag=True, help="Delete without prompting.")
@click.pass_context
@add_interactive_option
def delete_env(ctx: click.Context, name: str | None, config_types: tuple[str, ...], yes: bool, interactive: bool | None):
    """Delete a named profile for one config type."""
    config_cls = _resolve_config_types_or_prompt(
        config_types=config_types,
        action="delete",
        interactive=interactive,
        allow_multi=False,
    )[0]
    name = _resolve_profile_name(name=name, action="delete", interactive=interactive)
    target = _store(ctx).profile_path(config_cls, name)
    if not target.exists():
        click.echo(f"Error: Profile '{name}' not found.", err=True)
        return
    if not yes and not ask_confirm(f"Delete {config_cls.get_storage_name()} profile '{target.name}'?", default=False):
        raise click.Abort()
    try:
        target = _store(ctx).delete_profile(config_cls, name)
    except FileNotFoundError:
        click.echo(f"Error: Profile '{name}' not found.", err=True)
        return
    click.echo(f"Deleted {config_cls.get_storage_name()} profile '{target.name}'")


@cli.command(name="set")
@click.argument("key_value", required=False)
@click.pass_context
@add_interactive_option
def set_env(ctx: click.Context, key_value: str | None, interactive: bool | None):
    """Set a configuration value in the matching active typed env file."""
    inputs = resolve_command_inputs(
        schema=KEY_VALUE_SCHEMA,
        provided={"key_value": key_value},
        interactive=interactive,
        usage="Usage: chatenv set [KEY=VALUE] [-i|-I]",
    )
    key_value = inputs["key_value"]
    if "=" not in key_value:
        click.echo("Error: Invalid format. Use KEY=VALUE", err=True)
        return
    key, value = key_value.split("=", 1)
    _load_all(ctx)
    match = BaseEnvConfig.find_field(key.strip())
    if match is None:
        click.echo(f"Error: Key '{key.strip()}' not found", err=True)
        return
    config_cls, _ = match
    BaseEnvConfig.set(key.strip(), value.strip())
    _write_active(ctx, config_cls)
    click.echo(f"Set {key.strip()}={value.strip()}")


@cli.command(name="get")
@click.argument("key", required=False)
@click.pass_context
@add_interactive_option
def get_env(ctx: click.Context, key: str | None, interactive: bool | None):
    """Get a configuration value from active typed env files."""
    inputs = resolve_command_inputs(
        schema=KEY_SCHEMA,
        provided={"key": key},
        interactive=interactive,
        usage="Usage: chatenv get [KEY] [-i|-I]",
    )
    key = inputs["key"]
    _load_all(ctx)
    match = BaseEnvConfig.find_field(key)
    if match is None:
        click.echo(f"Error: Key '{key}' not found", err=True)
        return
    _, field = match
    click.echo("" if field.value is None else field.value)


@cli.command(name="test")
@click.option("--target", "-t", required=False, help="Target service to test.")
@add_interactive_option
def test_env(target: str | None, interactive: bool | None):
    """Test a registered configuration schema."""
    load_config_providers()
    inputs = resolve_command_inputs(
        schema=TEST_TARGET_SCHEMA,
        provided={"target": target},
        interactive=interactive,
        usage="Usage: chatenv test --target TEXT [-i|-I]",
    )
    target = inputs["target"]
    config_cls = BaseEnvConfig.get_config_by_alias(target)
    if config_cls is None:
        click.echo(f"❌ Unknown target: {target}", err=True)
        click.echo("Available targets:")
        for cls in BaseEnvConfig._registry:
            aliases = ", ".join(cls._aliases)
            click.echo(f"  - {cls._title}: {aliases}")
        raise click.Abort()
    config_cls.test()


def _read_paste_text(value: str | None, read_stdin: bool, interactive: bool | None) -> str:
    if value is not None and read_stdin:
        raise click.ClickException("--value and --stdin cannot be used together.")
    if value is not None:
        return value
    if read_stdin:
        return sys.stdin.read()
    resolution = resolve_interactive_mode(
        interactive,
        auto_prompt_condition=True,
        respect_auto_prompt_env=True,
    )
    abort_if_force_without_tty(
        resolution.force_interactive,
        resolution.can_prompt,
        "Usage: chatenv paste [--value TEXT | --stdin] [--profile NAME] [-i|-I]",
    )
    if not resolution.need_prompt:
        raise click.ClickException(
            "paste requires --value or --stdin outside interactive mode."
        )
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


def _confirm_paste_write(yes: bool, message: str, interactive: bool | None) -> None:
    if yes:
        return
    resolution = resolve_interactive_mode(interactive, auto_prompt_condition=True)
    abort_if_force_without_tty(
        resolution.force_interactive,
        resolution.can_prompt,
        "Usage: chatenv paste [--value TEXT | --stdin] [--profile NAME] [-i|-I]",
    )
    if not resolution.need_prompt:
        raise click.ClickException("paste requires --yes outside interactive mode.")
    if not ask_confirm(message, default=False):
        raise click.Abort()


def _resolve_paste_profile(profile: str | None, yes: bool, interactive: bool | None) -> str | None:
    if profile:
        return normalize_profile_name(profile)
    if yes:
        return None
    resolution = resolve_interactive_mode(interactive, auto_prompt_condition=True)
    abort_if_force_without_tty(
        resolution.force_interactive,
        resolution.can_prompt,
        "Usage: chatenv paste [--value TEXT | --stdin] [--profile NAME] [-i|-I]",
    )
    if not resolution.need_prompt:
        return None
    profile_name = ask_text("Profile name (leave blank to write active .env)", default="")
    if profile_name == BACK_VALUE:
        raise click.Abort()
    profile_name = str(profile_name).strip()
    return normalize_profile_name(profile_name) if profile_name else None


@cli.command(name="paste")
@click.option("--value", help="Paste content passed as an argument.")
@click.option("--stdin", "read_stdin", is_flag=True, help="Read paste content from stdin.")
@click.option("--profile", help="Write to same-named typed profiles instead of active .env files.")
@click.option("--yes", "yes", "-y", is_flag=True, help="Confirm write operations without prompting.")
@click.pass_context
@add_interactive_option
def paste_env(ctx: click.Context, value: str | None, read_stdin: bool, profile: str | None, yes: bool, interactive: bool | None):
    """Paste loose env text and import recognized keys."""
    result = parse_pasted_env_text(_read_paste_text(value, read_stdin, interactive))
    if not result.grouped:
        if result.unknown:
            click.echo(f"Ignored {len(result.unknown)} unknown key{'s' if len(result.unknown) != 1 else ''}:")
            for key in result.unknown:
                click.echo(f"- {key}")
        raise click.ClickException("No registered configuration keys found in pasted text.")
    _summarize_paste(result)

    profile_name = _resolve_paste_profile(profile, yes, interactive)
    target_desc = f"profile '{profile_name}.env'" if profile_name else "active env files"
    if profile_name:
        existing = [
            (config_cls, _store(ctx).profile_path(config_cls, profile_name))
            for config_cls in result.grouped
            if _store(ctx).profile_path(config_cls, profile_name).exists()
        ]
        if existing:
            click.echo("Existing profiles will be overwritten:")
            for config_cls, target_path in existing:
                click.echo(f"- {config_cls.get_storage_name()}: {target_path}")
    _confirm_paste_write(
        yes,
        f"Write parsed values to {target_desc} for {len(result.grouped)} config type(s)?",
        interactive,
    )

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


def main() -> None:
    cli()


if __name__ == "__main__":
    main()

from types import SimpleNamespace

from click.testing import CliRunner
import chatenv.cli as cli_module
from chatenv.cli import cli
from chatenv.fields import BaseEnvConfig, EnvField
from chatenv.paste import parse_pasted_env_text
from chatenv.paths import get_paths
from chatenv.store import EnvStore


class UnitConfig(BaseEnvConfig):
    _title = "Unit Configuration"
    _aliases = ["unit"]
    _storage_dir = "Unit"

    UNIT_KEY = EnvField("UNIT_KEY", is_sensitive=True)
    UNIT_VALUE = EnvField("UNIT_VALUE", default="default")


def test_paths_only_use_chatarch_home(monkeypatch, tmp_path):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "arch"))
    paths = get_paths()
    assert paths.home_dir == (tmp_path / "arch").resolve()
    assert paths.envs_dir == (tmp_path / "arch" / "envs").resolve()


def test_store_profile_roundtrip(tmp_path):
    store = EnvStore(tmp_path / "envs")
    UnitConfig.load_from_sources(env_values={"UNIT_KEY": "secret", "UNIT_VALUE": "x"})
    profile = store.save_profile(UnitConfig, "work")
    assert profile.name == "work.env"
    assert store.list_profiles(UnitConfig) == ["work"]
    store.use_profile(UnitConfig, "work")
    values = store.load_active(UnitConfig)
    assert values["UNIT_KEY"] == "secret"
    assert values["UNIT_VALUE"] == "x"


def test_base_env_config_compat_helpers(tmp_path, capsys):
    assert BaseEnvConfig.get_config_by_alias("unit") is UnitConfig
    assert BaseEnvConfig.get_config_by_alias("Unit") is UnitConfig

    UnitConfig.load_from_sources(env_values={"UNIT_KEY": "secret", "UNIT_VALUE": "x"})
    BaseEnvConfig.save_env_file(tmp_path / "envs")
    assert (tmp_path / "envs" / "Unit" / ".env").exists()

    BaseEnvConfig.print_config()
    output = capsys.readouterr().out
    assert "Unit Configuration" in output
    assert "UNIT_KEY" in output
    assert "secret" not in output


def test_paste_parser_extracts_from_loose_terminal_text():
    text = """
    > chatenv paste
    >: UNIT_VALUE='from-paste'
    UNIT_KEY='sk-abcdefghijklmnopqrstuvwxyz123456'
    junk UNKNOWN_KEY=nope
    """
    result = parse_pasted_env_text(text)
    assert result.grouped[UnitConfig]["UNIT_VALUE"] == "from-paste"
    assert result.grouped[UnitConfig]["UNIT_KEY"].startswith("sk-")
    assert result.unknown == ["UNKNOWN_KEY"]


def test_cli_paste_active_and_cat(tmp_path):
    runner = CliRunner()
    home = tmp_path / "arch"
    value = "UNIT_VALUE='from-cli'\nUNIT_KEY='sk-abcdefghijklmnopqrstuvwxyz123456'\n"
    result = runner.invoke(cli, ["--home", str(home), "paste", "--value", value, "--yes"])
    assert result.exit_code == 0, result.output
    assert "Written values" in result.output
    assert (home / "envs" / "Unit" / ".env").exists()

    cat = runner.invoke(cli, ["--home", str(home), "cat", "-t", "unit"])
    assert cat.exit_code == 0, cat.output
    assert "UNIT_VALUE='from-cli'" in cat.output
    assert "sk-abcde" in cat.output
    assert "123456" in cat.output
    assert "abcdefghijklmnopqrstuvwxyz" not in cat.output


def test_cli_delete_profile_requires_confirmation(tmp_path):
    runner = CliRunner()
    home = tmp_path / "arch"
    store = EnvStore(home / "envs")
    UnitConfig.load_from_sources(env_values={"UNIT_KEY": "secret", "UNIT_VALUE": "x"})
    profile = store.save_profile(UnitConfig, "work")

    declined = runner.invoke(
        cli,
        ["--home", str(home), "delete", "-t", "unit", "work"],
        input="n\n",
    )
    assert declined.exit_code != 0
    assert profile.exists()

    confirmed = runner.invoke(
        cli,
        ["--home", str(home), "delete", "-t", "unit", "work"],
        input="y\n",
    )
    assert confirmed.exit_code == 0, confirmed.output
    assert not profile.exists()


def _interactive_resolution(interactive=None, *, auto_prompt_condition=True, **kwargs):
    return SimpleNamespace(
        interactive=interactive,
        can_prompt=True,
        force_interactive=interactive is True,
        need_prompt=True,
    )


def _tty_resolution(interactive=None, *, auto_prompt_condition=True):
    return SimpleNamespace(
        interactive=interactive,
        can_prompt=True,
        force_interactive=interactive is True,
        need_prompt=interactive is True or (interactive is None and auto_prompt_condition),
    )


def test_chatenv_auto_prompt_env_false_disables_implicit_prompt(monkeypatch):
    monkeypatch.setenv("CHATARCH_AUTO_PROMPT", "false")
    monkeypatch.setattr(
        "chatenv.cli._chatstyle_resolve_interactive_mode",
        _tty_resolution,
    )

    resolution = cli_module.resolve_interactive_mode(
        None,
        auto_prompt_condition=True,
        respect_auto_prompt_env=True,
    )

    assert resolution.can_prompt is True
    assert resolution.force_interactive is False
    assert resolution.need_prompt is False


def test_chatenv_auto_prompt_env_false_keeps_force_interactive(monkeypatch):
    monkeypatch.setenv("CHATARCH_AUTO_PROMPT", "false")
    monkeypatch.setattr(
        "chatenv.cli._chatstyle_resolve_interactive_mode",
        _tty_resolution,
    )

    resolution = cli_module.resolve_interactive_mode(
        True,
        auto_prompt_condition=True,
        respect_auto_prompt_env=True,
    )

    assert resolution.force_interactive is True
    assert resolution.need_prompt is True


def test_cli_new_missing_type_errors_when_auto_prompt_disabled(
    tmp_path, monkeypatch
):
    runner = CliRunner()
    home = tmp_path / "arch"
    monkeypatch.setenv("CHATARCH_AUTO_PROMPT", "false")
    monkeypatch.setattr(
        "chatenv.cli._chatstyle_resolve_interactive_mode",
        _tty_resolution,
    )

    result = runner.invoke(cli, ["--home", str(home), "new", "work"])

    assert result.exit_code != 0
    assert "new requires --type/-t outside interactive mode" in result.output


def test_cli_get_missing_key_errors_when_auto_prompt_disabled(
    tmp_path, monkeypatch
):
    runner = CliRunner()
    home = tmp_path / "arch"
    monkeypatch.setenv("CHATARCH_AUTO_PROMPT", "false")
    monkeypatch.setattr(
        "chatenv.cli._chatstyle_resolve_interactive_mode",
        _tty_resolution,
    )

    result = runner.invoke(cli, ["--home", str(home), "get"])

    assert result.exit_code != 0
    assert "key" in result.output.lower()
    assert "required" in result.output.lower()


def test_cli_init_with_type_still_prompts_fields_when_auto_prompt_disabled(
    tmp_path, monkeypatch
):
    runner = CliRunner()
    home = tmp_path / "arch"
    monkeypatch.setenv("CHATARCH_AUTO_PROMPT", "false")
    monkeypatch.setattr(
        "chatenv.cli._chatstyle_resolve_interactive_mode",
        _tty_resolution,
    )
    monkeypatch.setattr(
        "chatenv.cli.ask_text",
        lambda prompt, default="", password=False: (
            "secret" if "UNIT_KEY" in prompt else "from-init"
        ),
    )

    result = runner.invoke(cli, ["--home", str(home), "init", "-t", "unit"])

    assert result.exit_code == 0, result.output
    env_text = (home / "envs" / "Unit" / ".env").read_text(encoding="utf-8")
    assert "UNIT_KEY='secret'" in env_text
    assert "UNIT_VALUE='from-init'" in env_text


def test_cli_new_prompts_for_config_type_when_type_missing(
    tmp_path, monkeypatch
):
    runner = CliRunner()
    home = tmp_path / "arch"
    selected_messages = []

    monkeypatch.setattr(
        "chatenv.cli.resolve_interactive_mode",
        _interactive_resolution,
    )
    monkeypatch.setattr(
        "chatenv.cli.ask_select",
        lambda message, choices: selected_messages.append(message) or UnitConfig,
    )
    monkeypatch.setattr(
        "chatenv.cli.resolve_command_inputs",
        lambda **kwargs: {"name": "work"},
    )
    monkeypatch.setattr("chatenv.cli.ask_text", lambda *args, **kwargs: "")

    result = runner.invoke(cli, ["--home", str(home), "new"])

    assert result.exit_code == 0, result.output
    assert selected_messages == ["Select one config type for new:"]
    assert (home / "envs" / "Unit" / "work.env").exists()


def test_cli_new_bad_type_shows_available_types_outside_interactive(tmp_path):
    runner = CliRunner()
    home = tmp_path / "arch"

    result = runner.invoke(
        cli,
        ["--home", str(home), "new", "-t", "missing", "work", "-I"],
    )

    assert result.exit_code != 0
    assert "No configuration types matched: missing" in result.output
    assert "Available types (and aliases):" in result.output
    assert "Unit (unit)" in result.output


def test_cli_init_prompts_for_config_type_when_type_missing(
    tmp_path, monkeypatch
):
    runner = CliRunner()
    home = tmp_path / "arch"
    selected_messages = []

    monkeypatch.setattr(
        "chatenv.cli.resolve_interactive_mode",
        _interactive_resolution,
    )
    monkeypatch.setattr(
        "chatenv.cli.ask_select",
        lambda message, choices: selected_messages.append(message) or UnitConfig,
    )
    monkeypatch.setattr(
        "chatenv.cli.ask_text",
        lambda prompt, default="", password=False: (
            "secret" if "UNIT_KEY" in prompt else "from-init"
        ),
    )

    result = runner.invoke(cli, ["--home", str(home), "init"])

    assert result.exit_code == 0, result.output
    assert selected_messages == ["Select one config type for init:"]
    env_file = home / "envs" / "Unit" / ".env"
    assert env_file.exists()
    env_text = env_file.read_text(encoding="utf-8")
    assert "UNIT_KEY='secret'" in env_text
    assert "UNIT_VALUE='from-init'" in env_text


def test_cli_help_uses_stable_command_order():
    runner = CliRunner()

    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0, result.output
    command_lines = result.output.split("Commands:", 1)[1].splitlines()
    commands = [
        line.split()[0]
        for line in command_lines
        if line.startswith("  ") and line.strip()
    ]
    assert commands == [
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
    assert "unset" not in commands

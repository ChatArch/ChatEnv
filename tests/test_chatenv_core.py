from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner
import chatenv.discovery as discovery_module
import chatenv.cli as cli_module
from chatenv.cli import cli
from chatenv.configs import FeishuConfig, OpenAIConfig
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


class RoundTripConfig(BaseEnvConfig):
    _title = "RoundTrip Configuration"
    _aliases = ["roundtrip"]
    _storage_dir = "RoundTrip"

    ROUNDTRIP_VALUE = EnvField("ROUNDTRIP_VALUE")
    ROUNDTRIP_URL = EnvField("ROUNDTRIP_URL")


def test_builtin_shared_openai_and_feishu_configs_are_registered():
    assert BaseEnvConfig.get_config_by_alias("openai") is OpenAIConfig
    assert BaseEnvConfig.get_config_by_alias("oai") is OpenAIConfig
    assert BaseEnvConfig.get_config_by_alias("feishu") is FeishuConfig
    assert BaseEnvConfig.get_config_by_alias("lark") is FeishuConfig

    assert OpenAIConfig.get_storage_name() == "OpenAI"
    assert FeishuConfig.get_storage_name() == "Feishu"
    assert "OPENAI_API_KEY" in [field.env_key for field in OpenAIConfig.get_fields().values()]
    assert "FEISHU_APP_SECRET" in [field.env_key for field in FeishuConfig.get_fields().values()]


def test_duplicate_logical_config_registration_is_skipped():
    registry_before = list(BaseEnvConfig._registry)

    class DuplicateOpenAIConfig(BaseEnvConfig):
        _title = "Duplicate OpenAI Configuration"
        _aliases = ["duplicate-openai"]
        _storage_dir = "OpenAI"

        DUPLICATE_OPENAI_KEY = EnvField("DUPLICATE_OPENAI_KEY")

    assert DuplicateOpenAIConfig not in BaseEnvConfig._registry
    assert getattr(DuplicateOpenAIConfig, "_duplicate_of") is OpenAIConfig
    assert BaseEnvConfig.get_config_by_alias("openai") is OpenAIConfig
    assert BaseEnvConfig.find_field("DUPLICATE_OPENAI_KEY") is None
    assert BaseEnvConfig._registry == registry_before


def test_duplicate_provider_config_does_not_pollute_registry(monkeypatch):
    registry_before = list(BaseEnvConfig._registry)
    provider_configs_before = discovery_module.get_provider_configs()

    class FakeEntryPoint:
        name = "legacy-chattool"
        value = "legacy_chattool.config"

        def load(self):
            class LegacyFeishuConfig(BaseEnvConfig):
                _title = "Legacy Feishu Configuration"
                _aliases = ["legacy-feishu"]
                _storage_dir = "Feishu"

                LEGACY_FEISHU_ONLY = EnvField("LEGACY_FEISHU_ONLY")

            return LegacyFeishuConfig

    monkeypatch.setattr(discovery_module, "_iter_entry_points", lambda: [FakeEntryPoint()])

    results = discovery_module.load_config_providers(force=True)

    assert len(results) == 1
    assert results[0].loaded is True
    assert results[0].configs == ()
    assert BaseEnvConfig._registry == registry_before
    assert BaseEnvConfig.get_config_by_alias("feishu") is FeishuConfig
    assert BaseEnvConfig.find_field("LEGACY_FEISHU_ONLY") is None

    discovery_module._provider_configs.clear()
    discovery_module._provider_configs.update(provider_configs_before)


def test_chatarch_internal_dependencies_have_upper_bounds():
    pyproject_text = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
        encoding="utf-8"
    )

    assert '"chatstyle>=0.1.0,<0.2.0"' in pyproject_text
    assert '"chatstyle>=0.1.0"' not in pyproject_text


def test_cli_set_only_writes_the_requested_key(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "system-secret")
    runner = CliRunner()
    home = tmp_path / "arch"

    result = runner.invoke(
        cli,
        ["--home", str(home), "set", "OPENAI_API_BASE=https://example.invalid/v1"],
    )

    assert result.exit_code == 0, result.output
    env_text = (home / "envs" / "OpenAI" / ".env").read_text(encoding="utf-8")
    assert "OPENAI_API_BASE='https://example.invalid/v1'" in env_text
    assert "OPENAI_API_KEY" not in env_text


def test_cli_paste_active_merges_file_values_without_system_env(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "system-secret")
    runner = CliRunner()
    home = tmp_path / "arch"
    openai_active = home / "envs" / "OpenAI" / ".env"
    openai_active.parent.mkdir(parents=True)
    openai_active.write_text("OPENAI_API_BASE='https://old.example/v1'\n", encoding="utf-8")

    result = runner.invoke(
        cli,
        [
            "--home",
            str(home),
            "paste",
            "--value",
            "OPENAI_API_MODEL='gpt-test'",
            "--yes",
        ],
    )

    assert result.exit_code == 0, result.output
    env_text = openai_active.read_text(encoding="utf-8")
    assert "OPENAI_API_BASE='https://old.example/v1'" in env_text
    assert "OPENAI_API_MODEL='gpt-test'" in env_text
    assert "OPENAI_API_KEY" not in env_text


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


def test_paste_parser_extracts_multiple_assignments_on_one_spaced_line():
    text = "UNIT_VALUE='hello world' UNIT_KEY='sk with spaces' UNKNOWN_KEY=nope"

    result = parse_pasted_env_text(text)

    assert result.grouped[UnitConfig]["UNIT_VALUE"] == "hello world"
    assert result.grouped[UnitConfig]["UNIT_KEY"] == "sk with spaces"
    assert result.unknown == ["UNKNOWN_KEY"]


def test_paste_parser_keeps_url_query_params_before_spaced_assignment():
    text = "UNIT_VALUE=https://api.example.test/v1?x=1 UNIT_KEY='secret'"

    result = parse_pasted_env_text(text)

    assert result.grouped[UnitConfig]["UNIT_VALUE"] == "https://api.example.test/v1?x=1"
    assert result.grouped[UnitConfig]["UNIT_KEY"] == "secret"
    assert result.unknown == []


def test_paste_parser_keeps_empty_value_before_spaced_assignment():
    text = "UNIT_VALUE= UNIT_KEY='secret'"

    result = parse_pasted_env_text(text)

    assert result.grouped[UnitConfig]["UNIT_VALUE"] == ""
    assert result.grouped[UnitConfig]["UNIT_KEY"] == "secret"


def test_paste_parser_stops_at_inline_comment_before_later_assignment():
    text = "UNIT_VALUE='hello world' # comment UNIT_KEY='secret'"

    result = parse_pasted_env_text(text)

    assert result.grouped[UnitConfig]["UNIT_VALUE"] == "hello world"
    assert "UNIT_KEY" not in result.grouped[UnitConfig]


def test_paste_parser_accepts_export_prefix_on_same_line_assignments():
    text = "export UNIT_VALUE='hello world' UNIT_KEY='secret'"

    result = parse_pasted_env_text(text)

    assert result.grouped[UnitConfig]["UNIT_VALUE"] == "hello world"
    assert result.grouped[UnitConfig]["UNIT_KEY"] == "secret"


def test_cli_paste_accepts_space_separated_assignments(tmp_path):
    runner = CliRunner()
    home = tmp_path / "arch"
    value = "UNIT_VALUE='from spaced paste' UNIT_KEY='sk with spaces'"

    result = runner.invoke(cli, ["--home", str(home), "paste", "--value", value, "--yes"])

    assert result.exit_code == 0, result.output
    env_text = (home / "envs" / "Unit" / ".env").read_text(encoding="utf-8")
    assert "UNIT_VALUE='from spaced paste'" in env_text
    assert "UNIT_KEY='sk with spaces'" in env_text


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


def test_cli_cat_output_with_blank_lines_can_be_pasted_to_profile(tmp_path):
    runner = CliRunner()
    source_home = tmp_path / "source"
    target_home = tmp_path / "target"
    value = "\n".join(
        [
            "UNIT_VALUE='hello world with spaces'",
            "UNIT_KEY='unit dummy value with spaces'",
            "ROUNDTRIP_VALUE='roundtrip value with spaces'",
            "ROUNDTRIP_URL=https://api.example.test/v1?x=1",
        ]
    )
    seed = runner.invoke(
        cli,
        ["--home", str(source_home), "paste", "--value", value, "--yes"],
    )
    assert seed.exit_code == 0, seed.output

    cat = runner.invoke(cli, ["--home", str(source_home), "cat", "--no-mask"])
    assert cat.exit_code == 0, cat.output
    assert "\n\n# RoundTrip\n" in cat.output

    imported = runner.invoke(
        cli,
        [
            "--home",
            str(target_home),
            "paste",
            "--value",
            cat.output,
            "--profile",
            "copy",
            "--yes",
        ],
    )
    assert imported.exit_code == 0, imported.output

    unit_copy = (target_home / "envs" / "Unit" / "copy.env").read_text(
        encoding="utf-8"
    )
    roundtrip_copy = (target_home / "envs" / "RoundTrip" / "copy.env").read_text(
        encoding="utf-8"
    )
    assert "UNIT_VALUE='hello world with spaces'" in unit_copy
    assert "UNIT_KEY='unit dummy value with spaces'" in unit_copy
    assert "ROUNDTRIP_VALUE='roundtrip value with spaces'" in roundtrip_copy
    assert "ROUNDTRIP_URL='https://api.example.test/v1?x=1'" in roundtrip_copy


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

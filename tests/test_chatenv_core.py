from click.testing import CliRunner

from chatenv.cli import cli
from chatenv.fields import BaseEnvConfig, EnvField
from chatenv.paste import parse_pasted_env_text
from chatenv.paths import get_paths
from chatenv.store import EnvStore
from chatenv.presets.chattool import OpenAIConfig


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


def test_paste_parser_extracts_from_loose_terminal_text():
    text = """
    > chatenv paste
    >: OPENAI_API_BASE='https://example.com/v1'
    OPENAI_API_KEY='sk-abcdefghijklmnopqrstuvwxyz123456'
    junk UNKNOWN_KEY=nope
    """
    result = parse_pasted_env_text(text)
    assert result.grouped[OpenAIConfig]["OPENAI_API_BASE"] == "https://example.com/v1"
    assert result.grouped[OpenAIConfig]["OPENAI_API_KEY"].startswith("sk-")
    assert result.unknown == ["UNKNOWN_KEY"]


def test_cli_paste_active_and_cat(tmp_path):
    runner = CliRunner()
    home = tmp_path / "arch"
    value = "OPENAI_API_BASE='https://example.com/v1'\nOPENAI_API_KEY='sk-abcdefghijklmnopqrstuvwxyz123456'\n"
    result = runner.invoke(cli, ["--home", str(home), "paste", "--value", value, "--yes"])
    assert result.exit_code == 0, result.output
    assert "Written values" in result.output
    assert (home / "envs" / "OpenAI" / ".env").exists()

    cat = runner.invoke(cli, ["--home", str(home), "cat", "-t", "oai"])
    assert cat.exit_code == 0, cat.output
    assert "OPENAI_API_BASE='https://example.com/v1'" in cat.output
    assert "sk-abcde" in cat.output
    assert "123456" in cat.output
    assert "abcdefghijklmnopqrstuvwxyz" not in cat.output

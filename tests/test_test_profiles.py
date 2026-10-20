"""Configuration test selection must not silently validate other credentials."""

import pytest
from click.testing import CliRunner

from chatenv.cli import cli
from chatenv.configs import OpenAIConfig
from chatenv.fields import BaseEnvConfig, EnvField
from chatenv.store import EnvStore


class ProbeConfig(BaseEnvConfig):
    _title = "Test Profile Probe"
    _aliases = ["profile-probe"]
    _storage_dir = "ProfileProbe"

    PROBE_SECRET = EnvField("PROFILE_PROBE_SECRET", is_sensitive=True)
    PROBE_URL = EnvField("PROFILE_PROBE_URL", default="https://default.invalid")


@pytest.fixture
def probe(monkeypatch, tmp_path):
    calls = []

    def test_config(cls):
        calls.append({name: field.value for name, field in cls.get_fields().items()})

    monkeypatch.setattr(ProbeConfig, "test", classmethod(test_config))
    monkeypatch.delenv("PROFILE_PROBE_SECRET", raising=False)
    monkeypatch.delenv("PROFILE_PROBE_URL", raising=False)
    home = tmp_path / "arch"
    return CliRunner(), home, EnvStore(home / "envs"), calls


def test_test_without_profile_loads_active_from_selected_home(probe, monkeypatch, tmp_path):
    runner, home, store, calls = probe
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "other-home"))
    monkeypatch.setenv("PROFILE_PROBE_SECRET", "process-secret")
    store.save_active(ProbeConfig, {"PROFILE_PROBE_SECRET": "active-secret"})

    result = runner.invoke(cli, ["--home", str(home), "test", "-t", "profile-probe", "-I"])

    assert result.exit_code == 0, result.output
    assert calls == [{"PROBE_SECRET": "active-secret", "PROBE_URL": "https://default.invalid"}]


def test_test_without_profile_preserves_process_fallback(probe, monkeypatch):
    runner, home, store, calls = probe
    monkeypatch.setenv("PROFILE_PROBE_SECRET", "process-secret")

    result = runner.invoke(cli, ["--home", str(home), "test", "-t", "profile-probe"])

    assert result.exit_code == 0, result.output
    assert calls[0]["PROBE_SECRET"] == "process-secret"
    assert not store.active_path(ProbeConfig).exists()


@pytest.mark.parametrize("name", ["work", "work.env"])
def test_test_named_profile_is_isolated_and_does_not_activate(probe, monkeypatch, name):
    runner, home, store, calls = probe
    active = store.save_active(ProbeConfig, {"PROFILE_PROBE_SECRET": "active-secret"})
    profile = store.save_profile(ProbeConfig, "work", {"PROFILE_PROBE_SECRET": "work-secret"})
    original_active = active.read_bytes()
    original_profile = profile.read_bytes()
    monkeypatch.setenv("PROFILE_PROBE_SECRET", "process-secret")
    monkeypatch.setenv("PROFILE_PROBE_URL", "https://process.invalid")
    monkeypatch.setattr(OpenAIConfig.OPENAI_API_KEY, "value", "unrelated-state")
    store.save_active(OpenAIConfig, {"OPENAI_API_KEY": "unrelated-file-secret"})

    result = runner.invoke(cli, ["--home", str(home), "test", "-t", "profile-probe", name])

    assert result.exit_code == 0, result.output
    assert calls == [{"PROBE_SECRET": "work-secret", "PROBE_URL": "https://default.invalid"}]
    assert active.read_bytes() == original_active
    assert profile.read_bytes() == original_profile
    assert OpenAIConfig.OPENAI_API_KEY.value == "unrelated-state"
    assert "work" in result.output
    for secret in ("work-secret", "active-secret", "process-secret"):
        assert secret not in result.output


def test_named_profile_missing_secret_does_not_reuse_other_credentials(probe, monkeypatch):
    runner, home, store, calls = probe
    store.save_active(ProbeConfig, {"PROFILE_PROBE_SECRET": "active-secret"})
    store.save_profile(ProbeConfig, "empty", {})
    monkeypatch.setenv("PROFILE_PROBE_SECRET", "process-secret")
    monkeypatch.setattr(ProbeConfig.PROBE_SECRET, "value", "previous-command-secret")

    result = runner.invoke(cli, ["--home", str(home), "test", "-t", "profile-probe", "empty"])

    assert result.exit_code == 0, result.output
    assert calls == [{"PROBE_SECRET": None, "PROBE_URL": "https://default.invalid"}]


def test_missing_named_profile_fails_without_testing_or_changing_active(probe):
    runner, home, store, calls = probe
    active = store.save_active(ProbeConfig, {"PROFILE_PROBE_SECRET": "active-secret"})
    original = active.read_bytes()

    result = runner.invoke(cli, ["--home", str(home), "test", "-t", "profile-probe", "missing"])

    assert result.exit_code != 0
    assert "missing" in result.output
    assert "not found" in result.output.lower()
    assert calls == []
    assert active.read_bytes() == original


def test_default_after_named_profile_reloads_active(probe):
    runner, home, store, calls = probe
    store.save_active(ProbeConfig, {"PROFILE_PROBE_SECRET": "active-secret"})
    store.save_profile(ProbeConfig, "work", {"PROFILE_PROBE_SECRET": "work-secret"})
    args = ["--home", str(home), "test", "-t", "profile-probe"]

    named = runner.invoke(cli, [*args, "work"])
    active = runner.invoke(cli, args)

    assert named.exit_code == 0, named.output
    assert active.exit_code == 0, active.output
    assert [call["PROBE_SECRET"] for call in calls] == ["work-secret", "active-secret"]


def test_load_from_sources_can_explicitly_disable_process_fallback(monkeypatch):
    monkeypatch.setenv("PROFILE_PROBE_SECRET", "process-secret")
    monkeypatch.setenv("PROFILE_PROBE_URL", "https://process.invalid")

    ProbeConfig.load_from_sources(env_values={}, include_process_env=False)

    assert ProbeConfig.PROBE_SECRET.value is None
    assert ProbeConfig.PROBE_URL.value == "https://default.invalid"


@pytest.mark.parametrize("args", [
    ["--profile", "work"],
    ["work", "--profile", "work"],
    ["work.env", "--profile", "work"],
])
def test_test_profile_option_accepts_legacy_and_equivalent_positionals(probe, args):
    runner, home, store, calls = probe
    store.save_profile(ProbeConfig, "work", {"PROFILE_PROBE_SECRET": "work-secret"})

    result = runner.invoke(cli, ["--home", str(home), "test", "-t", "profile-probe", *args])

    assert result.exit_code == 0, result.output
    assert calls[0]["PROBE_SECRET"] == "work-secret"


def test_conflicting_profile_option_and_positional_fail_before_test(probe):
    runner, home, store, calls = probe
    store.save_profile(ProbeConfig, "work", {"PROFILE_PROBE_SECRET": "work-secret"})
    store.save_profile(ProbeConfig, "other", {"PROFILE_PROBE_SECRET": "other-secret"})

    result = runner.invoke(cli, ["--home", str(home), "test", "-t", "profile-probe", "work", "--profile", "other"])

    assert result.exit_code != 0
    assert "conflict" in result.output.lower()
    assert calls == []


@pytest.mark.parametrize("profile_args, expected", [([], "active-secret"), (["--profile", "work"], "work-secret")])
def test_legacy_provider_loader_and_parameterless_test_still_work(probe, monkeypatch, profile_args, expected):
    runner, home, store, calls = probe
    store.save_active(ProbeConfig, {"PROFILE_PROBE_SECRET": "active-secret"})
    store.save_profile(ProbeConfig, "work", {"PROFILE_PROBE_SECRET": "work-secret"})
    monkeypatch.setenv("PROFILE_PROBE_SECRET", "process-secret")
    loader_calls = []

    def legacy_loader(cls, env_values=None, override_values=None):
        loader_calls.append(True)
        BaseEnvConfig.load_from_sources.__func__(cls, env_values, override_values)

    monkeypatch.setattr(ProbeConfig, "load_from_sources", classmethod(legacy_loader))

    result = runner.invoke(cli, ["--home", str(home), "test", "-t", "profile-probe", *profile_args])

    assert result.exit_code == 0, result.output
    assert calls[0]["PROBE_SECRET"] == expected
    assert loader_calls == ([] if profile_args else [True])


def test_store_load_config_is_reusable_without_cli(probe, monkeypatch):
    runner, home, store, calls = probe
    active = store.save_active(ProbeConfig, {"PROFILE_PROBE_SECRET": "active-secret"})
    named = store.save_profile(ProbeConfig, "work", {})
    monkeypatch.setenv("PROFILE_PROBE_SECRET", "process-secret")

    assert store.load_config(ProbeConfig) == active
    assert ProbeConfig.PROBE_SECRET.value == "active-secret"
    assert store.load_config(ProbeConfig, profile="work") == named
    assert ProbeConfig.PROBE_SECRET.value is None
    with pytest.raises(FileNotFoundError):
        store.load_config(ProbeConfig, profile="missing")


def test_named_profile_does_not_interpolate_process_credentials(probe, monkeypatch):
    runner, home, store, calls = probe
    monkeypatch.setenv("PROFILE_PROBE_SECRET", "process-secret")
    store.save_profile(ProbeConfig, "reference", {"PROFILE_PROBE_SECRET": "${PROFILE_PROBE_SECRET}"})

    result = runner.invoke(cli, ["--home", str(home), "test", "-t", "profile-probe", "--profile", "reference"])

    assert result.exit_code == 0, result.output
    assert calls[0]["PROBE_SECRET"] == "${PROFILE_PROBE_SECRET}"
    assert "process-secret" not in result.output


@pytest.mark.parametrize("profile", [".env", "..", "../Other/work", "Other\\work"])
def test_store_load_config_rejects_names_outside_target_profile(probe, profile):
    runner, home, store, calls = probe

    with pytest.raises(ValueError, match="Profile name"):
        store.load_config(ProbeConfig, profile=profile)

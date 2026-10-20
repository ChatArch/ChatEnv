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

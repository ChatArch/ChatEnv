from types import SimpleNamespace
import stat

import click
import pytest
from click.testing import CliRunner

import chatenv.cli as cli_module
from chatenv.cli import cli
from chatenv.fields import BaseEnvConfig, EnvField
from chatenv.store import EnvStore
from chatenv.utils import mask_secret

CANARY = 'DUMMY_CANARY_SECRET_VALUE_LONG_123456789'

class SecretDisplayConfig(BaseEnvConfig):
    _title = 'Secret Display Regression'
    _aliases = ['secret-display-regression']
    _storage_dir = 'SecretDisplayRegression'
    DISPLAY_PASSWORD = EnvField('DISPLAY_PASSWORD', is_sensitive=True)

@pytest.mark.parametrize('value', ['dummy', CANARY, '假密码仅测试01234567890123456789'])
def test_default_mask_is_complete(value):
    assert mask_secret(value) == '*' * len(value)

def test_zero_visibility_never_appends_original():
    assert mask_secret(CANARY, visible=0) == '*' * len(CANARY)

def test_explicit_fingerprint_remains_opt_in():
    assert mask_secret(CANARY, visible=3) == CANARY[:3] + '*' * (len(CANARY)-6) + CANARY[-3:]

def test_init_masks_existing_fragments_and_retains_on_enter(monkeypatch, tmp_path):
    home = tmp_path/'arch'
    store = EnvStore(home/'envs')
    store.save_active(SecretDisplayConfig, {'DISPLAY_PASSWORD': CANARY})
    prompts = []
    def ask(prompt, **kwargs):
        prompts.append(kwargs)
        click.echo(prompt)
        return ''
    monkeypatch.setattr(cli_module,'load_config_providers',lambda:None)
    monkeypatch.setattr(cli_module,'resolve_interactive_mode',lambda *a,**k:SimpleNamespace(force_interactive=False,can_prompt=True,need_prompt=True))
    monkeypatch.setattr(cli_module,'ask_text',ask)
    result = CliRunner().invoke(cli,['--home',str(home),'init','-t','secret-display-regression','-i'])
    assert result.exit_code == 0, result.output
    assert CANARY[:8] not in result.output and CANARY[-8:] not in result.output
    assert prompts[0]['password'] is True and prompts[0]['default'] == ''
    assert store.load_active(SecretDisplayConfig)['DISPLAY_PASSWORD'] == CANARY
    assert stat.S_IMODE(store.active_path(SecretDisplayConfig).stat().st_mode) == 0o600

def test_cat_masks_fragments_by_default(monkeypatch,tmp_path):
    home=tmp_path/'arch'
    EnvStore(home/'envs').save_active(SecretDisplayConfig,{'DISPLAY_PASSWORD':CANARY})
    monkeypatch.setattr(cli_module,'load_config_providers',lambda:None)
    result=CliRunner().invoke(cli,['--home',str(home),'cat','-t','secret-display-regression'])
    assert result.exit_code==0,result.output
    assert CANARY[:8] not in result.output and CANARY[-8:] not in result.output
    assert "DISPLAY_PASSWORD='"+'*'*len(CANARY)+"'" in result.output

def test_status_masks_sensitive_default(monkeypatch,tmp_path):
    monkeypatch.setattr(SecretDisplayConfig.DISPLAY_PASSWORD,'default',CANARY)
    monkeypatch.setattr(cli_module,'load_config_providers',lambda:None)
    result=CliRunner().invoke(cli,['--home',str(tmp_path/'arch'),'status','-t','secret-display-regression','--detail'])
    assert result.exit_code==0,result.output
    assert CANARY[:8] not in result.output and CANARY[-8:] not in result.output
    assert 'sensitive=yes' in result.output

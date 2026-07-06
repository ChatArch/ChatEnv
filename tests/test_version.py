from chatenv import __version__
from chatenv.cli import cli
from click.testing import CliRunner


def test_version_present():
    assert __version__ == "0.2.3"


def test_cli_version_option():
    result = CliRunner().invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output

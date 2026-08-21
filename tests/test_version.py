from chatenv import __version__
from chatenv.cli import cli
from click.testing import CliRunner


def test_version_present():
    assert __version__ == "0.2.9"


def test_cli_version_option():
    result = CliRunner().invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output


def test_help_lists_tree_option():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "--tree" in result.output


def test_tree_option_renders_registered_command_surface():
    result = CliRunner().invoke(cli, ["--tree"])

    assert result.exit_code == 0
    assert "chatenv [--home <HOME>]  # Manage typed env profiles" in result.output
    assert "├── --help" in result.output
    assert "├── --version" in result.output
    assert "├── --tree" in result.output
    assert "├── init" in result.output
    assert "├── new [NAME]" in result.output
    assert "├── paste" in result.output
    assert "├── use [NAME]" in result.output
    assert "├── list" in result.output
    assert "├── status" in result.output
    assert "├── token" in result.output
    assert "│   ├── status" in result.output
    assert "│   ├── refresh" in result.output
    assert "│   ├── import" in result.output
    assert "│   ├── list" in result.output
    assert "│   └── clear" in result.output
    assert "├── cat [NAME]" in result.output
    assert "├── get [KEY]" in result.output
    assert "├── set [KEY-VALUE]" in result.output
    assert "├── save [NAME]" in result.output
    assert "├── delete [NAME]" in result.output
    assert "└── test" in result.output
    assert "hello" not in result.output.lower()

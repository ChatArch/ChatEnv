from chatenv import __version__
from chatenv.cli import cli
from click.testing import CliRunner


def test_version_present():
    assert __version__ == "0.2.10"


def test_cli_version_option():
    result = CliRunner().invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output


def test_help_lists_tree_options():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "--tree" in result.output
    assert "--tree-brief" in result.output


def test_tree_option_renders_registered_command_surface():
    result = CliRunner().invoke(cli, ["--tree"])

    assert result.exit_code == 0
    assert result.output.startswith("chatenv\n")
    assert "├── --help" in result.output
    assert "├── --version" in result.output
    assert "├── --tree" in result.output
    assert "├── --tree-brief" in result.output
    assert "├── --home HOME" in result.output
    assert "├── init [--type CONFIG-TYPES]" in result.output
    assert "├── new [NAME] [--type CONFIG-TYPES]" in result.output
    assert "├── paste [--value VALUE]" in result.output
    assert "├── use [NAME] [--type CONFIG-TYPES]" in result.output
    assert "├── list" in result.output
    assert "├── status" in result.output
    assert "├── token" in result.output
    assert "│   ├── status <SERVICE> [PROFILE]" in result.output
    assert "│   ├── refresh <SERVICE> [PROFILE]" in result.output
    assert "│   ├── import <SERVICE> [PROFILE]" in result.output
    assert "│   ├── list [SERVICE]" in result.output
    assert "│   └── clear <SERVICE> [PROFILE]" in result.output
    assert "├── cat [NAME]" in result.output
    assert "├── get [KEY]" in result.output
    assert "├── set [KEY-VALUE]" in result.output
    assert "├── save [NAME]" in result.output
    assert "├── delete [NAME]" in result.output
    assert "└── test" in result.output
    assert "hello" not in result.output.lower()


def test_tree_brief_option_omits_parameter_signatures():
    result = CliRunner().invoke(cli, ["--tree-brief"])

    assert result.exit_code == 0
    assert result.output.startswith("chatenv\n")
    assert "├── --tree-brief" in result.output
    assert "├── --home  #" in result.output
    assert "├── init  #" in result.output
    assert "├── token  #" in result.output
    assert "│   ├── refresh  #" in result.output
    assert "└── test  #" in result.output
    assert "<SERVICE>" not in result.output
    assert "[PROFILE]" not in result.output
    assert "--home HOME" not in result.output

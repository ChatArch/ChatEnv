from pathlib import Path

from chatenv.cli import cli, render_cli_tree


PUBLIC_DOCS = (
    "README.md",
    "README.en.md",
    "docs/index.md",
    "docs/index.en.md",
    "docs/cli.md",
    "docs/cli.en.md",
    "docs/design.md",
    "docs/design.en.md",
    "docs/developer-guide.md",
    "docs/developer-guide.en.md",
    "docs/development.md",
    "docs/development.en.md",
)


def test_mkdocs_chatarch_i18n_material_contract() -> None:
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "site_url: https://arch.gh.wzhecnu.cn/ChatEnv/" in mkdocs
    assert 'Homepage = "https://arch.gh.wzhecnu.cn/ChatEnv/"' in pyproject
    assert 'Documentation = "https://arch.gh.wzhecnu.cn/ChatEnv/"' in pyproject
    assert 'Repository = "https://github.com/ChatArch/ChatEnv"' in pyproject
    assert "mkdocs-material>=9.5,<10.0" in pyproject
    assert "mkdocs-static-i18n>=1.2,<2.0" in pyproject
    assert "name: material" in mkdocs
    assert "pymdownx.emoji" in mkdocs
    assert "material.extensions.emoji.twemoji" in mkdocs
    assert "material.extensions.emoji.to_svg" in mkdocs
    assert "i18n:" in mkdocs
    assert "locale: en" in mkdocs
    assert "/ChatEnv/en/" in mkdocs


def test_public_docs_are_bilingual_and_use_chatarch_domain() -> None:
    for rel in PUBLIC_DOCS:
        path = Path(rel)
        assert path.exists(), rel
        text = path.read_text(encoding="utf-8")
        assert "chatarch.github.io" not in text, rel
        assert "github.io" not in text, rel
        assert "template `hello`" not in text, rel


def test_public_docs_keep_live_cli_tree_contract() -> None:
    live_tree = render_cli_tree(cli)
    required = [
        "chatenv [--home <HOME>]  # Manage typed env profiles",
        "├── token  # Manage generic runtime token profiles.",
        "│   ├── refresh <SERVICE> [PROFILE]",
        "│   ├── import <SERVICE> [PROFILE]",
        "└── test [--target <TARGET>]",
    ]
    for rel in ("README.md", "README.en.md", "docs/cli.md", "docs/cli.en.md"):
        text = Path(rel).read_text(encoding="utf-8")
        for line in required:
            assert line in text, f"{rel} missing {line!r}"
    for line in required:
        assert line in live_tree
    assert "hello" not in live_tree.lower()

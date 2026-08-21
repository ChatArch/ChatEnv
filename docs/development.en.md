# Repository Development

## Local install

```bash
python -m pip install -e .[dev,docs]
```

## Tests

```bash
python -m pytest -q
```

## CLI smoke

```bash
PYTHONPATH=src python -m chatenv.cli --help
PYTHONPATH=src python -m chatenv.cli --tree
PYTHONPATH=src python -m chatenv.cli --tree-brief
PYTHONPATH=src python -m chatenv.cli --home ./playground/chatenv-smoke list || true
```

A standalone ChatEnv install only includes the built-in shared schemas. Leaf packages should define and register their own `BaseEnvConfig` subclasses before exercising typed profile writes.

## Build gate

```bash
python -m build
python -m twine check dist/*
```

## Docs

```bash
python -m pip install -e .[docs]
python -m mkdocs build --strict
```

Production docs publish to https://arch.gh.wzhecnu.cn/ChatEnv/.

## Release

1. Update `src/chatenv/__init__.py`.
2. Merge to `main` through a PR.
3. Push a matching annotated tag, for example:

```bash
git tag -a v0.2.8 -m "ChatEnv 0.2.8"
git push origin v0.2.8
```

`publish.yml` verifies that the tag matches the package version, that the tag commit is on `origin/main`, and that the version is not already present on PyPI before publishing through Trusted Publishing / GitHub OIDC.

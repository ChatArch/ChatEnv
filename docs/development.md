# 开发说明

## 本地安装

```bash
pip install -e .[dev]
```

## 测试

```bash
python -m pytest -q
```

## CLI smoke

```bash
PYTHONPATH=src python -m chatenv.cli --help
PYTHONPATH=src python -m chatenv.cli --home /tmp/chatenv-smoke paste --value "OPENAI_API_KEY='sk-xxx'" --yes
PYTHONPATH=src python -m chatenv.cli --home /tmp/chatenv-smoke cat -t oai
```

## 构建校验

```bash
python -m build
python -m twine check dist/*
```

或使用 ChatTool 的 PyPI helper：

```bash
chattool pypi build --project-dir .
chattool pypi check --project-dir .
```

当前本地 ChatTool 只保留 `init/build/check/upload/probe`，没有 `doctor` 命令。

## 发布

1. 更新 `src/chatenv/__init__.py` 中的 `__version__`。
2. 合并到 `main`。
3. 推送匹配版本的 tag，例如：

```bash
git tag v0.1.0
git push origin v0.1.0
```

`publish.yml` 会校验 tag 与包版本一致，并在 PyPI 已存在相同版本时失败。

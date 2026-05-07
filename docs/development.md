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
PYTHONPATH=src python -m chatenv.cli --home /tmp/chatenv-smoke list || true
```

单独安装 `chatenv` 不内置业务 schema。需要测试 typed profile 写入时，应在业务项目里定义并导入自己的 `BaseEnvConfig` 子类后再调用通用命令。

## 构建校验

```bash
python -m build
python -m twine check dist/*
```

## 文档

```bash
pip install -e .[docs]
mkdocs serve
mkdocs build --strict
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
git tag v0.1.1
git push origin v0.1.1
```

`publish.yml` 会校验 tag 与包版本一致，并在 PyPI 已存在相同版本时失败。

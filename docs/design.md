# 设计说明

ChatEnv 是 ChatArch 的 typed env/profile 底层模块。它的职责是把不同工具的密钥、endpoint、模型名等环境变量按“类型 + profile”组织起来，并提供 CLI 与 Python API。

## 目录原则

本阶段做减法，只保留一个根变量：

```text
CHATARCH_HOME=${CHATARCH_HOME:-~/.chatarch}
$CHATARCH_HOME/envs/
```

不新增以下状态面：

- 工具级 config 目录；
- cache 目录；
- data/state 目录；
- 细分路径环境变量。

原因是当前 ChatTool 实际落盘主要是 `~/.config/chattool/envs`，`~/.cache/chattool` 基本不承载状态。ChatEnv 独立化优先迁移真实使用的 env/profile，不顺手扩大配置系统。

## 数据布局

```text
$CHATARCH_HOME/envs/
  OpenAI/
    .env
    work.env
    apple.env
  Aliyun/
    .env
  Tencent/
    .env
```

每个 schema 类型对应一个目录：

- `.env` 是 active profile；
- `name.env` 是 named profile；
- `chatenv use -t TYPE name` 将 named profile 复制为 active `.env`。

## 分层

```text
chatenv.paths       # CHATARCH_HOME 与 envs_dir
chatenv.fields      # EnvField / BaseEnvConfig
chatenv.registry    # type / alias 解析
chatenv.store       # profile 文件读写
chatenv.paste       # 宽松 paste parser
chatenv.cli         # click CLI
chatenv.presets     # 迁移期 schema preset
```

core 模块不依赖 ChatTool；`presets.chattool` 只提供字段定义，不包含 OpenAI/DNS/Feishu 等业务连通性测试。

## 兼容策略

ChatEnv 第一版内置 `chatenv.presets.chattool`，方便直接复用当前 ChatTool 常见 schema。后续 ChatTool 迁移时，可以选择：

1. 继续由 ChatEnv 提供迁移期 preset；
2. ChatTool 自己注册业务 schema，ChatEnv 只作为 runtime/store。

`chatenv migrate chattool` 只做复制，不删除旧文件，默认 dry-run。

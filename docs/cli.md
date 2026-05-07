# CLI 用法

ChatEnv 的 CLI 入口是 `chatenv`。所有命令默认只读取一个根变量：

```bash
export CHATARCH_HOME=~/.chatarch
```

实际 env/profile 根目录为：

```text
$CHATARCH_HOME/envs/
```

也可以对单次命令使用 `--home`：

```bash
chatenv --home /tmp/chatarch cat -t oai
```

## 初始化

```bash
chatenv init                  # 写入全部已注册类型的 active .env
chatenv init -t oai           # 只写入 OpenAI 类型
chatenv init -t oai -i        # 初始化前逐项补问
```

## 查看

```bash
chatenv list                  # 按类型列出 named profiles
chatenv list -t oai
chatenv cat                   # 输出所有 active values，敏感值默认打码
chatenv cat -t oai
chatenv cat -t oai work       # 输出 OpenAI/work.env
chatenv cat -t oai --no-mask  # 明文输出，适合 pipe 给安全的目标
```

## Profile

```bash
chatenv new -t oai work       # 从当前 active values 创建 work.env
chatenv save -t oai work      # 保存当前 active values 到 work.env
chatenv use -t oai work       # 将 work.env 激活为 .env
chatenv delete -t oai work    # 删除 work.env
```

`new/save/delete` 遇到覆盖或删除会确认；自动化场景使用 `-y/--yes`。

## Key 操作

```bash
chatenv set OPENAI_API_KEY=sk-xxx
chatenv get OPENAI_API_KEY
chatenv unset OPENAI_API_KEY
```

`set/unset` 会根据 key 所属 schema 写回对应类型的 active `.env`。

## Paste

`paste` 用于跨机器复制 typed env。输入不要求是严格 dotenv 文件，会从终端日志、shell prompt、复制文本里提取已注册 key。

```bash
chatenv cat -t oai --no-mask | chatenv paste --stdin --profile work --yes
chatenv paste --value "OPENAI_API_KEY='sk-xxx'" --yes
chatenv paste                         # 交互式粘贴，空行结束
```

写入前会输出识别概要：识别到哪些类型、哪些 key、未知 key 被忽略。

## 迁移 ChatTool

```bash
chatenv migrate chattool              # dry-run
chatenv migrate chattool --execute    # 执行复制
chatenv migrate chattool --source ~/.config/chattool --execute
```

迁移只复制旧 `envs/` 中的 env 文件到 `$CHATARCH_HOME/envs/`，不会删除旧文件。

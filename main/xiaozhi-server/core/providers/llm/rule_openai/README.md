# rule_openai

该 Provider 先检查本地规则，命中后直接把规则结果返回给后续 TTS；未命中时沿用原有 OpenAI Provider 调用大模型。

当前规则位于 `rules.py`：

- `往前走` -> `往前走`
- `往后走` -> `往后走`

规则采用完整句子匹配，会忽略空白和句末标点。因此 `往前走。` 可以命中，而 `为什么要往前走` 不会命中。

## 启用

保留原有 OpenAI 模型参数，仅把该 LLM 配置的 `type` 从 `openai` 改为：

```yaml
type: rule_openai
```

如果启用了 manager-api，应在管理后台实际下发给设备的 LLM 模型配置中修改 `type`；此时本地 `config.yaml` 的 LLM 配置通常会被远端配置覆盖。

修改配置后重启 xiaozhi-server，并让设备重新连接。命中规则时日志包含：

```text
规则路由命中，直接返回指令: 往前走
```

## 恢复原行为

把 LLM 配置的 `type` 改回：

```yaml
type: openai
```

无需删除该目录，也没有修改原有 OpenAI Provider。

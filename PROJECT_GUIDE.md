# 语音智能服务平台项目说明书

## 1. 系统定位

本项目为 ESP32 等语音终端提供设备长连接、语音处理、智能体配置、模型管理、OTA 配置和网页运维。ESP32 固件是独立客户端，本次改造不修改固件代码。

| 模块 | 默认端口 | 职责 |
| --- | ---: | --- |
| `xiaozhi-server` | 8000、8003 | WebSocket 设备通信、音频流水线、ASR/LLM/TTS、HTTP 扩展接口 |
| `manager-web` | 8001（开发） | Vue 管理网页；生产构建后通常由 8002 统一托管 |
| `manager-api` | 8002 | Java 管理 API、鉴权、模型/设备/智能体/OTA 配置、数据库迁移 |
| MySQL | 3306（内部） | 持久化业务数据 |
| Redis | 6379（内部） | 配置和查询缓存 |

设备使用两个不同地址：

- OTA：`http://服务器IP:8002/xiaozhi/ota/`
- WebSocket：`ws://服务器IP:8000/xiaozhi/v1/`

不要把 WebSocket 地址填入 OTA URL。OTA 检查会发送 HTTP 请求并期待 JSON 响应，填成 `ws://...` 或普通网页地址会导致“检查新版本失败”。

## 2. 工程结构

```text
xiaozhi-esp32-server-main/
├─ main/
│  ├─ xiaozhi-server/       # Python 实时语音服务
│  ├─ manager-api/          # Java 管理 API
│  ├─ manager-web/          # Vue 2 桌面管理端
│  └─ manager-mobile/       # 移动管理端（可选）
├─ deploy/                  # 新增模块化部署定义
├─ Dockerfile-server
├─ Dockerfile-web
└─ PROJECT_GUIDE.md
```

## 3. 本次改造内容

### 3.1 网页端

- 建立全局设计变量，统一颜色、圆角、阴影、按钮、表单、表格、弹窗和下拉菜单。
- 登录页改为响应式双栏工作台，不再依赖原有宣传人物图和品牌字图。
- 顶部导航改为半透明工作台；窄屏时折叠文字并允许导航横向滚动。
- 首页改为运维中心式首屏，智能体卡片增加清晰层级、悬停反馈和语义化按钮。
- 模型管理页移除旧宣传背景图，改为中性深色模型导航。
- 浏览器标题、描述和主要界面名称统一为“语音智能平台”。

### 3.2 Java 管理 API

模型配置链路遵循“Controller 参数绑定 → Service 事务编排 → Validator 领域校验 → DAO 持久化”：

- `ModelConfigValidator` 统一验证模型名称、配置 JSON、供应器类型、模型名、API URL、API Key 和超时。
- OpenAI/Ollama 地址入库前去除多余尾斜杠，并拒绝非法协议、带账号密码的 URL 和 URL 片段。
- 分页参数自动兜底，单页最大 100 条，避免格式错误和超大查询。
- 模型启停、设默认从 Controller 下沉到 Service；同类型唯一默认模型在事务中更新。
- 模型状态变化后清理 Redis 缓存，避免管理页已更新而语音服务仍读取旧配置。
- 新增错误码 `10205`—`10212` 及多语言消息。
- 迁移 `202608100001.sql` 为 Ollama/OpenAI 表单增加超时、温度、令牌数等字段。

### 3.3 Python Ollama 适配

- 自动将 `http://host:11434` 规范为 `http://host:11434/v1`。
- 校验模型名、URL 和超时，SDK 请求支持两次重试。
- 深拷贝对话，避免 Qwen3 的 `/no_think` 修改共享会话。
- 支持 `temperature`、`max_tokens`、`disable_thinking`。
- 正确过滤跨流式分片的 `<think>...</think>`，并确保响应流关闭。

## 4. 本地开发启动顺序

以下只作为说明，本次改造没有启动项目：

1. 启动 MySQL 和 Redis。
2. 启动 `manager-api`，确认 `http://127.0.0.1:8002/xiaozhi/doc.html` 可访问。
3. 在 `manager-web` 安装依赖并执行 `npm run serve`；页面为 `http://127.0.0.1:8001`，`/xiaozhi` 代理到 8002。
4. 注册首个管理员，在参数管理中取得 `server.secret`。
5. 将 `main/xiaozhi-server/config_from_api.yaml` 复制为 `data/.config.yaml`，填写管理 API 地址和密钥。
6. 启动 Python 服务，确认 8000 WebSocket 和 8003 HTTP 端口监听。

生产环境不需要暴露 8001。网页构建产物和管理 API 由 `Dockerfile-web` 组合到 8002 提供。

## 5. Ollama 接入

在“模型配置 → LLM → 新增”中填写：

```json
{
  "type": "ollama",
  "model_name": "qwen3:8b",
  "base_url": "http://宿主机IP:11434",
  "timeout": 120,
  "temperature": 0.7,
  "max_tokens": 2048,
  "disable_thinking": true
}
```

Python 服务在 Docker 中时，`localhost:11434` 指向容器自身。应使用宿主机网关，或把 Ollama 加入同一 Compose 网络并填写 `http://ollama:11434`。

模块化部署示例：

```bash
cd deploy
cp env.template .env
docker compose -f docker-compose.modular.yml --profile local-ai up -d --build
docker compose -f docker-compose.modular.yml exec ollama ollama pull qwen3:8b
```

## 6. OpenAI 兼容 API

OpenAI、通义兼容模式、One API、New API 和 vLLM 等均可使用 `openai` 供应器：

```json
{
  "type": "openai",
  "base_url": "https://api.example.com/v1",
  "model_name": "your-model-name",
  "api_key": "由服务端保存的密钥",
  "timeout": 120,
  "temperature": 0.7,
  "max_tokens": 2048,
  "top_p": 0.9
}
```

API Key 只通过 8002 管理 API 保存。列表接口返回掩码；编辑时回传原掩码，Service 会保留数据库中的真实密钥。不要把密钥写入 Vue `.env`、浏览器 localStorage 或 ESP32 固件。

## 7. 模块化部署

`deploy/docker-compose.modular.yml` 从当前源码构建：

- `manager-platform`：管理 API + 网页；
- `voice-server`：实时语音服务；
- `mysql`、`redis`：仅内部网络可见；
- `ollama`：通过 `local-ai` profile 按需启用。

部署前必须：

1. 复制 `deploy/env.template` 为 `deploy/.env` 并更换数据库、Redis 密码；
2. 准备 `deploy/data/server/.config.yaml`；
3. 准备 `deploy/models/SenseVoiceSmall/model.pt`，或按实际 ASR 配置调整挂载；
4. 在反向代理配置 HTTPS/WSS，只开放必要入口；
5. 定期备份 MySQL、上传目录和服务器配置。

## 8. 常见故障

### 检查新版本失败

- OTA URL 必须为 `http(s)://.../xiaozhi/ota/`，不能填 `ws://...`。
- URL 必须能从设备所在网络访问，不能使用设备视角下的 `localhost`。
- 检查 8002、防火墙、反向代理路径和管理 API 日志。

### 保存模型失败

- 查看 8002 返回错误码；`10205`—`10212` 是模型配置校验错误。
- Ollama 地址不必手工添加 `/v1`，适配器会补齐。
- Docker 中访问其他容器必须使用服务名或可达 IP。

### 配置修改后仍使用旧模型

- 确认 Java 和 Python 连接同一套数据库、Redis。
- 确认 Python 从 `manager-api` 拉取配置，而不是读取旧本地配置。
- 已建立的会话可能继续使用旧实例，新会话才读取新模型。

## 9. 开发与安全规范

- Controller 不编写跨表业务；事务、缓存和规则放在 Service。
- 供应器输入校验放在 Validation 包；Python 适配器负责运行时协议兼容。
- 数据库结构或预置配置变更必须新增迁移，禁止修改已上线迁移。
- 密钥和密码使用环境变量或密钥管理系统，不提交 Git。
- 生产环境限制 Swagger/Knife4j，关闭默认账号和示例密码。
- 保留原项目及第三方许可证；界面品牌中性化不等于删除法律归属。

[English](./README.md) | [中文](./README.zh-CN.md)

# Anima

**让每一件硬件都拥有智能。**

一个开源的 Agent OS，自动发现你的硬件设备，为每一台设备赋予 AI 技能，使它们能够自主感知、决策与协作。

## Anima 是什么？

**Anima**（拉丁语，意为"灵魂"）为你拥有的每一件硬件注入智能。系统的前提不是"你需要什么传感器"，而是 **"你有什么——我来用。"**

- 零配置——自动发现局域网上的设备
- AI 驱动决策——LLM 大脑加载领域知识，做出智能选择
- 技能系统——每种设备类型获得专属智能，而非简单的开/关控制
- 学习你的偏好——根据你的习惯持续进化

## 架构

```
┌───────────────────────────────────────────┐
│              核心（单进程）                  │
│                                           │
│  发现服务 ──▶ 事件总线 ◀── 调度器           │
│                   │                       │
│    规则引擎 ──▶ LLM 大脑 ◀── 记忆体        │
│                   │                       │
│       控制面板 · 聊天 API · MQTT 客户端     │
└──────────────────┬────────────────────────┘
                   │ MQTT
            ┌──────┴──────┐
            │  Mosquitto  │
            └──┬─────┬────┘
           MIoT    Matter   HA 桥接
          适配器   适配器   (v0.2+)
```

## v0.1 包含什么

| 模块 | 说明 |
|------|------|
| **事件总线** | 异步事件系统，支持通配符订阅和错误隔离 |
| **规则引擎** | 快速通道安全规则（如"温度 > 35°C → 开空调"），毫秒级响应，不需要 LLM |
| **LLM 大脑** | 技能驱动的 AI 决策——加载领域知识，组装上下文，调用 LLM，解析 JSON 动作 |
| **记忆系统** | `preferences.md` + `history.json` + `learned.md`——全部可读，无需数据库 |
| **技能系统** | 4 个内置技能：加湿器、空调、灯光、协调者（跨设备编排） |
| **发现服务** | 通过 mDNS 自动扫描局域网，注册设备，自动去重 |
| **MIoT 适配器** | 小米/米家设备发现和控制（基于 python-miio） |
| **调度器** | 周期性设备扫描（5 分钟）、偏好学习（每天） |
| **CLI** | Rich 交互式终端：`devices`、`scan`、`status <id>`、`history` |
| **REST API** | FastAPI 服务，端口 8080，8 个接口 |
| **Docker Compose** | 一条命令部署：核心 + Mosquitto MQTT Broker |

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
git clone https://github.com/fulai-tech/Anima.git
cd Anima
cp .env.example .env     # 填入你的 LLM_API_KEY
docker compose up -d
# 打开 http://localhost:8080
```

### 方式二：本地开发

```bash
git clone https://github.com/fulai-tech/Anima.git
cd Anima

# 安装依赖（需要 uv：https://docs.astral.sh/uv/）
uv sync --extra dev --python 3.13

# 配置
cp .env.example .env     # 填入你的 LLM_API_KEY

# 启动 MQTT Broker
docker compose up mqtt -d

# 运行 Anima（API 模式）
uv run python -m core.main

# 或者以 CLI 模式运行
uv run python -m core.main --mode cli
```

### 配置说明 (.env)

```env
# 必填：任何兼容 OpenAI 格式的 API Key
LLM_API_KEY=sk-xxx

# 可选：模型名称（默认 gpt-4o）
LLM_MODEL=gpt-4o

# 可选：自定义 API 端点（DeepSeek / 豆包 / Ollama 等）
LLM_BASE_URL=https://api.deepseek.com/v1

# 可选：小米云服务凭据（用于获取设备 token）
XIAOMI_CLOUD_USER=
XIAOMI_CLOUD_PASS=
```

**支持的 LLM 提供商**（任何兼容 OpenAI API 的服务）：

| 提供商 | LLM_MODEL | LLM_BASE_URL |
|--------|-----------|--------------|
| OpenAI | `gpt-4o` | *（留空）* |
| Anthropic（通过代理） | `claude-sonnet-4-20250514` | 你的代理地址 |
| DeepSeek | `deepseek-chat` | `https://api.deepseek.com/v1` |
| 豆包 | `doubao-1.5-pro-32k` | `https://ark.cn-beijing.volces.com/api/v3` |
| Ollama（本地） | `llama3` | `http://localhost:11434/v1` |

## CLI 命令

```
anima> help

Commands:
  devices       — 列出所有已发现的设备
  scan          — 重新扫描设备
  status <id>   — 查看设备状态（JSON）
  history       — 查看最近的 AI 决策记录
  quit          — 退出 CLI
```

## REST API

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/devices` | 列出所有已发现的设备 |
| GET | `/api/devices/{id}` | 获取设备详情 |
| POST | `/api/devices/{id}/command` | 向设备发送控制命令 |
| POST | `/api/scan` | 触发设备重新扫描 |
| GET | `/api/decisions` | 最近的 AI 决策历史 |
| POST | `/api/chat` | 与 Anima 对话（v0.2 完整实现） |
| GET | `/api/rooms` | 列出房间 |

**示例：**

```bash
# 列出设备
curl http://localhost:8080/api/devices

# 触发扫描
curl -X POST http://localhost:8080/api/scan

# 发送控制命令
curl -X POST http://localhost:8080/api/devices/miot_xxx/command \
  -H "Content-Type: application/json" \
  -d '{"device_id":"miot_xxx","action":"set_humidity","params":{"value":55}}'
```

## 技能系统

每个技能教会 Anima **一种设备类型如何变得自主智能**——而非简单地开关控制。

```
skills/
  humidifier/
    skill.yaml          # 元数据 + 兼容设备类型
    knowledge.md        # 领域知识（舒适范围、季节建议、设备联动）
    actions.py          # 可执行操作（set_humidity、set_mode、turn_on/off）
    prompts/
      decide.md         # LLM 决策提示词模板
      learn.md          # 偏好学习提示词模板
```

### 内置技能

| 技能 | 知识库包含 |
|------|-----------|
| **加湿器** | 舒适湿度范围（40-60%）、季节调整、空调联动、水位预警 |
| **空调** | 能耗优化、昼夜温度节律、湿度协调 |
| **灯光** | 昼夜节律照明（2200K-5000K）、分时亮度、渐变过渡 |
| **协调者** | 跨设备编排——防止冲突、创造协同 |

### 决策流程

```
传感器数据变化
  → 规则引擎：是否超过阈值？（快速通道，不涉及 LLM）
  → 如果未处理 → 加载技能知识库 + 用户记忆
  → 组装提示词 → 调用 LLM
  → 解析 JSON 响应 → 通过适配器执行操作
  → 记录到记忆体（偏好演化）
```

## 项目结构

```
Anima/
├── core/                       # 核心进程
│   ├── brain/                  # LLM 决策引擎 + 技能加载器
│   ├── events/                 # 异步事件总线
│   ├── rules/                  # 快速通道规则引擎
│   ├── memory/                 # 用户记忆（Markdown + JSON）
│   ├── scheduler/              # 周期任务调度器
│   ├── api/                    # FastAPI REST 接口
│   ├── config.py               # 配置管理（pydantic-settings）
│   ├── discovery.py            # 设备发现编排器
│   ├── mqtt.py                 # MQTT 客户端封装
│   ├── cli.py                  # Rich 交互式 CLI
│   ├── main.py                 # 主入口 + Anima 编排器
│   └── models.py               # Pydantic 数据模型
├── adapters/                   # 设备协议适配器
│   ├── base.py                 # BaseAdapter 抽象类（实现 3 个方法即可）
│   └── miot/                   # 小米 MIoT 适配器
├── skills/                     # AI 技能包
│   ├── humidifier/
│   ├── air_conditioner/
│   ├── light/
│   └── coordinator/
├── tests/                      # 55 个测试
├── docs/plans/                 # 设计文档 + 实施计划
├── data/memory/                # 运行时用户数据（gitignore）
├── mosquitto/                  # Mosquitto MQTT 配置
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## 测试

```bash
# 运行全部测试（55 个）
uv run pytest tests/ -v

# 运行特定模块测试
uv run pytest tests/core/test_brain.py -v
uv run pytest tests/test_integration.py -v
```

## 路线图

| 版本 | 里程碑 | 主要功能 |
|------|--------|---------|
| **v0.1** | "它活了"（当前） | 核心框架、MIoT 适配器、4 个技能、CLI + API、Docker |
| v0.2 | "现在你能看到了" | 控制面板（React）、Matter 适配器、内嵌聊天、偏好学习 |
| v0.3 | "社区来了" | 技能商店、适配器插件、Telegram Bot、HA 桥接 |
| v0.4 | "越来越强" | 多用户、树莓派镜像、安全加固 |

## 参与贡献

Anima 的设计让贡献变得简单：

- **编写技能** — 3 个文件：`skill.yaml`、`knowledge.md`、`prompts/decide.md`
- **编写适配器** — 1 个类、3 个方法：`discover()`、`subscribe()`、`execute()`

详见[设计文档](docs/plans/2026-03-17-anima-design.zh-CN.md)。

## 许可证

[Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0)

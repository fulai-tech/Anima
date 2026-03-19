[English](./README.md) | [中文](./README.zh-CN.md)

# Anima

**Make Every Hardware Intelligent.**

An open-source Agent OS that auto-discovers your hardware devices, empowers each one with AI Skills, and lets them autonomously sense, decide, and collaborate.

## What is Anima?

**Anima** (Latin for "soul") breathes intelligence into every piece of hardware you own. Instead of asking "what sensors do you need?", Anima asks **"what do you have — I'll use it."**

- Zero configuration — auto-discovers devices on your local network
- AI-driven decisions — LLM Brain loads domain knowledge and makes smart choices
- Skill system — each device type gets specialized intelligence, not just on/off control
- Learns your preferences — evolves over time based on your habits

## Architecture

```
┌───────────────────────────────────────────┐
│              Core (single process)         │
│                                           │
│  Discovery ──▶ EventBus ◀── Scheduler     │
│                   │                       │
│        Rules ──▶ LLM Brain ◀── Memory     │
│                   │                       │
│        Dashboard · Chat API · MQTT Client │
└──────────────────┬────────────────────────┘
                   │ MQTT
            ┌──────┴──────┐
            │  Mosquitto  │
            └──┬─────┬────┘
           MIoT    Matter   HA Bridge
          Adapter  Adapter  (v0.2+)
```

## What's in v0.1

| Module | Description |
|--------|-------------|
| **EventBus** | Async event system with wildcard subscriptions and error isolation |
| **Rules Engine** | Fast-path safety rules (e.g., "temp > 35°C → AC on"), millisecond response, no LLM needed |
| **LLM Brain** | Skill-driven AI decisions — loads domain knowledge, assembles context, calls LLM, parses JSON actions |
| **Memory System** | `preferences.md` + `history.json` + `learned.md` — all human-readable, no database |
| **Skill System** | 4 built-in skills: Humidifier, Air Conditioner, Light, Coordinator (cross-device) |
| **Discovery** | Auto-scans local network via mDNS, registers devices, deduplicates |
| **MIoT Adapter** | Xiaomi/Mi Home device discovery and control via python-miio |
| **Scheduler** | Periodic device scanning (5 min), preference learning (daily) |
| **CLI** | Interactive Rich terminal: `devices`, `scan`, `status <id>`, `history` |
| **REST API** | FastAPI server on port 8080 with 8 endpoints |
| **Docker Compose** | One-command deployment: core + Mosquitto MQTT broker |

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
git clone https://github.com/fulai-tech/Anima.git
cd Anima
cp .env.example .env     # Fill in your LLM_API_KEY
docker compose up -d
# Open http://localhost:8080
```

### Option 2: Local Development

```bash
git clone https://github.com/fulai-tech/Anima.git
cd Anima

# Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync --extra dev --python 3.13

# Configure
cp .env.example .env     # Fill in your LLM_API_KEY

# Start MQTT broker
docker compose up mqtt -d

# Run Anima (API mode)
uv run python -m core.main

# Or run in CLI mode
uv run python -m core.main --mode cli
```

### Configuration (.env)

```env
# Required: any OpenAI-compatible API key
LLM_API_KEY=sk-xxx

# Optional: model name (default: gpt-4o)
LLM_MODEL=gpt-4o

# Optional: custom endpoint for DeepSeek / Doubao / Ollama / etc.
LLM_BASE_URL=https://api.deepseek.com/v1

# Optional: Xiaomi Cloud credentials (for token acquisition)
XIAOMI_CLOUD_USER=
XIAOMI_CLOUD_PASS=
```

**Supported LLM providers** (any OpenAI-compatible API):

| Provider | LLM_MODEL | LLM_BASE_URL |
|----------|-----------|--------------|
| OpenAI | `gpt-4o` | *(leave empty)* |
| Anthropic (via proxy) | `claude-sonnet-4-20250514` | your proxy URL |
| DeepSeek | `deepseek-chat` | `https://api.deepseek.com/v1` |
| Doubao | `doubao-1.5-pro-32k` | `https://ark.cn-beijing.volces.com/api/v3` |
| Ollama (local) | `llama3` | `http://localhost:11434/v1` |

## CLI Commands

```
anima> help

Commands:
  devices       — List all discovered devices
  scan          — Re-scan for new devices
  status <id>   — Show device status (JSON)
  history       — Show recent AI decisions
  quit          — Exit CLI
```

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/devices` | List all discovered devices |
| GET | `/api/devices/{id}` | Get device details |
| POST | `/api/devices/{id}/command` | Send command to device |
| POST | `/api/scan` | Trigger device re-scan |
| GET | `/api/decisions` | Recent AI decision history |
| POST | `/api/chat` | Chat with Anima (v0.2 full implementation) |
| GET | `/api/rooms` | List rooms |

**Example:**

```bash
# List devices
curl http://localhost:8080/api/devices

# Trigger scan
curl -X POST http://localhost:8080/api/scan

# Send command
curl -X POST http://localhost:8080/api/devices/miot_xxx/command \
  -H "Content-Type: application/json" \
  -d '{"device_id":"miot_xxx","action":"set_humidity","params":{"value":55}}'
```

## Skill System

Each Skill teaches Anima **how a device type becomes autonomously intelligent** — not just how to toggle it on/off.

```
skills/
  humidifier/
    skill.yaml          # Metadata + compatible device types
    knowledge.md        # Domain knowledge (comfort ranges, seasonal tips, device interactions)
    actions.py          # Executable actions (set_humidity, set_mode, turn_on/off)
    prompts/
      decide.md         # Decision prompt template for LLM
      learn.md          # Preference learning prompt template
```

### Built-in Skills

| Skill | Knowledge includes |
|-------|-------------------|
| **Humidifier** | Comfort ranges (40-60%), seasonal adjustments, AC interaction, water level alerts |
| **Air Conditioner** | Energy optimization, circadian temperature, humidity coordination |
| **Light** | Circadian lighting (2200K-5000K), time-of-day brightness, transition smoothness |
| **Coordinator** | Cross-device orchestration — prevents conflicts, creates synergies |

### Decision Flow

```
Sensor data changes
  → Rules Engine: threshold breached? (fast path, no LLM)
  → If not handled → Load Skill knowledge + user memory
  → Assemble prompt → Call LLM
  → Parse JSON response → Execute action via adapter
  → Record to memory (preference evolution)
```

## Project Structure

```
Anima/
├── core/                       # Core process
│   ├── brain/                  # LLM decision engine + Skill loader
│   ├── events/                 # Async EventBus
│   ├── rules/                  # Fast-path rules engine
│   ├── memory/                 # User memory (markdown + JSON)
│   ├── scheduler/              # Periodic job scheduler
│   ├── api/                    # FastAPI REST endpoints
│   ├── config.py               # Settings (pydantic-settings)
│   ├── discovery.py            # Device discovery orchestrator
│   ├── mqtt.py                 # MQTT client wrapper
│   ├── cli.py                  # Rich interactive CLI
│   ├── main.py                 # Main entrypoint + Anima orchestrator
│   └── models.py               # Pydantic data models
├── adapters/                   # Device protocol adapters
│   ├── base.py                 # BaseAdapter ABC (3 methods to implement)
│   └── miot/                   # Xiaomi MIoT adapter
├── skills/                     # AI Skill packages
│   ├── humidifier/
│   ├── air_conditioner/
│   ├── light/
│   └── coordinator/
├── tests/                      # 55 tests
├── docs/plans/                 # Design doc + implementation plan
├── data/memory/                # Runtime user data (gitignored)
├── mosquitto/                  # Mosquitto MQTT config
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Testing

```bash
# Run all tests (55 tests)
uv run pytest tests/ -v

# Run specific module tests
uv run pytest tests/core/test_brain.py -v
uv run pytest tests/test_integration.py -v
```

## Roadmap

| Version | Milestone | Key Features |
|---------|-----------|-------------|
| **v0.1** | "It's Alive" (current) | Core framework, MIoT adapter, 4 Skills, CLI + API, Docker |
| v0.2 | "Now You Can See" | Dashboard (React), Matter adapter, embedded chat, preference learning |
| v0.3 | "Community Arrives" | Skill Store, adapter plugins, Telegram Bot, HA bridge |
| v0.4 | "Getting Stronger" | Multi-user, Raspberry Pi image, security hardening |

## Contributing

Anima is designed for easy contribution:

- **Write a Skill** — 3 files: `skill.yaml`, `knowledge.md`, `prompts/decide.md`
- **Write an Adapter** — 1 class, 3 methods: `discover()`, `subscribe()`, `execute()`

See [Design Document](docs/plans/2026-03-17-anima-design.md) for full architecture details.

## License

[Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0)

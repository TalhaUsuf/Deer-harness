<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-23 | Updated: 2026-04-23 -->

# channels

## Purpose

Bridges external messaging platforms to the DeerFlow agent via the LangGraph Server. Each channel runs as a long-lived task that receives platform events, maps `channel:chat[:topic]` → `thread_id`, dispatches messages through `langgraph-sdk` (`runs.wait` or `runs.stream`), and posts AI responses back to the platform.

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | Package marker |
| `base.py` | Abstract `Channel` base class (start/stop/send lifecycle) |
| `service.py` | Manages lifecycle of all configured channels from `config.yaml` |
| `manager.py` | Core dispatcher: thread lookup/creation, command routing, streaming integration |
| `message_bus.py` | Async pub/sub hub: `InboundMessage` queue + outbound callback registry |
| `store.py` | JSON-file persistence for `channel:chat[:topic]` → `thread_id` mapping |
| `commands.py` | Built-in slash commands (`/new`, `/status`, `/models`, `/memory`, `/help`) |
| `feishu.py` | Feishu (Lark) bridge — patches a single running card in place via `update_multi=true` |
| `slack.py` | Slack bridge using bot token + app token (Socket Mode) |
| `telegram.py` | Telegram bridge using `python-telegram-bot` |
| `discord.py` | Discord bridge using `discord.py` |
| `wechat.py` / `wecom.py` | WeChat (consumer) and WeCom (enterprise) bridges |

## For AI Agents

### Working In This Directory

- Channels run **inside the gateway container** in Docker mode, so do not use `localhost` for the LangGraph URL — use `http://langgraph:2024` or set `DEER_FLOW_CHANNELS_LANGGRAPH_URL`.
- Outbound message flow:
  - Slack/Telegram/Discord/WeChat: `runs.wait()` → single final response
  - Feishu: `runs.stream(["messages-tuple", "values"])` → multiple incremental updates patched into the same card
- The store's keys distinguish root vs. threaded conversations: `channel:chat` for root, `channel:chat:topic` for threaded (Feishu, Slack threads).
- New channels must subclass `base.Channel`, register with `service.py`, and be added to the `config.yaml` `channels` section.

### Testing Requirements

- Channel tests live at `backend/tests/test_channels.py` and `tests/test_channel_file_attachments.py`.
- For new platforms, add at least one happy-path test plus a thread-mapping test.

### Common Patterns

- All channels use the shared `MessageBus` rather than calling each other directly.
- Slash commands are routed by `manager.py` to `commands.py` and handled out-of-band (no LangGraph round-trip).
- File attachments are uploaded to the Gateway uploads endpoint, then referenced in the inbound message text.

## Dependencies

### Internal

- `deerflow.client` — for non-LangGraph metadata queries (model list, memory, etc.)
- `app.gateway.deps` — service singletons

### External

- `langgraph-sdk`, `httpx`, `aiohttp`, channel SDKs (`slack-sdk`, `python-telegram-bot`, `discord.py`)

<!-- MANUAL: -->

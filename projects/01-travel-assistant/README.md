# 能处理分步任务的智能旅行助手

该项目用于练习“分步任务（multi-step）规划 + 工具调用”的 Agent 实践。

## 环境准备

建议使用项目内虚拟环境：

```bash
cd projects/01-travel-assistant
bash ./scripts/bootstrap_venv.sh --recreate
source .venv/bin/activate
```

如果你在 macOS 上看到 `urllib3` 的 `NotOpenSSLWarning`，一般是 Python 使用了 `LibreSSL` 导致的提示；本项目已在 `requirements.txt` 中将 `urllib3` 固定为 `<2` 来避免该警告。

如果你在 Apple Silicon（M 系列）上遇到类似 `pydantic_core ... incompatible architecture (have 'x86_64', need 'arm64')` 的报错，说明当前 shell 的架构与已安装 wheel 架构不一致；请用上述脚本重建 `.venv`（或确保使用原生 arm64 终端而非 Rosetta）。

## 配置

将 `.env.example` 复制为 `.env` 并填写你的密钥（你会自行注册获取）：

```bash
cp .env.example .env
```

## 运行

```bash
cd projects/01-travel-assistant
source .venv/bin/activate
python -m travel_assistant --prompt "你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。"
```

说明：

- 需要在 `.env` 中配置 `OPENAI_API_KEY`、`OPENAI_MODEL`（可选 `OPENAI_BASE_URL`，默认 `https://api.openai.com/v1`）
- 若要使用联网搜索景点推荐，需要配置 `TAVILY_API_KEY`

## 下一步（你准备开始写代码时）

- 指令模板：见 `src/travel_assistant/prompts.py`（`AGENT_SYSTEM_PROMPT`）
- LLM 客户端：见 `src/travel_assistant/llm.py`（`OpenAICompatibleClient`，需配置 `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL`）
- 工具实现：见 `src/travel_assistant/tools.py`（`get_weather` / `get_attraction` / `available_tools`）
- 主循环：见 `src/travel_assistant/agent.py`（`run_agent`）
- 定义任务拆分与执行循环（Plan → Act → Observe → Reflect）
- 接入 `tavily-python` 做实时搜索，接入 `openai` 做推理与结构化输出
- 为旅行计划输出定义一个稳定的结构（例如 JSON Schema）

# 能处理分步任务的智能旅行助手

该项目用于练习“分步任务（multi-step）规划 + 工具调用”的 Agent 实践。

## 你将得到什么

- 一个最小可运行的“工具调用 + 主循环”智能体：`python -m travel_assistant`
- 两个工具：`get_weather`（wttr.in 实时天气）与 `get_attraction`（Tavily 搜索景点推荐）
- 一个通用的 OpenAI 兼容 LLM 客户端：`OpenAICompatibleClient`

## 环境准备

### 前置要求

- Python 3.9+（建议使用系统自带或 pyenv 安装的 Python）
- macOS 用户：如果你是 Apple Silicon（M 系列），请尽量使用原生 arm64 终端（不要用 Rosetta）

### 一键创建虚拟环境（推荐）

```bash
cd projects/01-travel-assistant
bash ./scripts/bootstrap_venv.sh --recreate
source .venv/bin/activate
```

如果你在 macOS 上看到 `urllib3` 的 `NotOpenSSLWarning`，一般是 Python 使用了 `LibreSSL` 导致的提示；本项目已在 `requirements.txt` 中将 `urllib3` 固定为 `<2` 来避免该警告。

如果你在 Apple Silicon（M 系列）上遇到类似 `pydantic_core ... incompatible architecture (have 'x86_64', need 'arm64')` 的报错，说明当前 shell 的架构与已安装 wheel 架构不一致；请用上述脚本重建 `.venv`（或确保使用原生 arm64 终端而非 Rosetta）。

## 配置

首次使用请按以下步骤配置密钥（你会自行注册获取）：

```bash
cp .env.example .env
```

编辑 `.env`，按需填写：

- `OPENAI_API_KEY`：你的 LLM 服务密钥
- `OPENAI_MODEL`：模型 ID（例如 `gpt-4o-mini` 或你服务商的模型名）
- `OPENAI_BASE_URL`：可选；OpenAI 官方默认 `https://api.openai.com/v1`
- `TAVILY_API_KEY`：可选；配置后才可用 `get_attraction` 联网搜索

注意：`.env` 不要提交到 git（仓库已在 `.gitignore` 中忽略）。

## 运行

```bash
cd projects/01-travel-assistant
source .venv/bin/activate
python -m travel_assistant --prompt "你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。"
```

说明：

- 需要在 `.env` 中配置 `OPENAI_API_KEY`、`OPENAI_MODEL`（可选 `OPENAI_BASE_URL`，默认 `https://api.openai.com/v1`）
- 若要使用联网搜索景点推荐，需要配置 `TAVILY_API_KEY`

### 第一次运行建议

- 先验证天气工具可用：`python -c "from travel_assistant import get_weather; print(get_weather('北京'))"`
- 再运行智能体主循环：`python -m travel_assistant --prompt "..."`
- 如果你还没配置 `TAVILY_API_KEY`，请先用只需要天气的提示词，避免模型调用 `get_attraction`：
  - `请只查询今天北京的天气，并用 finish 给出结论，不要推荐景点。`

## 常见问题

- **`incompatible architecture` / `pydantic_core` 加载失败**：通常是 Rosetta/x86_64 与 arm64 混用；在本目录运行 `bash ./scripts/bootstrap_venv.sh --recreate` 重建环境。
- **`错误:未配置TAVILY_API_KEY环境变量。`**：正常；配置 `TAVILY_API_KEY` 后即可使用景点搜索工具。
- **LLM 返回 `finish(...)` 但程序提示没找到 Action**：已兼容裸 `finish(answer="...")` 的结束格式；若仍出现，请贴出模型原始输出便于定位。

## 下一步（你准备开始写代码时）

- 指令模板：见 `src/travel_assistant/prompts.py`（`AGENT_SYSTEM_PROMPT`）
- LLM 客户端：见 `src/travel_assistant/llm.py`（`OpenAICompatibleClient`，需配置 `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL`）
- 工具实现：见 `src/travel_assistant/tools.py`（`get_weather` / `get_attraction` / `available_tools`）
- 主循环：见 `src/travel_assistant/agent.py`（`run_agent`）
- 定义任务拆分与执行循环（Plan → Act → Observe → Reflect）
- 接入 `tavily-python` 做实时搜索，接入 `openai` 做推理与结构化输出
- 为旅行计划输出定义一个稳定的结构（例如 JSON Schema）

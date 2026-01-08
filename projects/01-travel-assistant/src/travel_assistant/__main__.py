from __future__ import annotations

import argparse
import os
import sys

from .agent import run_agent
from .env import load_env_file
from .llm import OpenAICompatibleClient
from .prompts import AGENT_SYSTEM_PROMPT
from .tools import available_tools


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="01-travel-assistant agent runner")
    parser.add_argument(
        "--prompt",
        required=False,
        help="User prompt to run once (otherwise read from stdin).",
    )
    parser.add_argument("--max-turns", type=int, default=5)
    args = parser.parse_args(argv)

    load_env_file()

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip()
    model = os.environ.get("OPENAI_MODEL", "").strip()
    if not api_key or not model:
        print(
            "缺少配置:请设置 OPENAI_API_KEY 与 OPENAI_MODEL（可在 projects/01-travel-assistant/.env 中填写）。",
            file=sys.stderr,
        )
        return 2

    if not base_url:
        base_url = "https://api.openai.com/v1"

    user_prompt = args.prompt
    if not user_prompt:
        user_prompt = sys.stdin.read().strip() or "你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。"

    llm = OpenAICompatibleClient(model=model, api_key=api_key, base_url=base_url)
    result = run_agent(
        user_prompt=user_prompt,
        system_prompt=AGENT_SYSTEM_PROMPT,
        llm_generate=llm.generate,
        tools=available_tools,
        max_turns=args.max_turns,
        verbose=True,
    )

    if result.answer and not result.answer.startswith("错误:"):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


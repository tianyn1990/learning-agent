from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple


ToolFn = Callable[..., str]


@dataclass(frozen=True)
class AgentResult:
    answer: str
    turns: int
    history: list[str]


_THOUGHT_ACTION_RE = re.compile(
    r"(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)",
    re.DOTALL,
)


def _extract_bare_finish(text: str) -> Optional[str]:
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate.startswith("finish"):
            continue
        try:
            name, _ = parse_action(candidate)
        except Exception:
            continue
        if name == "finish":
            return candidate
    return None


def truncate_to_first_thought_action(text: str) -> str:
    """
    Keep the model output to a single step.

    Preference order:
    1) Any bare `finish(answer="...")` line
    2) Any Thought/Action pair whose Action is `finish(...)`
    3) The first Thought/Action pair
    4) Raw trimmed text
    """
    bare_finish = _extract_bare_finish(text)
    if bare_finish:
        return bare_finish

    matches = list(_THOUGHT_ACTION_RE.finditer(text))
    if matches:
        for m in matches:
            if re.search(r"Action:\s*finish\s*\(", m.group(1)):
                return m.group(1).strip()
        return matches[0].group(1).strip()
    return text.strip()


def _parse_quoted_value(s: str, start: int) -> Tuple[str, int]:
    quote = s[start]
    if quote not in {"\"", "'"}:
        raise ValueError("expected quote")
    i = start + 1
    out: list[str] = []
    while i < len(s):
        ch = s[i]
        if ch == "\\":
            if i + 1 >= len(s):
                raise ValueError("dangling escape")
            out.append(s[i + 1])
            i += 2
            continue
        if ch == quote:
            return "".join(out), i + 1
        out.append(ch)
        i += 1
    raise ValueError("unterminated string")


def parse_action(action_str: str) -> Tuple[str, Optional[dict]]:
    """
    Parse an Action string.

    Returns:
      - ("finish", {"answer": str}) OR
      - (tool_name, {kw: val})
    """
    action_str = action_str.strip()
    if action_str.startswith("finish"):
        m = re.match(r'^finish\s*\(\s*answer\s*=\s*(["\'])', action_str)
        if not m:
            raise ValueError("finish action must be finish(answer=\"...\")")
        quote = m.group(1)
        start = m.end(1) - 1
        answer, end = _parse_quoted_value(action_str, start)
        tail = action_str[end:].strip()
        if not tail.startswith(")"):
            raise ValueError("finish action missing closing ')'")
        return "finish", {"answer": answer}

    m = re.match(r"^([a-zA-Z_]\w*)\s*\((.*)\)\s*$", action_str, flags=re.DOTALL)
    if not m:
        raise ValueError("tool action must look like tool_name(arg=\"value\")")

    tool_name = m.group(1)
    args_str = m.group(2).strip()
    kwargs: dict[str, str] = {}
    if not args_str:
        return tool_name, kwargs

    i = 0
    while i < len(args_str):
        while i < len(args_str) and args_str[i].isspace():
            i += 1
        key_match = re.match(r"[a-zA-Z_]\w*", args_str[i:])
        if not key_match:
            raise ValueError(f"invalid kwarg near: {args_str[i:i+20]!r}")
        key = key_match.group(0)
        i += len(key)

        while i < len(args_str) and args_str[i].isspace():
            i += 1
        if i >= len(args_str) or args_str[i] != "=":
            raise ValueError(f"expected '=' after {key}")
        i += 1

        while i < len(args_str) and args_str[i].isspace():
            i += 1
        if i >= len(args_str) or args_str[i] not in {"\"", "'"}:
            raise ValueError(f"expected quoted value for {key}")

        value, i = _parse_quoted_value(args_str, i)
        kwargs[key] = value

        while i < len(args_str) and args_str[i].isspace():
            i += 1
        if i >= len(args_str):
            break
        if args_str[i] != ",":
            raise ValueError(f"expected ',' near: {args_str[i:i+20]!r}")
        i += 1

    return tool_name, kwargs


def run_agent(
    *,
    user_prompt: str,
    system_prompt: str,
    llm_generate: Callable[[str, str], str],
    tools: Dict[str, ToolFn],
    max_turns: int = 5,
    verbose: bool = True,
) -> AgentResult:
    prompt_history = [f"用户请求: {user_prompt}"]

    if verbose:
        print(f"用户输入: {user_prompt}\n" + "=" * 40)

    for i in range(max_turns):
        if verbose:
            print(f"--- 循环 {i + 1} ---\n")

        full_prompt = "\n".join(prompt_history)
        llm_output = llm_generate(full_prompt, system_prompt)
        llm_output = truncate_to_first_thought_action(llm_output)

        if verbose:
            print(f"模型输出:\n{llm_output}\n")
        prompt_history.append(llm_output)

        action_match = re.search(r"Action:\s*(.*)", llm_output, re.DOTALL)
        if action_match:
            action_str = action_match.group(1).strip()
        else:
            # Some models may output a bare action like: finish(answer="...")
            candidate = llm_output.strip()
            if candidate.startswith("finish") or re.match(r"^[a-zA-Z_]\w*\s*\(", candidate):
                action_str = candidate
            else:
                observation = "解析错误:模型输出中未找到 Action。"
                if verbose:
                    print(observation)
                prompt_history.append(f"Observation: {observation}")
                break
        try:
            name, kwargs = parse_action(action_str)
        except Exception as e:
            observation = f"解析错误:无法解析 Action - {e}"
            if verbose:
                print(observation)
            prompt_history.append(f"Observation: {observation}")
            continue

        if name == "finish":
            answer = (kwargs or {}).get("answer", "")
            if verbose:
                print(f"任务完成，最终答案: {answer}")
            return AgentResult(answer=answer, turns=i + 1, history=prompt_history)

        if name not in tools:
            observation = f"错误:未定义的工具 '{name}'"
        else:
            try:
                observation = tools[name](**(kwargs or {}))
            except TypeError as e:
                observation = f"错误:工具参数不匹配 - {e}"
            except Exception as e:
                observation = f"错误:工具执行异常 - {e}"

        observation_str = f"Observation: {observation}"
        if verbose:
            print(f"{observation_str}\n" + "=" * 40)
        prompt_history.append(observation_str)

    return AgentResult(answer="错误:达到最大循环次数仍未完成任务。", turns=max_turns, history=prompt_history)

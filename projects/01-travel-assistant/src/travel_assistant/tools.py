from __future__ import annotations

import os
from urllib.parse import quote

import requests
from tavily import TavilyClient


def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 查询真实的天气信息。
    """
    city = city.strip()
    if not city:
        return "错误:城市名称不能为空。"

    url = f"https://wttr.in/{quote(city)}?format=j1"

    try:
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "learning-agent/01-travel-assistant"},
        )
        response.raise_for_status()
        data = response.json()

        current_condition = data["current_condition"][0]
        weather_desc = current_condition["weatherDesc"][0]["value"]
        temp_c = current_condition["temp_C"]

        return f"{city}当前天气:{weather_desc}，气温{temp_c}摄氏度"
    except requests.exceptions.RequestException as e:
        return f"错误:查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError, TypeError, ValueError) as e:
        return f"错误:解析天气数据失败，可能是城市名称无效 - {e}"


def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用 Tavily Search API 搜索并返回优化后的景点推荐。
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误:未配置TAVILY_API_KEY环境变量。"

    city = city.strip()
    weather = weather.strip()
    if not city:
        return "错误:城市名称不能为空。"
    if not weather:
        return "错误:天气信息不能为空。"

    tavily = TavilyClient(api_key=api_key)
    query = f"{city} {weather} 天气 旅游景点 推荐 理由"

    try:
        response = tavily.search(
            query=query,
            search_depth="basic",
            include_answer=True,
            max_results=5,
        )

        if response.get("answer"):
            return response["answer"]

        formatted_results: list[str] = []
        for result in response.get("results", []):
            title = result.get("title", "").strip()
            content = result.get("content", "").strip()
            url = result.get("url", "").strip()

            line = f"- {title}: {content}".strip()
            if url:
                line += f" ({url})"
            formatted_results.append(line)

        if not formatted_results:
            return "抱歉，没有找到相关的旅游景点推荐。"

        return "根据搜索，为您找到以下信息:\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"错误:执行Tavily搜索时出现问题 - {e}"


available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}


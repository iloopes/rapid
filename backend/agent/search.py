import re
import os
import httpx
from duckduckgo_search import DDGS

TAVILY_API = "https://api.tavily.com/search"


def build_search_query(post_text: str) -> str:
    if not post_text or not post_text.strip():
        raise ValueError("Texto do post não pode ser vazio")

    text = re.sub(r"https?://\S+", "", post_text)
    text = re.sub(r"@\w[\w.]*", "", text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) < 3:
        raise ValueError("Texto insuficiente para construir uma query de busca")

    return text[:200]


def search_web(query: str, max_results: int = 5) -> list[dict]:
    api_key = os.getenv("TAVILY_API_KEY")
    if api_key:
        return _search_tavily(query, api_key, max_results)
    return _search_duckduckgo(query, max_results)


def _search_tavily(query: str, api_key: str, max_results: int) -> list[dict]:
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_answer": False,
    }
    try:
        response = httpx.post(TAVILY_API, json=payload, timeout=15)
        response.raise_for_status()
    except httpx.TimeoutException:
        raise Exception("Erro de conexão: timeout ao buscar contexto")
    except httpx.HTTPStatusError as e:
        raise Exception(f"Erro na busca: {e.response.status_code}")

    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")}
        for r in response.json().get("results", [])
    ]


def _search_duckduckgo(query: str, max_results: int) -> list[dict]:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [
            {"title": r.get("title", ""), "url": r.get("href", ""), "content": r.get("body", "")}
            for r in results
        ]
    except Exception as e:
        raise Exception(f"Erro na busca: {e}")

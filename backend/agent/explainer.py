import re
import os
import sys
import json
import base64
import time
import httpx
from openai import OpenAI
from agent.search import build_search_query, search_web
from agent.prompts import get_langfuse_prompt, get_system_prompt, build_user_message


def format_bullets(raw: str) -> list[str]:
    if not raw or not raw.strip():
        raise ValueError("Texto vazio")

    lines = raw.splitlines()
    bullets = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # remove numbered prefixes like "1. ", "2. "
        line = re.sub(r"^\d+\.\s*", "", line)
        # remove bullet prefixes: •, -, *
        line = re.sub(r"^[•\-\*]\s*", "", line)
        line = line.strip()
        if line:
            bullets.append(line[:300])

    if len(bullets) < 3:
        raise ValueError("mínimo de 3 bullets")

    return bullets

_openai_client: OpenAI | None = None


def openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY não configurada")
        if os.getenv("LANGFUSE_SECRET_KEY"):
            from langfuse.openai import OpenAI as LangfuseOpenAI
            _openai_client = LangfuseOpenAI(api_key=api_key)
        else:
            _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def _fetch_image_b64(image_url: str) -> str | None:
    try:
        data = httpx.get(image_url, timeout=10).content
        return base64.b64encode(data).decode()
    except Exception:
        return None


def explain_post(post: dict, model: str = "gpt-4o") -> dict:
    if os.getenv("LANGFUSE_SECRET_KEY"):
        from langfuse import observe, get_client

        @observe(name="explain-post")
        def _run(post: dict) -> dict:
            result = _core(post, model=model)
            get_client().score_current_span(
                name="bullets_count",
                value=len(result["bullets"]),
            )
            return result

        return _run(post)

    return _core(post, model=model)


def _core(post: dict, model: str = "gpt-4o") -> dict:
    try:
        query = build_search_query(post["text"])
        search_results = search_web(query)
    except Exception as e:
        raise Exception(f"Erro ao gerar explicação: falha na busca — {e}")

    text_prompt = build_user_message(post, search_results)

    user_content: list = []
    if post.get("image_url"):
        b64 = _fetch_image_b64(post["image_url"])
        if b64:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            })
    user_content.append({"type": "text", "text": text_prompt})

    lf_prompt = get_langfuse_prompt()
    system_text = lf_prompt.compile() if lf_prompt is not None else get_system_prompt()

    messages = [
        {"role": "system", "content": system_text},
        {"role": "user",   "content": user_content},
    ]

    print("\n" + "="*60)
    print("PROMPT ENVIADO AO GPT:")
    print("="*60)
    for part in user_content:
        if part["type"] == "text":
            safe = part["text"].encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
            print(safe)
        else:
            print("[IMAGE: base64 jpeg]")
    print("="*60 + "\n")

    create_kwargs = dict(
        model=model,
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "explanation",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "bullets": {"type": "array", "items": {"type": "string"}},
                        "sources": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["bullets", "sources"],
                    "additionalProperties": False,
                },
            },
        },
        temperature=0.3,
        max_tokens=1500,
    )
    if lf_prompt is not None:
        create_kwargs["langfuse_prompt"] = lf_prompt

    for attempt in range(3):
        try:
            response = openai_client().chat.completions.create(**create_kwargs)
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise Exception(f"Erro ao gerar explicação: {e}")

    raw = response.choices[0].message.content or ""

    try:
        data = json.loads(raw)
        bullets = data["bullets"]
        sources = data.get("sources") or [r["url"] for r in search_results if r.get("url")]
    except Exception:
        raise Exception("Erro ao parsear resposta do modelo")

    return {"bullets": bullets, "sources": sources}

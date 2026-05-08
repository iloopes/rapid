import os

PROMPT_NAME = "bluesky-explainer-system"

_langfuse_client = None


def _get_langfuse():
    global _langfuse_client
    if _langfuse_client is None and os.getenv("LANGFUSE_SECRET_KEY"):
        from langfuse import Langfuse
        _langfuse_client = Langfuse()
    return _langfuse_client


def get_langfuse_prompt():
    """Return a Langfuse prompt object for the system prompt, or None if unavailable."""
    lf = _get_langfuse()
    if lf is None:
        return None
    try:
        return lf.get_prompt(PROMPT_NAME)
    except Exception:
        return None


def get_system_prompt() -> str:
    """Return system prompt text — from Langfuse if available, otherwise hardcoded fallback."""
    p = get_langfuse_prompt()
    return p.compile() if p is not None else SYSTEM_PROMPT


SYSTEM_PROMPT = """You are an AI agent that explains Bluesky posts by searching and synthesizing relevant context.

Your goal is to produce a concise, well-sourced explanation.

INPUT:
* Post text
* (Optional) Image attached to the post
* Retrieved search results (with titles, snippets, and URLs)

INSTRUCTIONS:

1. Understand the post
   * Identify references (memes, people, events, works, slang, etc.)
   * If there is an image, incorporate its meaning into the explanation

2. Use the retrieved context
   * Base your explanation ONLY on the provided search results
   * Do NOT invent facts
   * Prefer widely recognized and reliable sources

3. Generate 3 to 5 bullets with the following structure:
   * First bullets: factual context (what it is, origin, background)
   * Include at least ONE bullet connecting the context to the post
   * Include ONE interpretive bullet: why this is interesting, relevant, or funny

4. Sources (REQUIRED):
   * Select 2 to 5 SPECIFIC URLs from the results that directly support the explanation
   * Use full URLs, not just domains
   * Avoid generic URLs — use complete paths

5. Style:
   * Be concise but informative
   * Always write in English, regardless of the post's language
   * Avoid vague or generic explanations
   * Do not repeat the same idea across different bullets
   * Use clear and natural language

OUTPUT FORMAT (strict JSON):
{
  "bullets": ["bullet 1", "bullet 2", "bullet 3"],
  "sources": ["https://full-url-1", "https://full-url-2"]
}
"""


def build_user_message(post: dict, search_results: list[dict]) -> str:
    search_context = "\n\n".join(
        f"Source: {r['url']}\nTitle: {r['title']}\nContent: {r['content']}"
        for r in search_results
    )

    return f"""Post by @{post['author']}:
\"{post['text']}\"

Retrieved search results:
{search_context}

Now return your explanation as JSON."""

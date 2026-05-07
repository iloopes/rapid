import re
import httpx

BLUESKY_API = "https://public.api.bsky.app/xrpc"


def parse_bluesky_url(url: str) -> dict:
    if not url:
        raise ValueError("URL inválida")
    pattern = r"https://bsky\.app/profile/([^/]+)/post/([^/?#]+)"
    match = re.match(pattern, url)
    if not match:
        raise ValueError("URL inválida")
    return {"handle": match.group(1), "rkey": match.group(2)}


def get_bluesky_post(handle: str, rkey: str) -> dict:
    url = f"{BLUESKY_API}/com.atproto.repo.getRecord"
    params = {
        "repo": handle,
        "collection": "app.bsky.feed.post",
        "rkey": rkey,
    }
    try:
        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (400, 404):
            raise Exception("Post não encontrado")
        raise Exception(f"Erro na API do Bluesky: {e.response.status_code}")
    except httpx.TimeoutException:
        raise Exception("Erro de conexão: timeout ao acessar Bluesky")
    except httpx.RequestError as e:
        raise Exception(f"Erro de conexão: {e}")

    data = response.json()
    value = data.get("value", {})

    # DID is embedded in the URI: at://did:plc:xxx/app.bsky.feed.post/rkey
    uri = data.get("uri", "")
    did = uri.split("/")[2] if uri else handle

    image_url = _extract_image_url(did, value)

    return {
        "text": value.get("text", ""),
        "author": handle,
        "created_at": value.get("createdAt", ""),
        "image_url": image_url,
    }


def _extract_image_url(did: str, value: dict) -> str | None:
    embed = value.get("embed", {})
    embed_type = embed.get("$type", "")

    if embed_type == "app.bsky.embed.images":
        images = embed.get("images", [])
        if images:
            cid = images[0].get("image", {}).get("ref", {}).get("$link", "")
            if cid:
                return f"https://cdn.bsky.app/img/feed_thumbnail/plain/{did}/{cid}@jpeg"

    return None

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from agent.bluesky import parse_bluesky_url, get_bluesky_post
from agent.explainer import explain_post

app = FastAPI(title="Bluesky Post Explainer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExplainRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("URL não pode ser vazia")
        return v.strip()


class PostInfo(BaseModel):
    text: str
    author: str
    image_url: str | None


class ExplainResponse(BaseModel):
    post: PostInfo
    bullets: list[str]
    sources: list[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/explain", response_model=ExplainResponse)
def explain(request: ExplainRequest):
    try:
        parsed = parse_bluesky_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        post = get_bluesky_post(parsed["handle"], parsed["rkey"])
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        result = explain_post(post)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ExplainResponse(
        post=PostInfo(
            text=post["text"],
            author=post["author"],
            image_url=post.get("image_url"),
        ),
        bullets=result["bullets"],
        sources=result["sources"],
    )

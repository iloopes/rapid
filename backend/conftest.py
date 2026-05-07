import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def bluesky_post_fixture():
    return {
        "uri": "at://user.bsky.social/app.bsky.feed.post/abc123",
        "value": {
            "text": "The Ralph Wiggum technique is a bash loop method for AI agents",
            "createdAt": "2025-06-01T12:00:00Z",
        },
    }


@pytest.fixture
def search_results_fixture():
    return [
        {
            "title": "Ralph Wiggum technique explained",
            "url": "https://example.com/ralph-wiggum",
            "content": "A bash loop method for iterating AI coding agents coined by Geoffrey Huntley in 2025.",
        },
        {
            "title": "Geoffrey Huntley on AI agents",
            "url": "https://ghuntley.com/ralph",
            "content": "The technique spawned the $RALPH Solana token.",
        },
    ]


@pytest.fixture
def client():
    from main import app
    return TestClient(app)

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


VALID_URL = "https://bsky.app/profile/user.bsky.social/post/abc123"

MOCK_EXPLAIN_RESULT = {
    "bullets": [
        "Ralph Wiggum technique é um método de loop em bash para agentes de IA",
        "Foi criado por Geoffrey Huntley em meados de 2025",
        "Gerou derivativos como o token $RALPH na blockchain Solana",
    ],
    "sources": ["https://example.com/ralph", "https://ghuntley.com/ralph"],
}

MOCK_POST = {
    "text": "The Ralph Wiggum technique is amazing",
    "author": "user.bsky.social",
    "image_url": None,
}


class TestExplainEndpoint:
    @patch("main.explain_post", return_value=MOCK_EXPLAIN_RESULT)
    @patch("main.get_bluesky_post", return_value=MOCK_POST)
    @patch("main.parse_bluesky_url", return_value={"handle": "user.bsky.social", "rkey": "abc123"})
    def test_retorna_200_com_url_valida(self, mock_parse, mock_get, mock_explain, client):
        response = client.post("/explain", json={"url": VALID_URL})
        assert response.status_code == 200

    @patch("main.explain_post", return_value=MOCK_EXPLAIN_RESULT)
    @patch("main.get_bluesky_post", return_value=MOCK_POST)
    @patch("main.parse_bluesky_url", return_value={"handle": "user.bsky.social", "rkey": "abc123"})
    def test_response_contem_bullets(self, mock_parse, mock_get, mock_explain, client):
        response = client.post("/explain", json={"url": VALID_URL})
        data = response.json()
        assert "bullets" in data
        assert len(data["bullets"]) >= 3

    @patch("main.explain_post", return_value=MOCK_EXPLAIN_RESULT)
    @patch("main.get_bluesky_post", return_value=MOCK_POST)
    @patch("main.parse_bluesky_url", return_value={"handle": "user.bsky.social", "rkey": "abc123"})
    def test_response_contem_post_original(self, mock_parse, mock_get, mock_explain, client):
        response = client.post("/explain", json={"url": VALID_URL})
        data = response.json()
        assert "post" in data
        assert "text" in data["post"]

    @patch("main.explain_post", return_value=MOCK_EXPLAIN_RESULT)
    @patch("main.get_bluesky_post", return_value=MOCK_POST)
    @patch("main.parse_bluesky_url", return_value={"handle": "user.bsky.social", "rkey": "abc123"})
    def test_response_contem_sources(self, mock_parse, mock_get, mock_explain, client):
        response = client.post("/explain", json={"url": VALID_URL})
        data = response.json()
        assert "sources" in data
        assert isinstance(data["sources"], list)

    def test_retorna_422_com_url_invalida(self, client):
        with patch("main.parse_bluesky_url", side_effect=ValueError("URL inválida")):
            response = client.post("/explain", json={"url": "https://twitter.com/abc"})
        assert response.status_code == 422

    def test_retorna_422_sem_campo_url(self, client):
        response = client.post("/explain", json={})
        assert response.status_code == 422

    def test_retorna_422_com_body_vazio(self, client):
        response = client.post("/explain", json={"url": ""})
        assert response.status_code == 422

    @patch("main.explain_post", side_effect=Exception("Erro ao gerar explicação"))
    @patch("main.get_bluesky_post", return_value=MOCK_POST)
    @patch("main.parse_bluesky_url", return_value={"handle": "user.bsky.social", "rkey": "abc123"})
    def test_retorna_500_quando_agente_falha(self, mock_parse, mock_get, mock_explain, client):
        response = client.post("/explain", json={"url": VALID_URL})
        assert response.status_code == 500


class TestHealthEndpoint:
    def test_health_retorna_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_retorna_status_ok(self, client):
        response = client.get("/health")
        assert response.json() == {"status": "ok"}

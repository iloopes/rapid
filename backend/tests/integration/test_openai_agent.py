import json
import pytest
from unittest.mock import patch, MagicMock
from agent.explainer import explain_post


MOCK_POST = {
    "text": "The Ralph Wiggum technique is amazing for AI agents",
    "author": "user.bsky.social",
    "image_url": None,
}

MOCK_SEARCH_RESULTS = [
    {
        "title": "Ralph Wiggum technique",
        "url": "https://example.com/ralph",
        "content": "Bash loop method coined by Geoffrey Huntley in 2025",
    }
]


def _mock_openai_client(bullets=None, sources=None):
    if bullets is None:
        bullets = ["Bullet 1", "Bullet 2", "Bullet 3"]
    if sources is None:
        sources = ["https://example.com/ralph"]

    response = MagicMock()
    response.choices[0].message.content = json.dumps({"bullets": bullets, "sources": sources})

    client = MagicMock()
    client.chat.completions.create.return_value = response
    return client


class TestExplainPost:
    @patch("agent.explainer.search_web")
    @patch("agent.explainer.openai_client")
    def test_retorna_entre_3_e_5_bullets(self, mock_client_fn, mock_search):
        mock_search.return_value = MOCK_SEARCH_RESULTS
        mock_client_fn.return_value = _mock_openai_client()

        result = explain_post(MOCK_POST)

        assert 3 <= len(result["bullets"]) <= 5

    @patch("agent.explainer.search_web")
    @patch("agent.explainer.openai_client")
    def test_retorna_sources_com_urls(self, mock_client_fn, mock_search):
        mock_search.return_value = MOCK_SEARCH_RESULTS
        mock_client_fn.return_value = _mock_openai_client()

        result = explain_post(MOCK_POST)

        assert "sources" in result
        assert isinstance(result["sources"], list)

    @patch("agent.explainer.search_web")
    @patch("agent.explainer.openai_client")
    def test_chama_search_web_pelo_menos_uma_vez(self, mock_client_fn, mock_search):
        mock_search.return_value = MOCK_SEARCH_RESULTS
        mock_client_fn.return_value = _mock_openai_client()

        explain_post(MOCK_POST)

        mock_search.assert_called()

    @patch("agent.explainer.search_web")
    @patch("agent.explainer.openai_client")
    def test_gemini_error_levanta_excecao(self, mock_client_fn, mock_search):
        mock_search.return_value = MOCK_SEARCH_RESULTS
        client = MagicMock()
        client.chat.completions.create.side_effect = Exception("OpenAI API error")
        mock_client_fn.return_value = client

        with pytest.raises(Exception, match="Erro ao gerar explicação"):
            explain_post(MOCK_POST)

    @patch("agent.explainer._fetch_image_b64")
    @patch("agent.explainer.search_web")
    @patch("agent.explainer.openai_client")
    def test_post_com_imagem_inclui_imagem_nos_parts(self, mock_client_fn, mock_search, mock_fetch):
        post_com_imagem = {**MOCK_POST, "image_url": "https://cdn.bsky.app/img/abc.jpg"}
        mock_search.return_value = MOCK_SEARCH_RESULTS
        mock_fetch.return_value = "base64encodedimage"
        mock_client_fn.return_value = _mock_openai_client()

        explain_post(post_com_imagem)

        client = mock_client_fn.return_value
        call_kwargs = client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        user_message = next(m for m in messages if m["role"] == "user")
        image_parts = [p for p in user_message["content"] if p.get("type") == "image_url"]
        assert len(image_parts) > 0

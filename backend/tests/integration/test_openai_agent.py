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


def _mock_model(text: str) -> MagicMock:
    model = MagicMock()
    model.generate_content.return_value = MagicMock(text=text)
    return model


class TestExplainPost:
    @patch("agent.explainer.search_web")
    @patch("agent.explainer.gemini_client")
    def test_retorna_entre_3_e_5_bullets(self, mock_client_fn, mock_search):
        mock_search.return_value = MOCK_SEARCH_RESULTS
        mock_client_fn.return_value = _mock_model("• Bullet 1\n• Bullet 2\n• Bullet 3")

        result = explain_post(MOCK_POST)

        assert 3 <= len(result["bullets"]) <= 5

    @patch("agent.explainer.search_web")
    @patch("agent.explainer.gemini_client")
    def test_retorna_sources_com_urls(self, mock_client_fn, mock_search):
        mock_search.return_value = MOCK_SEARCH_RESULTS
        mock_client_fn.return_value = _mock_model("• Bullet 1\n• Bullet 2\n• Bullet 3")

        result = explain_post(MOCK_POST)

        assert "sources" in result
        assert isinstance(result["sources"], list)

    @patch("agent.explainer.search_web")
    @patch("agent.explainer.gemini_client")
    def test_chama_search_web_pelo_menos_uma_vez(self, mock_client_fn, mock_search):
        mock_search.return_value = MOCK_SEARCH_RESULTS
        mock_client_fn.return_value = _mock_model("• B1\n• B2\n• B3")

        explain_post(MOCK_POST)

        mock_search.assert_called()

    @patch("agent.explainer.search_web")
    @patch("agent.explainer.gemini_client")
    def test_gemini_error_levanta_excecao(self, mock_client_fn, mock_search):
        mock_search.return_value = MOCK_SEARCH_RESULTS
        model = MagicMock()
        model.generate_content.side_effect = Exception("Gemini API error")
        mock_client_fn.return_value = model

        with pytest.raises(Exception, match="Erro ao gerar explicação"):
            explain_post(MOCK_POST)

    @patch("agent.explainer._fetch_image_part")
    @patch("agent.explainer.search_web")
    @patch("agent.explainer.gemini_client")
    def test_post_com_imagem_inclui_imagem_nos_parts(self, mock_client_fn, mock_search, mock_fetch):
        post_com_imagem = {**MOCK_POST, "image_url": "https://cdn.bsky.app/img/abc.jpg"}
        mock_search.return_value = MOCK_SEARCH_RESULTS
        mock_fetch.return_value = {"mime_type": "image/jpeg", "data": b"fakeimage"}
        model = MagicMock()
        model.generate_content.return_value = MagicMock(text="• B1\n• B2\n• B3")
        mock_client_fn.return_value = model

        explain_post(post_com_imagem)

        call_parts = model.generate_content.call_args[0][0]
        mime_types = [p["mime_type"] for p in call_parts if isinstance(p, dict)]
        assert "image/jpeg" in mime_types

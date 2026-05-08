import pytest
from unittest.mock import patch, MagicMock
from agent.bluesky import get_bluesky_post


class TestGetBlueskyPost:
    @patch("agent.bluesky.httpx.get")
    def test_retorna_texto_do_post(self, mock_get, bluesky_post_fixture):
        mock_get.return_value.json.return_value = bluesky_post_fixture
        mock_get.return_value.raise_for_status = MagicMock()

        post = get_bluesky_post("user.bsky.social", "abc123")

        assert post["text"] == "The Ralph Wiggum technique is a bash loop method for AI agents"

    @patch("agent.bluesky.httpx.get")
    def test_retorna_autor_do_post(self, mock_get, bluesky_post_fixture):
        mock_get.return_value.json.return_value = bluesky_post_fixture
        mock_get.return_value.raise_for_status = MagicMock()

        post = get_bluesky_post("user.bsky.social", "abc123")

        assert "author" in post
        assert post["author"] == "user.bsky.social"

    @patch("agent.bluesky.httpx.get")
    def test_chama_endpoint_correto(self, mock_get, bluesky_post_fixture):
        mock_get.return_value.json.return_value = bluesky_post_fixture
        mock_get.return_value.raise_for_status = MagicMock()

        get_bluesky_post("user.bsky.social", "abc123")

        call_args = mock_get.call_args
        call_url = call_args[0][0]
        call_params = call_args.kwargs.get("params", {})
        assert "com.atproto.repo.getRecord" in call_url
        assert call_params.get("repo") == "user.bsky.social"
        assert call_params.get("rkey") == "abc123"

    @patch("agent.bluesky.httpx.get")
    def test_post_nao_encontrado_levanta_excecao(self, mock_get):
        import httpx
        mock_get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock(status_code=404)
        )

        with pytest.raises(Exception, match="Post não encontrado"):
            get_bluesky_post("user.bsky.social", "post-inexistente")

    @patch("agent.bluesky.httpx.get")
    def test_post_com_imagem_retorna_image_url(self, mock_get):
        mock_response = {
            "uri": "at://user.bsky.social/app.bsky.feed.post/abc",
            "value": {
                "text": "Check this image",
                "embed": {
                    "$type": "app.bsky.embed.images",
                    "images": [{"image": {"ref": {"$link": "bafkreiabc"}}, "alt": "screenshot"}],
                },
                "createdAt": "2025-06-01T12:00:00Z",
            },
        }
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = MagicMock()

        post = get_bluesky_post("user.bsky.social", "abc")

        assert post.get("image_url") is not None

    @patch("agent.bluesky.httpx.get")
    def test_timeout_levanta_excecao_de_conexao(self, mock_get):
        import httpx
        mock_get.side_effect = httpx.TimeoutException("timeout")

        with pytest.raises(Exception, match="Erro de conexão"):
            get_bluesky_post("user.bsky.social", "abc123")

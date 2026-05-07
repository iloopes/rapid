import pytest
from agent.bluesky import parse_bluesky_url


class TestParseBlueSkyUrl:
    def test_url_valida_retorna_handle_e_rkey(self):
        url = "https://bsky.app/profile/user.bsky.social/post/abc123"
        result = parse_bluesky_url(url)
        assert result == {"handle": "user.bsky.social", "rkey": "abc123"}

    def test_url_com_subdominio_customizado(self):
        url = "https://bsky.app/profile/john.doe.com/post/xyz789"
        result = parse_bluesky_url(url)
        assert result == {"handle": "john.doe.com", "rkey": "xyz789"}

    def test_url_sem_https_levanta_value_error(self):
        with pytest.raises(ValueError, match="URL inválida"):
            parse_bluesky_url("bsky.app/profile/user.bsky.social/post/abc123")

    def test_url_de_outro_dominio_levanta_value_error(self):
        with pytest.raises(ValueError, match="URL inválida"):
            parse_bluesky_url("https://twitter.com/user/status/123")

    def test_url_sem_rkey_levanta_value_error(self):
        with pytest.raises(ValueError, match="URL inválida"):
            parse_bluesky_url("https://bsky.app/profile/user.bsky.social")

    def test_url_vazia_levanta_value_error(self):
        with pytest.raises(ValueError, match="URL inválida"):
            parse_bluesky_url("")

    def test_url_none_levanta_type_error(self):
        with pytest.raises((ValueError, TypeError)):
            parse_bluesky_url(None)

    def test_rkey_alfanumerico_longo(self):
        url = "https://bsky.app/profile/alice.bsky.social/post/3jxwzv7gc2s2a"
        result = parse_bluesky_url(url)
        assert result["rkey"] == "3jxwzv7gc2s2a"
        assert result["handle"] == "alice.bsky.social"

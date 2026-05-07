import pytest
from agent.search import build_search_query


class TestBuildSearchQuery:
    def test_query_simples_retorna_texto_do_post(self):
        post_text = "Ralph Wiggum technique for AI agents"
        query = build_search_query(post_text)
        assert "Ralph Wiggum" in query

    def test_query_remove_mencoes(self):
        post_text = "@alice.bsky.social check out this technique"
        query = build_search_query(post_text)
        assert "@alice.bsky.social" not in query
        assert "technique" in query

    def test_query_remove_urls(self):
        post_text = "great article https://example.com/article about AI"
        query = build_search_query(post_text)
        assert "https://example.com/article" not in query
        assert "great article" in query

    def test_query_remove_hashtags(self):
        post_text = "AI agents are cool #AI #tech"
        query = build_search_query(post_text)
        assert "#AI" not in query
        assert "#tech" not in query

    def test_query_texto_vazio_levanta_value_error(self):
        with pytest.raises(ValueError, match="Texto do post não pode ser vazio"):
            build_search_query("")

    def test_query_so_com_mencoes_levanta_value_error(self):
        with pytest.raises(ValueError, match="Texto insuficiente"):
            build_search_query("@alice @bob @carol")

    def test_query_limita_tamanho_maximo(self):
        post_text = "palavra " * 100
        query = build_search_query(post_text)
        assert len(query) <= 200

    def test_query_preserva_termos_tecnicos(self):
        post_text = "usando o $RALPH token no Solana blockchain"
        query = build_search_query(post_text)
        assert "RALPH" in query or "Solana" in query

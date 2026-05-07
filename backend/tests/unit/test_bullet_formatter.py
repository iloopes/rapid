import pytest
from agent.explainer import format_bullets


class TestFormatBullets:
    def test_retorna_lista_de_strings(self):
        raw = "• Primeiro ponto\n• Segundo ponto\n• Terceiro ponto"
        bullets = format_bullets(raw)
        assert isinstance(bullets, list)
        assert all(isinstance(b, str) for b in bullets)

    def test_entre_3_e_5_bullets(self):
        raw = "• A\n• B\n• C\n• D"
        bullets = format_bullets(raw)
        assert 3 <= len(bullets) <= 5

    def test_remove_prefixos_de_bullet(self):
        raw = "• Primeiro\n- Segundo\n* Terceiro"
        bullets = format_bullets(raw)
        for bullet in bullets:
            assert not bullet.startswith(("•", "-", "*"))

    def test_remove_linhas_vazias(self):
        raw = "• Primeiro\n\n• Segundo\n\n• Terceiro"
        bullets = format_bullets(raw)
        assert len(bullets) == 3
        assert all(b.strip() for b in bullets)

    def test_levanta_value_error_com_menos_de_3_bullets(self):
        raw = "• Só um bullet"
        with pytest.raises(ValueError, match="mínimo de 3 bullets"):
            format_bullets(raw)

    def test_levanta_value_error_com_texto_vazio(self):
        with pytest.raises(ValueError, match="Texto vazio"):
            format_bullets("")

    def test_trunca_bullets_muito_longos(self):
        longo = "palavra " * 100
        raw = f"• {longo}\n• {longo}\n• {longo}"
        bullets = format_bullets(raw)
        for bullet in bullets:
            assert len(bullet) <= 300

    def test_bullets_numerados_tambem_sao_aceitos(self):
        raw = "1. Primeiro ponto\n2. Segundo ponto\n3. Terceiro ponto"
        bullets = format_bullets(raw)
        assert len(bullets) == 3
        assert not bullets[0][0].isdigit()

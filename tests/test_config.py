import pytest

from bib.config import Configuracoes
from bib.excecoes import ValidacaoError


def test_configuracoes_inicia_com_valores_padrao():
    config = Configuracoes()

    assert config.limite_leituras_simultaneas == 3
    assert config.genero_favorito is None
    assert config.meta_anual == 0


@pytest.mark.parametrize(
    ("atributo", "valor"),
    [
        ("limite_leituras_simultaneas", 0),
        ("limite_leituras_simultaneas", -1),
        ("limite_leituras_simultaneas", True),
        ("limite_leituras_simultaneas", 2.5),
        ("genero_favorito", ""),
        ("genero_favorito", "   "),
        ("genero_favorito", 42),
        ("meta_anual", -1),
        ("meta_anual", True),
        ("meta_anual", 2.5),
    ],
)
def test_configuracoes_rejeita_valores_invalidos(atributo, valor):
    config = Configuracoes()

    with pytest.raises(ValidacaoError):
        setattr(config, atributo, valor)


def test_configuracoes_normaliza_genero_e_aceita_meta_sem_meta():
    config = Configuracoes()

    config.genero_favorito = "  Ficção  "
    config.meta_anual = 0

    assert config.genero_favorito == "Ficção"
    assert config.meta_anual == 0


def test_configuracoes_aceita_limites_validos():
    config = Configuracoes()

    config.limite_leituras_simultaneas = 1
    config.meta_anual = 12

    assert config.limite_leituras_simultaneas == 1
    assert config.meta_anual == 12

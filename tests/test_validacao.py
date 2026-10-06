import pytest

from bib.excecoes import ValidacaoError


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        pytest.param("titulo", "", id="titulo-vazio"),
        pytest.param("titulo", "   ", id="titulo-apenas-espacos"),
        pytest.param("autor", "", id="autor-vazio"),
        pytest.param("ano", 1499, id="ano-abaixo-do-minimo"),
        pytest.param("ano", "2000", id="ano-nao-inteiro"),
        pytest.param("ano", True, id="ano-booleano"),
        pytest.param("nota", -0.1, id="nota-abaixo-do-minimo"),
        pytest.param("nota", 10.1, id="nota-acima-do-maximo"),
        pytest.param("nota", True, id="nota-booleano"),
        pytest.param("status", "desconhecido", id="status-invalido"),
        pytest.param("paginas", 0, id="sem-paginas"),
        pytest.param("paginas", True, id="paginas-booleano"),
        pytest.param("pagina_atual", -1, id="progresso-negativo"),
        pytest.param("pagina_atual", 257, id="progresso-maior-que-total"),
        pytest.param("pagina_atual", False, id="progresso-booleano"),
    ],
)
def test_rejeita_dados_invalidos_ao_criar_livro(livro_factory, campo, valor):
    with pytest.raises(ValidacaoError):
        livro_factory(**{campo: valor})


@pytest.mark.parametrize(
    ("campo", "valor", "esperado"),
    [
        pytest.param("titulo", "  Título  ", "Título", id="titulo-aparado"),
        pytest.param("ano", 1500, 1500, id="ano-minimo-permitido"),
        pytest.param("nota", 0, 0.0, id="nota-minima-permitida"),
        pytest.param("nota", 10, 10.0, id="nota-maxima-permitida"),
        pytest.param("nota", None, None, id="nota-opcional"),
        pytest.param("paginas", 1, 1, id="uma-pagina"),
        pytest.param("pagina_atual", 0, 0, id="progresso-inicial"),
        pytest.param("pagina_atual", 256, 256, id="progresso-no-limite"),
    ],
)
def test_aceita_limites_e_opcionais(livro_factory, campo, valor, esperado):
    livro = livro_factory(**{campo: valor})

    assert getattr(livro, campo) == esperado

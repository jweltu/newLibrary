from datetime import date

import pytest

from bib.excecoes import (
    PublicacaoDuplicadaError,
    PublicacaoNaoEncontradaError,
    ValidacaoError,
)
from bib.models.colecao import Colecao
from bib.models.enums import StatusLeitura


def test_adiciona_obtem_remove_e_itera_publicacoes(livro_factory):
    livro = livro_factory()
    colecao = Colecao()

    colecao.adicionar(livro)

    assert len(colecao) == 1
    assert colecao.obter(livro.id) is livro
    assert list(colecao) == [livro]
    assert colecao.remover(livro.id) is None
    assert len(colecao) == 0


def test_adicionar_rejeita_publicacao_duplicada_por_id_ou_titulo_autor(
    livro_factory
):
    primeiro = livro_factory()
    colecao = Colecao({primeiro.id: primeiro})

    with pytest.raises(PublicacaoDuplicadaError):
        colecao.adicionar(livro_factory(id="outro-id"))
    with pytest.raises(PublicacaoDuplicadaError):
        colecao.adicionar(livro_factory(titulo="Outro", id=primeiro.id))


@pytest.mark.parametrize("operacao", ["obter", "remover"])
def test_obter_ou_remover_id_inexistente_lanca_excecao(operacao):
    colecao = Colecao()

    with pytest.raises(PublicacaoNaoEncontradaError):
        getattr(colecao, operacao)("inexistente")


def test_existe_compara_titulo_e_autor_sem_diferenciar_maiusculas(livro_factory):
    livro = livro_factory()
    colecao = Colecao({livro.id: livro})

    assert colecao.existe("dom casmurro", "MACHADO DE ASSIS")
    assert not colecao.existe("Dom Casmurro", "Outro autor")


def test_buscar_combina_filtros_de_texto_e_status(livro_factory, revista_factory):
    livro = livro_factory(status=StatusLeitura.LENDO)
    revista = revista_factory(status=StatusLeitura.NAO_LIDO)
    colecao = Colecao({livro.id: livro, revista.id: revista})

    assert colecao.buscar(titulo="casmurro") == [livro]
    assert colecao.buscar(autor="equipe", status="NAO_LIDO") == [revista]
    assert colecao.buscar(genero="não encontrado") == []
    assert colecao.em_leitura() == [livro]


def test_buscar_rejeita_filtro_de_status_invalido(livro_factory):
    colecao = Colecao({"livro": livro_factory()})

    with pytest.raises(ValidacaoError, match="Status"):
        colecao.buscar(status="desconhecido")


def test_filtrar_periodo_inclui_datas_limite(livro_factory):
    antes = livro_factory(id="antes", data_inclusao=date(2026, 1, 1))
    dentro = livro_factory(id="dentro", data_inclusao=date(2026, 1, 2))
    limite = livro_factory(id="limite", data_inclusao=date(2026, 1, 3))
    depois = livro_factory(id="depois", data_inclusao=date(2026, 1, 4))
    colecao = Colecao(
        {livro.id: livro for livro in (antes, dentro, limite, depois)}
    )

    resultado = colecao.filtrar_por_periodo(date(2026, 1, 2), date(2026, 1, 3))

    assert resultado == [dentro, limite]


def test_filtrar_rejeita_periodo_invalido(livro_factory):
    colecao = Colecao({"livro": livro_factory()})

    with pytest.raises(ValidacaoError):
        colecao.filtrar("2026-01-01", date(2026, 1, 2))
    with pytest.raises(ValidacaoError, match="inicial"):
        colecao.filtrar(date(2026, 1, 3), date(2026, 1, 2))


def test_concluidas_no_ano_e_contar_por_status(livro_factory, revista_factory):
    concluida = livro_factory(
        status=StatusLeitura.LIDO, data_termino=date(2026, 5, 1)
    )
    em_leitura = revista_factory(status=StatusLeitura.LENDO)
    lida_ano_anterior = livro_factory(
        id="ano-anterior",
        status=StatusLeitura.LIDO,
        data_termino=date(2025, 12, 31),
    )
    colecao = Colecao(
        {
            concluida.id: concluida,
            em_leitura.id: em_leitura,
            lida_ano_anterior.id: lida_ano_anterior,
        }
    )

    assert colecao.concluidas_no_ano(2026) == 1
    assert colecao.contar_por_status(StatusLeitura.LIDO) == 2
    assert colecao.contar_por_status("LENDO") == 1


def test_ordenadas_organiza_por_ano(livro_factory):
    recente = livro_factory(id="recente", ano=2020)
    antigo = livro_factory(id="antigo", ano=1899)
    colecao = Colecao({recente.id: recente, antigo.id: antigo})

    assert colecao.ordenadas() == [antigo, recente]


def test_adicionar_rejeita_objeto_que_nao_e_publicacao():
    with pytest.raises(ValidacaoError):
        Colecao().adicionar(object())
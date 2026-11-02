from datetime import date

import pytest

from bib.models.colecao import Colecao
from bib.models.enums import StatusLeitura
from bib.relatorio import (
    GeradorRelatorios,
    RelatorioMediaAvaliacoes,
    RelatorioPorStatus,
    RelatorioProgressoAnual,
    RelatorioTopAvaliadas,
    RelatorioTotal,
)


def test_relatorio_total_conta_publicacoes(livro_factory, revista_factory):
    colecao = Colecao(
        {
            "livro": livro_factory(),
            "revista": revista_factory(),
        }
    )

    assert RelatorioTotal().gerar(colecao) == {"total": 2}


def test_relatorio_por_status_retorna_quantidade_e_percentual(
    livro_factory, revista_factory
):
    livro = livro_factory(status=StatusLeitura.LIDO)
    revista = revista_factory(status=StatusLeitura.LENDO)
    outro_livro = livro_factory(id="livro-2")
    colecao = Colecao(
        {
            livro.id: livro,
            revista.id: revista,
            outro_livro.id: outro_livro,
        }
    )

    assert RelatorioPorStatus().gerar(colecao) == {
        "total": 3,
        "lidos": {"quantidade": 1, "percentual": 33.33},
        "nao_lidos": {"quantidade": 1, "percentual": 33.33},
        "lendo": {"quantidade": 1, "percentual": 33.33},
        "livros": {
            "total": 2,
            "lidos": {"quantidade": 1, "percentual": 50.0},
            "nao_lidos": {"quantidade": 1, "percentual": 50.0},
            "lendo": {"quantidade": 0, "percentual": 0.0},
        },
    }


def test_relatorio_por_status_sem_publicacoes_retorna_percentuais_zerados():
    assert RelatorioPorStatus().gerar(Colecao({})) == {
        "total": 0,
        "lidos": {"quantidade": 0, "percentual": 0.0},
        "nao_lidos": {"quantidade": 0, "percentual": 0.0},
        "lendo": {"quantidade": 0, "percentual": 0.0},
        "livros": {
            "total": 0,
            "lidos": {"quantidade": 0, "percentual": 0.0},
            "nao_lidos": {"quantidade": 0, "percentual": 0.0},
            "lendo": {"quantidade": 0, "percentual": 0.0},
        },
    }


def test_relatorio_media_avalia_apenas_publicacoes_lidas_e_avaliadas(
    livro_factory, revista_factory
):
    avaliado = livro_factory(status=StatusLeitura.LIDO, nota=8)
    sem_nota = revista_factory(status=StatusLeitura.LIDO)
    ainda_lendo = livro_factory(id="livro-2", status=StatusLeitura.LENDO, nota=10)
    colecao = Colecao(
        {
            avaliado.id: avaliado,
            sem_nota.id: sem_nota,
            ainda_lendo.id: ainda_lendo,
        }
    )

    assert RelatorioMediaAvaliacoes().gerar(colecao) == {
        "media": 8.0,
        "quantidade_avaliada": 1,
    }


def test_relatorio_media_sem_avaliacoes_retorna_media_nula():
    assert RelatorioMediaAvaliacoes().gerar(Colecao({})) == {
        "media": None,
        "quantidade_avaliada": 0,
    }


def test_relatorio_top5_informa_insuficiencia_com_menos_de_cinco_avaliacoes(
    livro_factory,
):
    lido = livro_factory(status=StatusLeitura.LIDO, nota=9)

    assert RelatorioTopAvaliadas().gerar(Colecao({lido.id: lido})) == {
        "suficiente": False,
        "mensagem": (
            "Não há informações suficientes no acervo para gerar "
            "o ranking das 5 publicações mais bem avaliadas."
        ),
        "publicacoes": [],
    }


def test_relatorio_top5_ordena_as_cinco_maiores_notas(livro_factory):
    livros = [
        livro_factory(
            id=str(nota),
            titulo=f"Livro {nota}",
            autor=f"Autor {nota}",
            status=StatusLeitura.LIDO,
            nota=nota,
        )
        for nota in range(1, 7)
    ]
    colecao = Colecao({livro.id: livro for livro in livros})

    resultado = RelatorioTopAvaliadas().gerar(colecao)

    assert resultado["suficiente"] is True
    assert [item["nota"] for item in resultado["publicacoes"]] == [
        6.0,
        5.0,
        4.0,
        3.0,
        2.0,
    ]


def test_relatorio_progresso_anual_considera_data_e_status(
    livro_factory, revista_factory
):
    concluida_no_ano = livro_factory(
        status=StatusLeitura.LIDO, data_termino=date(2026, 4, 15)
    )
    concluida_em_outro_ano = revista_factory(
        status=StatusLeitura.LIDO, data_termino=date(2025, 12, 20)
    )
    colecao = Colecao(
        {
            concluida_no_ano.id: concluida_no_ano,
            concluida_em_outro_ano.id: concluida_em_outro_ano,
        }
    )

    assert RelatorioProgressoAnual(meta=2, ano=2026).gerar(colecao) == {
        "concluidas": 1,
        "meta": 2,
        "percentual_atingido": 50.0,
        "aviso": "Meta pendente",
    }


def test_relatorio_progresso_sem_meta_retorna_percentual_nulo():
    relatorio = RelatorioProgressoAnual(meta=0, ano=2026)

    assert relatorio.gerar(Colecao({})) == {
        "concluidas": 0,
        "meta": 0,
        "percentual_atingido": None,
        "aviso": "Nenhuma meta anual definida",
    }


@pytest.mark.parametrize(
    ("meta", "ano"),
    [
        (-1, 2026),
        (True, 2026),
        (1, True),
        (1, "2026"),
    ],
)
def test_relatorio_progresso_valida_meta_e_ano(meta, ano):
    with pytest.raises(ValueError):
        RelatorioProgressoAnual(meta=meta, ano=ano)


def test_gerador_permite_trocar_estrategia(livro_factory):
    colecao = Colecao({"livro": livro_factory()})
    gerador = GeradorRelatorios(RelatorioTotal())

    assert gerador.executar(colecao) == {"total": 1}

    gerador.definir_estrategia(RelatorioPorStatus())

    assert gerador.executar(colecao)["nao_lidos"]["quantidade"] == 1


def test_gerador_rejeita_estrategia_invalida():
    with pytest.raises(TypeError, match="EstrategiaRelatorio"):
        GeradorRelatorios(object())
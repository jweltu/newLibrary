from collections.abc import Iterable

from bib.models.colecao import Colecao
from bib.models.enums import StatusLeitura
from bib.models.publicacao import Publicacao
from bib.relatorio.base import EstrategiaRelatorio


class RelatorioTotal(EstrategiaRelatorio):
    def gerar(self, colecao: Colecao) -> dict[str, object]:
        return {"total": len(colecao.publicacoes)}


class RelatorioPorStatus(EstrategiaRelatorio):
    def gerar(self, colecao: Colecao) -> dict[str, object]:
        relatorio = self._resumo(colecao.publicacoes.values())
        livros = [
            publicacao
            for publicacao in colecao.publicacoes.values()
            if publicacao.tipo() == "livro"
        ]
        relatorio["livros"] = self._resumo(livros)
        return relatorio

    @staticmethod
    def _resumo(publicacoes: Iterable[Publicacao]) -> dict[str, object]:
        total = len(publicacoes)
        relatorio: dict[str, object] = {"total": total}
        chaves = {
            StatusLeitura.LIDO: "lidos",
            StatusLeitura.NAO_LIDO: "nao_lidos",
            StatusLeitura.LENDO: "lendo",
        }
        for status, chave in chaves.items():
            quantidade = sum(
                publicacao.status is status for publicacao in publicacoes
            )
            percentual = round(quantidade / total * 100, 2) if total else 0.0
            relatorio[chave] = {
                "quantidade": quantidade,
                "percentual": percentual,
            }
        return relatorio


class RelatorioMediaAvaliacoes(EstrategiaRelatorio):
    def gerar(self, colecao: Colecao) -> dict[str, object]:
        avaliadas = [
            publicacao.nota
            for publicacao in colecao.publicacoes.values()
            if publicacao.status is StatusLeitura.LIDO
            and publicacao.nota is not None
        ]
        media = round(sum(avaliadas) / len(avaliadas), 2) if avaliadas else None
        return {"media": media, "quantidade_avaliada": len(avaliadas)}


class RelatorioTopAvaliadas(EstrategiaRelatorio):
    def gerar(self, colecao: Colecao) -> dict[str, object]:
        avaliadas = [
            publicacao
            for publicacao in colecao.publicacoes.values()
            if publicacao.status is StatusLeitura.LIDO
            and publicacao.nota is not None
        ]
        if len(avaliadas) < 5:
            return {
                "suficiente": False,
                "mensagem": (
                    "Não há informações suficientes no acervo para gerar "
                    "o ranking das 5 publicações mais bem avaliadas."
                ),
                "publicacoes": [],
            }
        melhores = sorted(
            avaliadas, key=lambda publicacao: (-publicacao.nota, publicacao.titulo.casefold())
        )[:5]
        return {
            "suficiente": True,
            "mensagem": None,
            "publicacoes": [
                {
                    "id": publicacao.id,
                    "titulo": publicacao.titulo,
                    "autor": publicacao.autor,
                    "tipo": publicacao.tipo(),
                    "nota": publicacao.nota,
                }
                for publicacao in melhores
            ],
        }


class RelatorioProgressoAnual(EstrategiaRelatorio):
    def __init__(self, meta: int, ano: int) -> None:
        if isinstance(meta, bool) or not isinstance(meta, int) or meta < 0:
            raise ValueError("A meta anual deve ser um valor inteiro não negativo")
        if isinstance(ano, bool) or not isinstance(ano, int):
            raise ValueError("O ano deve ser um valor inteiro")
        self._meta = meta
        self._ano = ano

    def gerar(self, colecao: Colecao) -> dict[str, object]:
        concluidas = sum(
            publicacao.status is StatusLeitura.LIDO
            and publicacao.data_termino is not None
            and publicacao.data_termino.year == self._ano
            for publicacao in colecao.publicacoes.values()
        )

        if self._meta:
            percentual = round(concluidas / self._meta * 100, 2)
            aviso = "Meta atingida" if concluidas >= self._meta else "Meta pendente"
        else:
            percentual = None
            aviso = "Nenhuma meta anual definida"

        return {
            "concluidas": concluidas,
            "meta": self._meta,
            "percentual_atingido": percentual,
            "aviso": aviso,
        }

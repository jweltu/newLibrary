from datetime import date

from bib.excecoes import (
    PublicacaoDuplicadaError,
    PublicacaoNaoEncontradaError,
    ValidacaoError,
)
from bib.models.enums import StatusLeitura
from bib.models.publicacao import Publicacao


class Colecao:
    def __init__(self, publicacoes=None):
        self._publicacoes = dict(publicacoes or {})

    @property
    def publicacoes(self):
        return self._publicacoes

    def __len__(self):
        return len(self._publicacoes)

    def __iter__(self):
        return iter(self._publicacoes.values())

    def adicionar(self, pub):
        if not isinstance(pub, Publicacao):
            raise ValidacaoError("A coleção aceita somente publicações válidas")

        if pub.id in self._publicacoes or self.existe(pub.titulo, pub.autor):
            raise PublicacaoDuplicadaError(
                f"A publicação '{pub.titulo}' de '{pub.autor}' já está na coleção"
            )

        self._publicacoes[pub.id] = pub

    def remover(self, id):
        try:
            self._publicacoes.pop(id)
        except KeyError:
            raise PublicacaoNaoEncontradaError(
                f"Publicação com ID {id!r} não encontrada"
            ) from None

    def obter(self, id):
        try:
            return self._publicacoes[id]
        except KeyError:
            raise PublicacaoNaoEncontradaError(
                f"Publicação com ID {id!r} não encontrada"
            ) from None

    def existe(self, titulo, autor):
        if not isinstance(titulo, str) or not isinstance(autor, str):
            raise ValidacaoError("Título e autor devem ser textos")
        titulo_busca = titulo.strip().casefold()
        autor_busca = autor.strip().casefold()
        return any(
            publicacao.titulo.casefold() == titulo_busca
            and publicacao.autor.casefold() == autor_busca
            for publicacao in self._publicacoes.values()
        )

    def buscar(self, titulo=None, autor=None, genero=None, status=None):
        status_busca = self._normalizar_status(status) if status is not None else None
        filtros_texto = {
            "titulo": titulo,
            "autor": autor,
            "genero": genero,
        }
        if any(
            valor is not None and not isinstance(valor, str)
            for valor in filtros_texto.values()
        ):
            raise ValidacaoError("Os filtros de texto devem ser strings")
        return [
            publicacao
            for publicacao in self._publicacoes.values()
            if all(
                valor is None
                or valor.strip().casefold()
                in getattr(publicacao, campo).casefold()
                for campo, valor in filtros_texto.items()
            )
            and (status_busca is None or publicacao.status is status_busca)
        ]

    def filtrar(self, inicio, fim):
        if not isinstance(inicio, date) or not isinstance(fim, date):
            raise ValidacaoError("O período deve usar datas válidas")
        if inicio > fim:
            raise ValidacaoError("A data inicial não pode ser posterior à data final")
        return [
            publicacao
            for publicacao in self._publicacoes.values()
            if publicacao.data_inclusao is not None
            and inicio <= publicacao.data_inclusao <= fim
        ]

    def filtrar_por_periodo(self, inicio, fim):
        return self.filtrar(inicio, fim)

    def em_leitura(self):
        return self.buscar(status=StatusLeitura.LENDO)

    def concluidas_no_ano(self, ano):
        if isinstance(ano, bool) or not isinstance(ano, int):
            raise ValidacaoError("O ano deve ser um inteiro")
        return sum(
            publicacao.status is StatusLeitura.LIDO
            and publicacao.data_termino is not None
            and publicacao.data_termino.year == ano
            for publicacao in self._publicacoes.values()
        )

    def contar_por_status(self, status):
        status_busca = self._normalizar_status(status)
        return sum(
            publicacao.status is status_busca
            for publicacao in self._publicacoes.values()
        )

    def ordenadas(self):
        return sorted(self._publicacoes.values())

    @staticmethod
    def _normalizar_status(status):
        if isinstance(status, StatusLeitura):
            return status
        try:
            return StatusLeitura(status)
        except (TypeError, ValueError):
            if isinstance(status, str):
                try:
                    return StatusLeitura[status]
                except KeyError:
                    pass
            raise ValidacaoError("Status de leitura inválido") from None

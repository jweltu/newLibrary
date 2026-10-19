import json

from bib.models.colecao import Colecao
from bib.models.livro import Livro
from bib.models.revista import Revista
from bib.repository.base import RepositorioPublicacoes


class RepositorioJSON(RepositorioPublicacoes):
    def __init__(self, caminho):
        self._caminho = caminho

    def salvar(self, colecao):
        dados = []
        for publicacao in colecao.publicacoes.values():
            registro = publicacao.to_dict()
            registro["tipo"] = publicacao.tipo()
            dados.append(registro)

        with open(self._caminho, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)

    def carregar(self):
        with open(self._caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if not isinstance(dados, list):
            raise ValueError("O arquivo JSON deve conter uma lista de publicações")

        publicacoes = {}
        tipos = {"livro": Livro, "revista": Revista}
        for registro in dados:
            if not isinstance(registro, dict):
                raise ValueError("Cada publicação no arquivo JSON deve ser um objeto")

            tipo = registro.get("tipo")
            if tipo is None:
                if "editora" in registro or "isbn" in registro:
                    tipo = "livro"
                elif "edicao" in registro or "issn" in registro:
                    tipo = "revista"

            classe = tipos.get(tipo)
            if classe is None:
                raise ValueError(f"Tipo de publicação inválido no arquivo JSON: {tipo!r}")

            publicacao = classe.from_dict(registro)
            if publicacao.id in publicacoes:
                raise ValueError(f"ID de publicação duplicado no arquivo JSON: {publicacao.id!r}")
            publicacoes[publicacao.id] = publicacao

        return Colecao(publicacoes)
from bib.repository.base import RepositorioPublicacoes

class RepositorioJSON(RepositorioPublicacoes):
    def __init__(self, caminho):
        self._caminho = caminho

    def salvar(self, colecao):
        pass

    def carregar(self):
        pass
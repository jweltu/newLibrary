from bib.repository.base import RepositorioPublicacoes
from bib.models.colecao import Colecao

class RepositorioSQLite(RepositorioPublicacoes):
    def __init__(self, caminho_db):
        self._caminho_db = caminho_db

    def salvar(self, colecao: Colecao):
        pass

    def carregar(self):
        pass
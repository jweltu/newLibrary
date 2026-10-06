from datetime import date

import pytest  # type: ignore[import-not-found]

from bib.models.enums import StatusLeitura
from bib.models.livro import Livro
from bib.models.revista import Revista


@pytest.fixture
def livro_factory():
    def criar_livro(**alteracoes):
        dados = {
            "titulo": "Dom Casmurro",
            "autor": "Machado de Assis",
            "ano": 1899,
            "nota": None,
            "status": StatusLeitura.NAO_LIDO,
            "id": "livro-1",
            "genero": "romance",
            "paginas": 256,
            "pagina_atual": 0,
            "data_inclusao": date(2026, 10, 6),
            "data_inicio": None,
            "data_termino": None,
            "resenha": None,
            "anotacoes": [],
            "estado": None,
            "editora": "Garnier",
            "isbn": "978-85-359-0277-5",
        }
        dados.update(alteracoes)
        return Livro(**dados)

    return criar_livro


@pytest.fixture
def revista_factory():
    def criar_revista(**alteracoes):
        dados = {
            "titulo": "Revista de História",
            "autor": "Equipe Editorial",
            "ano": 2024,
            "nota": None,
            "status": StatusLeitura.NAO_LIDO,
            "id": "revista-1",
            "genero": "história",
            "paginas": 80,
            "pagina_atual": 0,
            "data_inclusao": date(2026, 10, 6),
            "data_inicio": None,
            "data_termino": None,
            "resenha": None,
            "anotacoes": [],
            "estado": None,
            "edicao": "42",
            "issn": "0100-1234",
        }
        dados.update(alteracoes)
        return Revista(**dados)

    return criar_revista
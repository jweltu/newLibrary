from datetime import date

from bib.models.enums import StatusLeitura
from bib.models.livro import Livro
from bib.models.revista import Revista


def test_cria_livro_com_atributos_informados(livro_factory):
    livro = livro_factory(nota=8.5, pagina_atual=12)

    assert isinstance(livro, Livro)
    assert livro.tipo() == "livro"
    assert livro.titulo == "Dom Casmurro"
    assert livro.autor == "Machado de Assis"
    assert livro.ano == 1899
    assert livro.nota == 8.5
    assert livro.status is StatusLeitura.NAO_LIDO
    assert livro.id == "livro-1"
    assert livro.genero == "romance"
    assert livro.paginas == 256
    assert livro.pagina_atual == 12
    assert livro.data_inclusao == date(2026, 10, 6)
    assert livro.editora == "Garnier"
    assert livro.isbn == "978-85-359-0277-5"


def test_cria_revista_com_atributos_informados(revista_factory):
    revista = revista_factory(status="LENDO", pagina_atual=10)

    assert isinstance(revista, Revista)
    assert revista.tipo() == "revista"
    assert revista.titulo == "Revista de História"
    assert revista.status is StatusLeitura.LENDO
    assert revista.edicao == "42"
    assert revista.issn == "0100-1234"


def test_cria_lista_de_anotacoes_independente_por_objeto(livro_factory):
    primeiro = livro_factory()
    segundo = livro_factory()

    anotacao = primeiro.adicionar_anotacao("Uma observação")

    assert primeiro.anotacoes == [anotacao]
    assert segundo.anotacoes == []

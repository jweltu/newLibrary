import json

from bib.dados import carregar_publicacoes, salvar_publicacoes
from bib.models.colecao import Colecao
from bib.models.enums import CategoriaAnotacao
from bib.models.livro import Livro
from bib.models.revista import Revista
from bib.repository.json_repo import RepositorioJSON
from bib.repository.sqlite_repo import RepositorioSQLite


def test_repositorio_json_persiste_publicacoes_e_anotacoes(
    tmp_path, livro_factory, revista_factory
):
    livro = livro_factory()
    anotacao_livro = livro.adicionar_anotacao(
        "Uma passagem importante",
        trecho="Trecho destacado",
        pagina=12,
        categoria=CategoriaAnotacao.DESTAQUE,
    )
    revista = revista_factory()
    anotacao_revista = revista.adicionar_anotacao("Revisar esta edição")
    caminho = tmp_path / "publicacoes.json"
    repositorio = RepositorioJSON(caminho)

    repositorio.salvar(Colecao({livro.id: livro, revista.id: revista}))
    carregada = repositorio.carregar()

    livro_carregado = carregada.publicacoes[livro.id]
    revista_carregada = carregada.publicacoes[revista.id]
    assert isinstance(livro_carregado, Livro)
    assert isinstance(revista_carregada, Revista)
    assert livro_carregado.to_dict()["anotacoes"] == [anotacao_livro.to_dict()]
    assert revista_carregada.to_dict()["anotacoes"] == [anotacao_revista.to_dict()]
    assert livro_carregado.to_dict() == livro.to_dict()
    assert revista_carregada.to_dict() == revista.to_dict()


def test_funcoes_de_dados_persistem_lista_json(tmp_path, livro_factory):
    livro = livro_factory()
    livro.adicionar_anotacao("Nota persistida")
    caminho = tmp_path / "publicacoes.json"

    salvar_publicacoes(Colecao({livro.id: livro}), caminho)

    with caminho.open(encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    carregada = carregar_publicacoes(caminho)

    assert dados[0]["tipo"] == "livro"
    assert dados[0]["anotacoes"][0]["texto"] == "Nota persistida"
    assert carregada.publicacoes[livro.id].to_dict() == livro.to_dict()


def test_repositorio_sqlite_persiste_livros_revistas_e_anotacoes(
    tmp_path, livro_factory, revista_factory
):
    livro = livro_factory()
    anotacao_livro = livro.adicionar_anotacao(
        "Uma passagem importante",
        trecho="Trecho destacado",
        pagina=12,
        categoria=CategoriaAnotacao.DESTAQUE,
    )
    revista = revista_factory()
    anotacao_revista = revista.adicionar_anotacao("Revisar esta edição")
    caminho = tmp_path / "dados" / "publicacoes.db"
    repositorio = RepositorioSQLite(caminho)

    assert repositorio.carregar().publicacoes == {}
    repositorio.salvar(Colecao({livro.id: livro, revista.id: revista}))
    carregada = repositorio.carregar()

    assert isinstance(carregada.publicacoes[livro.id], Livro)
    assert isinstance(carregada.publicacoes[revista.id], Revista)
    assert carregada.publicacoes[livro.id].to_dict() == livro.to_dict()
    assert carregada.publicacoes[revista.id].to_dict() == revista.to_dict()
    assert carregada.publicacoes[livro.id].anotacoes[0].to_dict() == anotacao_livro.to_dict()
    assert carregada.publicacoes[revista.id].anotacoes[0].to_dict() == anotacao_revista.to_dict()


def test_funcoes_de_dados_persistem_sqlite(tmp_path, livro_factory):
    livro = livro_factory()
    caminho = tmp_path / "publicacoes.db"

    salvar_publicacoes(Colecao({livro.id: livro}), caminho, formato="sqlite")
    carregada = carregar_publicacoes(caminho, formato="sqlite")

    assert carregada.publicacoes[livro.id].to_dict() == livro.to_dict()
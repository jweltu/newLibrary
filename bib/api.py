"""API HTTP da biblioteca pessoal."""

import os
from datetime import date
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from bib.excecoes import (
    BibliotecaError,
    PublicacaoDuplicadaError,
    PublicacaoNaoEncontradaError,
)
from bib.models.colecao import Colecao
from bib.models.enums import CategoriaAnotacao, StatusLeitura
from bib.models.livro import Livro
from bib.models.publicacao import Publicacao
from bib.models.revista import Revista
from bib.relatorio import (
    RelatorioMediaAvaliacoes,
    RelatorioPorStatus,
    RelatorioProgressoAnual,
    RelatorioTotal,
)
from bib.repository import criar_repositorio


class PublicacaoEntrada(BaseModel):
    tipo: Literal["livro", "revista"]
    titulo: str
    autor: str
    ano: int = Field(ge=1500)
    paginas: int = Field(gt=0)
    genero: str = "Sem gênero"
    status: Literal["NAO_LIDO", "LENDO", "LIDO"] = "NAO_LIDO"
    editora: str | None = None
    isbn: str | None = None
    edicao: str | None = None
    issn: str | None = None


class AnotacaoEntrada(BaseModel):
    texto: str
    trecho: str | None = None
    pagina: int | None = Field(default=None, ge=1)
    categoria: Literal["anotacao", "destaque"] = "anotacao"


_STATUS = {status.name: status for status in StatusLeitura}
_FORMATO_PADRAO = os.environ.get("BIB_FORMATO", "json")
_ARQUIVO_CONFIGURADO = os.environ.get("BIB_ARQUIVO")


def _carregar(arquivo: Path, formato: str) -> Colecao:
    return criar_repositorio(formato, arquivo).carregar()


def _salvar(arquivo: Path, formato: str, colecao: Colecao) -> None:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    criar_repositorio(formato, arquivo).salvar(colecao)


def _serializar_publicacao(publicacao: Publicacao) -> dict[str, object]:
    dados = publicacao.to_dict()
    dados["tipo"] = publicacao.tipo()
    return dados


def create_app(
    arquivo: Path | str | None = None, formato: str | None = None
) -> FastAPI:
    """Cria a aplicação, permitindo configurar arquivo e formato do acervo."""
    formato_persistencia = formato if formato is not None else _FORMATO_PADRAO
    if formato_persistencia not in ("json", "sqlite"):
        raise ValueError(f"Formato de persistência inválido: {formato_persistencia!r}")
    if arquivo is not None:
        caminho = Path(arquivo)
    elif _ARQUIVO_CONFIGURADO:
        caminho = Path(_ARQUIVO_CONFIGURADO)
    else:
        extensao = "json" if formato_persistencia == "json" else "db"
        caminho = Path.home() / ".bib" / f"publicacoes.{extensao}"
    app = FastAPI(title="NewLibrary API", version="0.1.0")

    @app.exception_handler(BibliotecaError)
    async def tratar_erro_dominio(
        request: Request, erro: BibliotecaError
    ) -> JSONResponse:
        if isinstance(erro, PublicacaoNaoEncontradaError):
            status_code = 404
        elif isinstance(erro, PublicacaoDuplicadaError):
            status_code = 409
        else:
            status_code = 422
        return JSONResponse(status_code=status_code, content={"detail": str(erro)})

    @app.get("/publicacoes")
    def listar_publicacoes(
        titulo: str | None = None,
        autor: str | None = None,
        genero: str | None = None,
        status: Literal["NAO_LIDO", "LENDO", "LIDO"] | None = None,
    ) -> list[dict[str, object]]:
        colecao = _carregar(caminho, formato_persistencia)
        resultado = colecao.buscar(
            titulo=titulo,
            autor=autor,
            genero=genero,
            status=_STATUS[status] if status else None,
        )
        return [_serializar_publicacao(item) for item in sorted(resultado)]

    @app.post("/publicacoes", status_code=201)
    def cadastrar_publicacao(entrada: PublicacaoEntrada) -> dict[str, object]:
        colecao = _carregar(caminho, formato_persistencia)
        dados = entrada.model_dump()
        tipo = dados.pop("tipo")
        status = _STATUS[dados.pop("status")]
        dados.update(
            id=str(uuid4()),
            nota=None,
            status=status,
            pagina_atual=0,
            data_inclusao=date.today(),
            data_inicio=None,
            data_termino=None,
            resenha=None,
            anotacoes=[],
            estado=None,
        )
        if tipo == "livro":
            dados.pop("edicao")
            dados.pop("issn")
            publicacao = Livro(**dados)
        else:
            dados.pop("editora")
            dados.pop("isbn")
            publicacao = Revista(**dados)
        colecao.adicionar(publicacao)
        _salvar(caminho, formato_persistencia, colecao)
        return _serializar_publicacao(publicacao)

    @app.get("/publicacoes/{publicacao_id}")
    def obter_publicacao(publicacao_id: str) -> dict[str, object]:
        publicacao = _carregar(caminho, formato_persistencia).obter(publicacao_id)
        return _serializar_publicacao(publicacao)

    @app.post("/publicacoes/{publicacao_id}/anotacoes", status_code=201)
    def adicionar_anotacao(
        publicacao_id: str, entrada: AnotacaoEntrada
    ) -> dict[str, object]:
        colecao = _carregar(caminho, formato_persistencia)
        publicacao = colecao.obter(publicacao_id)
        anotacao = publicacao.adicionar_anotacao(
            entrada.texto,
            trecho=entrada.trecho,
            pagina=entrada.pagina,
            categoria=CategoriaAnotacao(entrada.categoria),
        )
        _salvar(caminho, formato_persistencia, colecao)
        return anotacao.to_dict()

    @app.get("/relatorios/{tipo}")
    def gerar_relatorio(
        tipo: Literal["completo", "total", "status", "media", "anual"],
        meta: int = Query(default=0, ge=0),
        ano: int | None = Query(default=None, ge=1500),
    ) -> dict[str, object]:
        colecao = _carregar(caminho, formato_persistencia)
        ano_relatorio = ano if ano is not None else date.today().year
        relatorios = {
            "total": lambda: RelatorioTotal().gerar(colecao),
            "status": lambda: RelatorioPorStatus().gerar(colecao),
            "media": lambda: RelatorioMediaAvaliacoes().gerar(colecao),
            "anual": lambda: RelatorioProgressoAnual(meta, ano_relatorio).gerar(
                colecao
            ),
        }
        if tipo == "completo":
            return {
                "total": relatorios["total"](),
                "status": relatorios["status"](),
                "avaliacoes": relatorios["media"](),
            }
        return relatorios[tipo]()

    return app


app = create_app()

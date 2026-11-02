"""API HTTP da biblioteca pessoal."""

import os
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from bib.config import Configuracoes
from bib.excecoes import (
    BibliotecaError,
    LimiteLeiturasError,
    PublicacaoDuplicadaError,
    PublicacaoNaoEncontradaError,
    ValidacaoError,
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
    RelatorioTopAvaliadas,
    RelatorioTotal,
)
from bib.repository.sqlite_repo import RepositorioSQLite


class PublicacaoEntrada(BaseModel):
    tipo: Literal["livro", "revista"]
    titulo: str
    autor: str
    ano: int = Field(ge=1500)
    paginas: int = Field(gt=0)
    genero: str | None = None
    editora: str | None = None
    isbn: str | None = None
    edicao: str | None = None
    issn: str | None = None


class AnotacaoEntrada(BaseModel):
    texto: str
    trecho: str | None = None
    pagina: int | None = Field(default=None, ge=1)
    categoria: Literal["anotacao", "destaque"] = "anotacao"


class PublicacaoAtualizacao(BaseModel):
    tipo: Literal["livro", "revista"] | None = None
    titulo: str | None = None
    autor: str | None = None
    ano: int | None = Field(default=None, ge=1500)
    genero: str | None = None
    paginas: int | None = Field(default=None, gt=0)
    nota: float | None = Field(default=None, ge=0, le=10)
    resenha: str | None = None
    editora: str | None = None
    isbn: str | None = None
    edicao: str | None = None
    issn: str | None = None


class StatusEntrada(BaseModel):
    acao: Literal["iniciar", "concluir"]


class ConfiguracoesAtualizacao(BaseModel):
    genero_favorito: str | None = None
    limite_leituras_simultaneas: int | None = Field(default=None, ge=1)
    meta_anual: int | None = Field(default=None, ge=0)


_STATUS = {status.name: status for status in StatusLeitura}
_ARQUIVO_CONFIGURADO = os.environ.get("BIB_ARQUIVO")


def _carregar(arquivo: Path) -> Colecao:
    return RepositorioSQLite(arquivo).carregar()


def _salvar(arquivo: Path, colecao: Colecao) -> None:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    RepositorioSQLite(arquivo).salvar(colecao)


def _serializar_publicacao(publicacao: Publicacao) -> dict[str, object]:
    dados = publicacao.to_dict()
    dados["tipo"] = publicacao.tipo()
    return dados


def create_app(arquivo: Path | str | None = None) -> FastAPI:
    """Cria a aplicação, permitindo configurar o caminho do banco SQLite."""
    if arquivo is not None:
        caminho = Path(arquivo)
    elif _ARQUIVO_CONFIGURADO:
        caminho = Path(_ARQUIVO_CONFIGURADO)
    else:
        caminho = Path.home() / ".bib" / "publicacoes.db"
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
        inicio: date | None = None,
        fim: date | None = None,
    ) -> list[dict[str, object]]:
        if (inicio is None) != (fim is None):
            raise ValidacaoError("Informe as datas inicial e final do período de leitura")
        colecao = _carregar(caminho)
        resultado = colecao.buscar(
            titulo=titulo,
            autor=autor,
            genero=genero,
            status=_STATUS[status] if status else None,
        )
        if inicio is not None and fim is not None:
            ids_no_periodo = {
                publicacao.id
                for publicacao in colecao.filtrar_por_periodo_leitura(inicio, fim)
            }
            resultado = [
                publicacao for publicacao in resultado if publicacao.id in ids_no_periodo
            ]
        return [_serializar_publicacao(item) for item in sorted(resultado)]

    @app.post("/publicacoes", status_code=201)
    def cadastrar_publicacao(entrada: PublicacaoEntrada) -> dict[str, object]:
        colecao = _carregar(caminho)
        dados = entrada.model_dump()
        tipo = dados.pop("tipo")
        dados["genero"] = (
            dados["genero"]
            or Configuracoes.carregar().genero_favorito
            or "Sem gênero"
        )
        dados.update(
            id=colecao.proximo_id(),
            nota=None,
            status=StatusLeitura.NAO_LIDO,
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
        _salvar(caminho, colecao)
        return _serializar_publicacao(publicacao)

    @app.get("/publicacoes/{publicacao_id}")
    def obter_publicacao(publicacao_id: str) -> dict[str, object]:
        publicacao = _carregar(caminho).obter(publicacao_id)
        return _serializar_publicacao(publicacao)

    @app.patch("/publicacoes/{publicacao_id}")
    def atualizar_publicacao(
        publicacao_id: str, entrada: PublicacaoAtualizacao
    ) -> dict[str, object]:
        colecao = _carregar(caminho)
        publicacao = colecao.obter(publicacao_id)
        alteracoes = entrada.model_dump(exclude_unset=True)
        tipo = alteracoes.pop("tipo", None) or publicacao.tipo()
        if "nota" in alteracoes and alteracoes["nota"] is not None:
            if publicacao.status is not StatusLeitura.LIDO:
                raise ValidacaoError("A publicação só pode ser avaliada após a leitura")
        titulo = alteracoes.get("titulo", publicacao.titulo)
        autor = alteracoes.get("autor", publicacao.autor)
        if any(not isinstance(valor, str) or not valor.strip() for valor in (titulo, autor)):
            raise ValidacaoError("Título e autor não podem ser vazios")
        if (titulo.strip().casefold(), autor.strip().casefold()) != (
            publicacao.titulo.casefold(),
            publicacao.autor.casefold(),
        ) and any(
            item.id != publicacao.id
            and item.titulo.casefold() == titulo.strip().casefold()
            and item.autor.casefold() == autor.strip().casefold()
            for item in colecao
        ):
            raise PublicacaoDuplicadaError(
                f"A publicação '{titulo}' de '{autor}' já está na coleção"
            )

        dados = publicacao.to_dict()
        dados.update(alteracoes)
        for campo in ("editora", "isbn", "edicao", "issn"):
            dados.pop(campo, None)
        classe = Livro if tipo == "livro" else Revista
        if tipo == "livro":
            dados["editora"] = alteracoes.get("editora", getattr(publicacao, "editora", None))
            dados["isbn"] = alteracoes.get("isbn", getattr(publicacao, "isbn", None))
        else:
            dados["edicao"] = alteracoes.get("edicao", getattr(publicacao, "edicao", None))
            dados["issn"] = alteracoes.get("issn", getattr(publicacao, "issn", None))
        substituta = classe.from_dict(dados)
        colecao.publicacoes[publicacao.id] = substituta
        _salvar(caminho, colecao)
        return _serializar_publicacao(substituta)

    @app.delete("/publicacoes/{publicacao_id}", status_code=204)
    def remover_publicacao(publicacao_id: str) -> None:
        colecao = _carregar(caminho)
        colecao.remover(publicacao_id)
        _salvar(caminho, colecao)

    @app.patch("/publicacoes/{publicacao_id}/status")
    def alterar_status(
        publicacao_id: str, entrada: StatusEntrada
    ) -> dict[str, object]:
        colecao = _carregar(caminho)
        publicacao = colecao.obter(publicacao_id)
        if entrada.acao == "iniciar":
            configuracoes = Configuracoes.carregar()
            if (
                publicacao.status is StatusLeitura.NAO_LIDO
                and colecao.contar_por_status(StatusLeitura.LENDO)
                >= configuracoes.limite_leituras_simultaneas
            ):
                raise LimiteLeiturasError(
                    "O limite de leituras simultâneas configurado foi atingido"
                )
            publicacao.iniciar_leitura()
        else:
            publicacao.concluir_leitura()
        _salvar(caminho, colecao)
        return _serializar_publicacao(publicacao)

    @app.patch("/publicacoes/{publicacao_id}/progresso")
    def atualizar_progresso(
        publicacao_id: str, pagina: int = Query(ge=0)
    ) -> dict[str, object]:
        colecao = _carregar(caminho)
        publicacao = colecao.obter(publicacao_id)
        publicacao.atualizar_progresso(pagina)
        _salvar(caminho, colecao)
        return _serializar_publicacao(publicacao)

    @app.post("/publicacoes/{publicacao_id}/avaliacao")
    def avaliar_publicacao(
        publicacao_id: str, nota: float = Query(ge=0, le=10), resenha: str | None = None
    ) -> dict[str, object]:
        colecao = _carregar(caminho)
        publicacao = colecao.obter(publicacao_id)
        publicacao.avaliar(nota, resenha)
        _salvar(caminho, colecao)
        return _serializar_publicacao(publicacao)

    @app.get("/publicacoes/{publicacao_id}/anotacoes")
    def listar_anotacoes(publicacao_id: str) -> list[dict[str, object]]:
        publicacao = _carregar(caminho).obter(publicacao_id)
        return [anotacao.to_dict() for anotacao in publicacao.listar_anotacoes()]

    @app.post("/publicacoes/{publicacao_id}/anotacoes", status_code=201)
    def adicionar_anotacao(
        publicacao_id: str, entrada: AnotacaoEntrada
    ) -> dict[str, object]:
        colecao = _carregar(caminho)
        publicacao = colecao.obter(publicacao_id)
        anotacao = publicacao.adicionar_anotacao(
            entrada.texto,
            trecho=entrada.trecho,
            pagina=entrada.pagina,
            categoria=CategoriaAnotacao(entrada.categoria),
        )
        _salvar(caminho, colecao)
        return anotacao.to_dict()

    @app.get("/relatorios/{tipo}")
    def gerar_relatorio(
        tipo: Literal["completo", "total", "status", "media", "top5", "anual"],
        meta: int | None = Query(default=None, ge=0),
        ano: int | None = Query(default=None, ge=1500),
    ) -> dict[str, object]:
        colecao = _carregar(caminho)
        meta_relatorio = (
            meta
            if meta is not None
            else Configuracoes.carregar().meta_anual
        )
        ano_relatorio = ano if ano is not None else date.today().year
        relatorios = {
            "total": lambda: RelatorioTotal().gerar(colecao),
            "status": lambda: RelatorioPorStatus().gerar(colecao),
            "media": lambda: RelatorioMediaAvaliacoes().gerar(colecao),
            "top5": lambda: RelatorioTopAvaliadas().gerar(colecao),
            "anual": lambda: RelatorioProgressoAnual(meta_relatorio, ano_relatorio).gerar(
                colecao
            ),
        }
        if tipo == "completo":
            return {
                "total": relatorios["total"](),
                "status": relatorios["status"](),
                "avaliacoes": relatorios["media"](),
                "melhores_avaliadas": relatorios["top5"](),
            }
        return relatorios[tipo]()

    @app.get("/configuracoes")
    def obter_configuracoes() -> dict[str, object]:
        configuracoes = Configuracoes.carregar()
        return {
            "genero_favorito": configuracoes.genero_favorito,
            "limite_leituras_simultaneas": configuracoes.limite_leituras_simultaneas,
            "meta_anual": configuracoes.meta_anual,
        }

    @app.put("/configuracoes")
    def atualizar_configuracoes(
        entrada: ConfiguracoesAtualizacao,
    ) -> dict[str, object]:
        configuracoes = Configuracoes.carregar()
        for campo, valor in entrada.model_dump(exclude_unset=True).items():
            setattr(configuracoes, campo, valor)
        configuracoes.salvar()
        return obter_configuracoes()

    return app


app = create_app()

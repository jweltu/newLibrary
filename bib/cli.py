"""Interface de linha de comando para a biblioteca pessoal."""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

from bib.excecoes import BibliotecaError
from bib.models.colecao import Colecao
from bib.models.enums import CategoriaAnotacao, StatusLeitura
from bib.models.livro import Livro
from bib.models.revista import Revista
from bib.relatorio import (
    RelatorioMediaAvaliacoes,
    RelatorioPorStatus,
    RelatorioProgressoAnual,
    RelatorioTotal,
)
from bib.repository import criar_repositorio


_DIRETORIO_PADRAO = Path.home() / ".bib"
_STATUS = {status.name.lower(): status for status in StatusLeitura}


def _adicionar_arquivo(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--arquivo",
        type=Path,
        help="caminho do arquivo do acervo (a extensão padrão depende do formato)",
    )
    parser.add_argument(
        "--formato",
        choices=("json", "sqlite"),
        default="json",
        help="formato de persistência (padrão: json)",
    )


def _criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bib",
        description="Gerencie seu acervo pessoal de livros e revistas.",
    )
    subcomandos = parser.add_subparsers(dest="comando", required=True)

    cadastrar = subcomandos.add_parser("cadastrar", help="cadastra uma publicação")
    _adicionar_arquivo(cadastrar)
    cadastrar.add_argument("tipo", choices=("livro", "revista"))
    cadastrar.add_argument("--titulo", required=True)
    cadastrar.add_argument("--autor", required=True)
    cadastrar.add_argument("--ano", required=True, type=int)
    cadastrar.add_argument("--paginas", required=True, type=int)
    cadastrar.add_argument("--genero", default="Sem gênero")
    cadastrar.add_argument(
        "--status", choices=tuple(_STATUS), default=StatusLeitura.NAO_LIDO.name.lower()
    )
    cadastrar.add_argument("--editora")
    cadastrar.add_argument("--isbn")
    cadastrar.add_argument("--edicao")
    cadastrar.add_argument("--issn")
    cadastrar.set_defaults(func=_cadastrar)

    listar = subcomandos.add_parser("listar", help="lista publicações do acervo")
    _adicionar_arquivo(listar)
    listar.add_argument("--titulo")
    listar.add_argument("--autor")
    listar.add_argument("--genero")
    listar.add_argument("--status", choices=tuple(_STATUS))
    listar.set_defaults(func=_listar)

    anotar = subcomandos.add_parser("anotar", help="adiciona uma anotação")
    _adicionar_arquivo(anotar)
    anotar.add_argument("id", help="ID da publicação")
    anotar.add_argument("--texto", required=True)
    anotar.add_argument("--trecho")
    anotar.add_argument("--pagina", type=int)
    anotar.add_argument(
        "--categoria",
        choices=tuple(categoria.value for categoria in CategoriaAnotacao),
        default=CategoriaAnotacao.ANOTACAO.value,
    )
    anotar.set_defaults(func=_anotar)

    relatorio = subcomandos.add_parser("relatorio", help="gera um relatório do acervo")
    _adicionar_arquivo(relatorio)
    relatorio.add_argument(
        "--tipo",
        choices=("completo", "total", "status", "media", "anual"),
        default="completo",
    )
    relatorio.add_argument(
        "--meta", type=int, default=0, help="meta de leituras para o relatório anual"
    )
    relatorio.add_argument(
        "--ano",
        type=int,
        default=date.today().year,
        help="ano do relatório de progresso anual",
    )
    relatorio.set_defaults(func=_relatorio)
    return parser


def _caminho_arquivo(args: argparse.Namespace) -> Path:
    if args.arquivo is not None:
        return args.arquivo
    extensao = "json" if args.formato == "json" else "db"
    return _DIRETORIO_PADRAO / f"publicacoes.{extensao}"


def _carregar(args: argparse.Namespace) -> Colecao:
    return criar_repositorio(args.formato, _caminho_arquivo(args)).carregar()


def _salvar(args: argparse.Namespace, colecao: Colecao) -> None:
    arquivo = _caminho_arquivo(args)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    criar_repositorio(args.formato, arquivo).salvar(colecao)


def _cadastrar(args: argparse.Namespace) -> int:
    colecao = _carregar(args)
    argumentos = {
        "titulo": args.titulo,
        "autor": args.autor,
        "ano": args.ano,
        "nota": None,
        "status": _STATUS[args.status],
        "id": str(uuid4()),
        "genero": args.genero,
        "paginas": args.paginas,
        "pagina_atual": 0,
        "data_inclusao": date.today(),
        "data_inicio": None,
        "data_termino": None,
        "resenha": None,
        "anotacoes": [],
        "estado": None,
    }
    if args.tipo == "livro":
        publicacao = Livro(**argumentos, editora=args.editora, isbn=args.isbn)
    else:
        publicacao = Revista(**argumentos, edicao=args.edicao, issn=args.issn)
    colecao.adicionar(publicacao)
    _salvar(args, colecao)
    print(f"Publicação cadastrada com ID {publicacao.id}: {publicacao.titulo}")
    return 0


def _listar(args: argparse.Namespace) -> int:
    colecao = _carregar(args)
    status = _STATUS[args.status] if args.status else None
    publicacoes = colecao.buscar(
        titulo=args.titulo,
        autor=args.autor,
        genero=args.genero,
        status=status,
    )
    if not publicacoes:
        print("Nenhuma publicação encontrada.")
        return 0

    for publicacao in sorted(publicacoes):
        print(
            f"[{publicacao.id}] {publicacao.tipo()}: {publicacao.titulo} - "
            f"{publicacao.autor} ({publicacao.ano}) | {publicacao.status.value} | "
            f"páginas {publicacao.pagina_atual}/{publicacao.paginas} | "
            f"anotações {len(publicacao.anotacoes)}"
        )
    return 0


def _anotar(args: argparse.Namespace) -> int:
    colecao = _carregar(args)
    publicacao = colecao.obter(args.id)
    anotacao = publicacao.adicionar_anotacao(
        args.texto,
        trecho=args.trecho,
        pagina=args.pagina,
        categoria=CategoriaAnotacao(args.categoria),
    )
    _salvar(args, colecao)
    print(f"Anotação registrada para {publicacao.titulo} (ID {anotacao.id}).")
    return 0


def _relatorio(args: argparse.Namespace) -> int:
    colecao = _carregar(args)
    relatorios = {
        "total": lambda: RelatorioTotal().gerar(colecao),
        "status": lambda: RelatorioPorStatus().gerar(colecao),
        "media": lambda: RelatorioMediaAvaliacoes().gerar(colecao),
        "anual": lambda: RelatorioProgressoAnual(args.meta, args.ano).gerar(colecao),
    }
    if args.tipo == "completo":
        resultado = {
            "total": relatorios["total"](),
            "status": relatorios["status"](),
            "avaliacoes": relatorios["media"](),
        }
    else:
        resultado = relatorios[args.tipo]()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Executa a CLI e retorna um código de saída."""
    args = _criar_parser().parse_args(argv)
    try:
        return args.func(args)
    except (BibliotecaError, ValueError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

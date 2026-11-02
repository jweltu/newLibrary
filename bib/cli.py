"""Interface de linha de comando para a biblioteca pessoal."""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from bib.config import Configuracoes
from bib.excecoes import BibliotecaError, LimiteLeiturasError, ValidacaoError
from bib.models.colecao import Colecao
from bib.models.enums import CategoriaAnotacao, StatusLeitura
from bib.models.livro import Livro
from bib.models.revista import Revista
from bib.relatorio import (
    RelatorioMediaAvaliacoes,
    RelatorioPorStatus,
    RelatorioProgressoAnual,
    RelatorioTopAvaliadas,
    RelatorioTotal,
)
from bib.repository.sqlite_repo import RepositorioSQLite


_DIRETORIO_PADRAO = Path.home() / ".bib"
_STATUS = {status.name.lower(): status for status in StatusLeitura}


def _adicionar_arquivo(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--arquivo",
        type=Path,
        help="caminho do banco SQLite do acervo",
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
    cadastrar.add_argument("--genero")
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
    listar.add_argument("--tipo", choices=("livro", "revista"))
    listar.add_argument("--inicio", type=date.fromisoformat)
    listar.add_argument("--fim", type=date.fromisoformat)
    listar.set_defaults(func=_listar)

    editar = subcomandos.add_parser("editar", help="altera uma publicação")
    _adicionar_arquivo(editar)
    editar.add_argument("id", help="ID da publicação")
    editar.add_argument("--tipo", choices=("livro", "revista"))
    editar.add_argument("--titulo")
    editar.add_argument("--autor")
    editar.add_argument("--ano", type=int)
    editar.add_argument("--genero")
    editar.add_argument("--paginas", type=int)
    editar.add_argument("--nota", type=float)
    editar.add_argument("--limpar-nota", action="store_true")
    editar.add_argument("--editora")
    editar.add_argument("--isbn")
    editar.add_argument("--edicao")
    editar.add_argument("--issn")
    editar.set_defaults(func=_editar)

    remover = subcomandos.add_parser("remover", help="remove uma publicação")
    _adicionar_arquivo(remover)
    remover.add_argument("id", help="ID da publicação")
    remover.set_defaults(func=_remover)

    status = subcomandos.add_parser("status", help="inicia ou conclui uma leitura")
    _adicionar_arquivo(status)
    status.add_argument("id", help="ID da publicação")
    status.add_argument("acao", choices=("iniciar", "concluir"))
    status.set_defaults(func=_alterar_status)

    avaliar = subcomandos.add_parser("avaliar", help="avalia uma publicação lida")
    _adicionar_arquivo(avaliar)
    avaliar.add_argument("id", help="ID da publicação")
    avaliar.add_argument("nota", type=float)
    avaliar.add_argument("--resenha")
    avaliar.set_defaults(func=_avaliar)

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

    anotacoes = subcomandos.add_parser(
        "anotacoes", help="lista as anotações de uma publicação"
    )
    _adicionar_arquivo(anotacoes)
    anotacoes.add_argument("id", help="ID da publicação")
    anotacoes.set_defaults(func=_listar_anotacoes)

    configuracoes = subcomandos.add_parser(
        "configuracoes", help="consulta ou altera as configurações"
    )
    configuracoes.add_argument("--genero-favorito")
    configuracoes.add_argument("--limpar-genero", action="store_true")
    configuracoes.add_argument("--limite-leituras", type=int)
    configuracoes.add_argument("--meta-anual", type=int)
    configuracoes.set_defaults(func=_configuracoes)

    relatorio = subcomandos.add_parser("relatorio", help="gera um relatório do acervo")
    _adicionar_arquivo(relatorio)
    relatorio.add_argument(
        "--tipo",
        choices=("completo", "total", "status", "media", "top5", "anual"),
        default="completo",
    )
    relatorio.add_argument(
        "--meta", type=int, help="meta de leituras para o relatório anual"
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
    return _DIRETORIO_PADRAO / "publicacoes.db"


def _carregar(args: argparse.Namespace) -> Colecao:
    return RepositorioSQLite(_caminho_arquivo(args)).carregar()


def _salvar(args: argparse.Namespace, colecao: Colecao) -> None:
    arquivo = _caminho_arquivo(args)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    RepositorioSQLite(arquivo).salvar(colecao)


def _cadastrar(args: argparse.Namespace) -> int:
    colecao = _carregar(args)
    argumentos = {
        "titulo": args.titulo,
        "autor": args.autor,
        "ano": args.ano,
        "nota": None,
        "status": StatusLeitura.NAO_LIDO,
        "id": colecao.proximo_id(),
        "genero": (
            args.genero
            or Configuracoes.carregar().genero_favorito
            or "Sem gênero"
        ),
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
    if (args.inicio is None) != (args.fim is None):
        raise ValidacaoError("Informe as datas inicial e final do período de leitura")
    publicacoes = colecao.buscar(
        titulo=args.titulo,
        autor=args.autor,
        genero=args.genero,
        status=status,
    )
    if args.tipo is not None:
        publicacoes = [
            publicacao
            for publicacao in publicacoes
            if publicacao.tipo() == args.tipo
        ]
    if args.inicio is not None and args.fim is not None:
        ids_no_periodo = {
            publicacao.id
            for publicacao in colecao.filtrar_por_periodo_leitura(
                args.inicio, args.fim
            )
        }
        publicacoes = [
            publicacao for publicacao in publicacoes if publicacao.id in ids_no_periodo
        ]
    if not publicacoes:
        print("Nenhuma publicação encontrada.")
        return 0

    for publicacao in sorted(publicacoes):
        print(
            f"[{publicacao.id}] {publicacao.tipo()}: {publicacao.titulo} - "
            f"{publicacao.autor} ({publicacao.ano}) | {publicacao.status.value} | "
            f"páginas {publicacao.pagina_atual}/{publicacao.paginas} | "
            f"avaliação {publicacao.nota if publicacao.nota is not None else '—'}/10 | "
            f"inclusão {publicacao.data_inclusao} | "
            f"anotações {len(publicacao.anotacoes)}"
        )
    return 0


def _editar(args: argparse.Namespace) -> int:
    colecao = _carregar(args)
    publicacao = colecao.obter(args.id)
    alteracoes = {
        campo: getattr(args, campo)
        for campo in ("titulo", "autor", "ano", "genero", "paginas")
        if getattr(args, campo) is not None
    }
    if args.nota is not None and args.limpar_nota:
        raise ValidacaoError("Escolha entre definir ou limpar a avaliação")
    if args.nota is not None and publicacao.status is not StatusLeitura.LIDO:
        raise ValidacaoError("A publicação só pode ser avaliada após a leitura")
    titulo = alteracoes.get("titulo", publicacao.titulo)
    autor = alteracoes.get("autor", publicacao.autor)
    if (titulo.strip().casefold(), autor.strip().casefold()) != (
        publicacao.titulo.casefold(),
        publicacao.autor.casefold(),
    ) and any(
        item.id != publicacao.id
        and item.titulo.casefold() == titulo.strip().casefold()
        and item.autor.casefold() == autor.strip().casefold()
        for item in colecao
    ):
        raise ValidacaoError("Já existe uma publicação com esse título e autor")

    for campo, valor in alteracoes.items():
        setattr(publicacao, campo, valor)
    if args.nota is not None:
        publicacao.avaliar(args.nota, publicacao.resenha)
    elif args.limpar_nota:
        publicacao.nota = None
        publicacao.resenha = None

    tipo_destino = args.tipo or publicacao.tipo()
    if tipo_destino != publicacao.tipo():
        dados = publicacao.to_dict()
        for campo in ("editora", "isbn", "edicao", "issn"):
            dados.pop(campo, None)
        tipo_publicacao = Livro if tipo_destino == "livro" else Revista
        dados.update(
            {"editora": None, "isbn": None}
            if tipo_destino == "livro"
            else {"edicao": None, "issn": None}
        )
        publicacao = tipo_publicacao.from_dict(dados)
        colecao.publicacoes[publicacao.id] = publicacao
    campos_especificos = (
        ("editora", "isbn") if tipo_destino == "livro" else ("edicao", "issn")
    )
    for campo in campos_especificos:
        valor = getattr(args, campo)
        if valor is not None:
            setattr(publicacao, campo, valor)
    _salvar(args, colecao)
    print(f"Publicação {publicacao.id} atualizada: {publicacao.titulo}")
    return 0


def _remover(args: argparse.Namespace) -> int:
    colecao = _carregar(args)
    publicacao = colecao.obter(args.id)
    colecao.remover(args.id)
    _salvar(args, colecao)
    print(f"Publicação removida: {publicacao.titulo}")
    return 0


def _alterar_status(args: argparse.Namespace) -> int:
    colecao = _carregar(args)
    publicacao = colecao.obter(args.id)
    if args.acao == "iniciar":
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
    _salvar(args, colecao)
    print(f"Status de {publicacao.titulo}: {publicacao.status.value}")
    return 0


def _avaliar(args: argparse.Namespace) -> int:
    colecao = _carregar(args)
    publicacao = colecao.obter(args.id)
    publicacao.avaliar(args.nota, args.resenha)
    _salvar(args, colecao)
    print(f"Avaliação registrada: {publicacao.nota}/10")
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


def _listar_anotacoes(args: argparse.Namespace) -> int:
    publicacao = _carregar(args).obter(args.id)
    if not publicacao.anotacoes:
        print("Esta publicação ainda não possui anotações.")
        return 0
    for anotacao in publicacao.listar_anotacoes():
        print(f"[{anotacao.data.isoformat()}] {anotacao.texto}")
        if anotacao.trecho:
            print(f"  Trecho: {anotacao.trecho}")
    return 0


def _configuracoes(args: argparse.Namespace) -> int:
    configuracoes = Configuracoes.carregar()
    alterou = any(
        (
            args.genero_favorito is not None,
            args.limpar_genero,
            args.limite_leituras is not None,
            args.meta_anual is not None,
        )
    )
    if args.limpar_genero and args.genero_favorito is not None:
        raise ValidacaoError("Escolha entre definir ou limpar o gênero favorito")
    if args.genero_favorito is not None:
        configuracoes.genero_favorito = args.genero_favorito
    elif args.limpar_genero:
        configuracoes.genero_favorito = None
    if args.limite_leituras is not None:
        configuracoes.limite_leituras_simultaneas = args.limite_leituras
    if args.meta_anual is not None:
        configuracoes.meta_anual = args.meta_anual
    if alterou:
        configuracoes.salvar()
        print("Configurações salvas.")
    print(f"Gênero favorito: {configuracoes.genero_favorito or 'não definido'}")
    print(f"Limite de leituras simultâneas: {configuracoes.limite_leituras_simultaneas}")
    print(f"Meta anual de leituras: {configuracoes.meta_anual}")
    return 0


def _relatorio(args: argparse.Namespace) -> int:
    colecao = _carregar(args)
    meta = (
        args.meta
        if args.meta is not None
        else Configuracoes.carregar().meta_anual
    )
    relatorios = {
        "total": lambda: RelatorioTotal().gerar(colecao),
        "status": lambda: RelatorioPorStatus().gerar(colecao),
        "media": lambda: RelatorioMediaAvaliacoes().gerar(colecao),
        "top5": lambda: RelatorioTopAvaliadas().gerar(colecao),
        "anual": lambda: RelatorioProgressoAnual(meta, args.ano).gerar(colecao),
    }
    if args.tipo == "completo":
        resultado = {
            "total": relatorios["total"](),
            "status": relatorios["status"](),
            "avaliacoes": relatorios["media"](),
            "melhores_avaliadas": relatorios["top5"](),
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

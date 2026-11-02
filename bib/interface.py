"""Menu interativo para uso da biblioteca pelo terminal."""

import json
import os
import sys
from collections.abc import Callable
from contextlib import redirect_stdout
from io import StringIO

from bib.cli import main as executar_comando


def limpar_terminal() -> None:
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def _ler_obrigatorio(prompt: str) -> str:
    while True:
        valor = input(prompt).strip()
        if valor:
            return valor
        print("Este campo é obrigatório.")


def _ler_inteiro(prompt: str, *, minimo: int | None = None) -> int:
    while True:
        valor = input(prompt).strip()
        try:
            numero = int(valor)
        except ValueError:
            print("Informe um número inteiro válido.")
            continue
        if minimo is not None and numero < minimo:
            print(f"Informe um valor maior ou igual a {minimo}.")
            continue
        return numero


def _aguardar_retorno() -> None:
    input("\nPressione Enter para voltar ao menu inicial...")


def _cadastrar(opcoes: list[str]) -> None:
    limpar_terminal()
    print("\nTipo de publicação:")
    print("1. Livro")
    print("2. Revista")
    while True:
        tipo = input("Escolha: ").strip()
        if tipo in ("1", "2"):
            break
        print("Opção inválida. Escolha 1 ou 2.")

    argumentos = [
        "cadastrar",
        "livro" if tipo == "1" else "revista",
        "--titulo",
        _ler_obrigatorio("Título: "),
        "--autor",
        _ler_obrigatorio("Autor: "),
        "--ano",
        str(_ler_inteiro("Ano de publicação: ", minimo=1500)),
        "--paginas",
        str(_ler_inteiro("Número de páginas: ", minimo=1)),
    ]
    genero = input("Gênero [Sem gênero]: ").strip()
    if genero:
        argumentos.extend(["--genero", genero])

    campos_especificos = (
        (("Editora", "--editora"), ("ISBN", "--isbn"))
        if tipo == "1"
        else (("Edição", "--edicao"), ("ISSN", "--issn"))
    )
    for rotulo, opcao in campos_especificos:
        valor = input(f"{rotulo} (opcional): ").strip()
        if valor:
            argumentos.extend([opcao, valor])
    executar_comando([*argumentos, *opcoes])


def _listar_todos(opcoes: list[str]) -> None:
    limpar_terminal()
    executar_comando(["listar", *opcoes])
    _aguardar_retorno()


def _filtrar(opcoes: list[str]) -> None:
    limpar_terminal()
    print("\nInforme os filtros desejados (Enter para ignorar):")
    argumentos = ["listar"]
    for rotulo, opcao in (
        ("Título", "--titulo"),
        ("Autor", "--autor"),
        ("Gênero", "--genero"),
        ("Status (nao_lido, lendo, lido)", "--status"),
    ):
        valor = input(f"{rotulo}: ").strip()
        if valor:
            argumentos.extend([opcao, valor.lower()])
    executar_comando([*argumentos, *opcoes])
    _aguardar_retorno()


def _anotar(opcoes: list[str]) -> None:
    limpar_terminal()
    argumentos = [
        "anotar",
        _ler_obrigatorio("ID da publicação: "),
        "--texto",
        _ler_obrigatorio("Anotação: "),
    ]
    trecho = input("Trecho (opcional): ").strip()
    if trecho:
        argumentos.extend(["--trecho", trecho])
    pagina = input("Página (opcional): ").strip()
    if pagina:
        argumentos.extend(["--pagina", pagina])
    categoria = input("Categoria [anotacao/destaque]: ").strip().lower()
    if categoria:
        argumentos.extend(["--categoria", categoria])
    executar_comando([*argumentos, *opcoes])


def _formatar_percentual(valor: int | float) -> str:
    return f"{valor:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _imprimir_status(relatorio: dict[str, object]) -> None:
    print(f"Publicações no acervo: {relatorio['total']}")
    print("\nStatus de leitura:")
    for chave, rotulo in (
        ("lidos", "Lidas"),
        ("nao_lidos", "Não lidas"),
        ("lendo", "Em leitura"),
    ):
        dados = relatorio[chave]
        if isinstance(dados, dict):
            quantidade = dados["quantidade"]
            percentual = _formatar_percentual(dados["percentual"])
            print(f"  {rotulo}: {quantidade} ({percentual}%)")


def _imprimir_relatorio(
    tipo: str, relatorio: dict[str, object], ano: int | None = None
) -> None:
    if tipo == "completo":
        print("\n=== Relatório completo ===")
        status = relatorio["status"]
        avaliacoes = relatorio["avaliacoes"]
        if isinstance(status, dict):
            _imprimir_status(status)
        if isinstance(avaliacoes, dict):
            media = avaliacoes["media"]
            quantidade = avaliacoes["quantidade_avaliada"]
            print("\nAvaliações:")
            if media is None:
                print("  Ainda não há publicações avaliadas.")
            else:
                print(
                    f"  Nota média: {_formatar_percentual(media)}/10 "
                    f"({quantidade} publicações)"
                )
        return

    if tipo == "total":
        print("\n=== Total do acervo ===")
        print(f"Publicações cadastradas: {relatorio['total']}")
    elif tipo == "status":
        print("\n=== Publicações por status ===")
        _imprimir_status(relatorio)
    elif tipo == "media":
        print("\n=== Média das avaliações ===")
        media = relatorio["media"]
        quantidade = relatorio["quantidade_avaliada"]
        if media is None:
            print("Ainda não há publicações avaliadas.")
        else:
            print(
                f"Nota média: {_formatar_percentual(media)}/10 "
                f"({quantidade} publicações)"
            )
    else:
        print(f"\n=== Progresso de leitura em {ano} ===")
        print(f"Leituras concluídas: {relatorio['concluidas']}")
        meta = relatorio["meta"]
        print(f"Meta anual: {meta}")
        percentual = relatorio["percentual_atingido"]
        if percentual is not None:
            print(f"Meta alcançada: {_formatar_percentual(percentual)}%")
        print(f"Situação: {relatorio['aviso']}")


def _relatorio(opcoes: list[str]) -> None:
    limpar_terminal()
    print("\nRelatório:")
    print("1. Completo")
    print("2. Total")
    print("3. Por status")
    print("4. Média das avaliações")
    print("5. Progresso anual")
    tipos = {
        "1": "completo",
        "2": "total",
        "3": "status",
        "4": "media",
        "5": "anual",
    }
    while True:
        escolha = input("Escolha [1]: ").strip() or "1"
        if escolha in tipos:
            break
        print("Opção inválida. Escolha um número de 1 a 5.")

    tipo = tipos[escolha]
    argumentos = ["relatorio", "--tipo", tipo]
    ano_relatorio = None
    if escolha == "5":
        ano_relatorio = _ler_inteiro("Ano do relatório: ", minimo=1500)
        argumentos.extend(
            [
                "--meta",
                str(_ler_inteiro("Meta anual de leituras: ", minimo=0)),
                "--ano",
                str(ano_relatorio),
            ]
        )
    saida = StringIO()
    with redirect_stdout(saida):
        codigo_saida = executar_comando([*argumentos, *opcoes])
    if codigo_saida == 0:
        resultado = json.loads(saida.getvalue())
        _imprimir_relatorio(tipo, resultado, ano_relatorio)
    _aguardar_retorno()


def main() -> int:
    """Inicia a interface interativa da biblioteca."""
    acoes: dict[str, Callable[[list[str]], None]] = {
        "1": _cadastrar,
        "2": _listar_todos,
        "3": _filtrar,
        "4": _anotar,
        "5": _relatorio,
    }
    try:
        opcoes: list[str] = []
        while True:
            limpar_terminal()
            print("\n" + "=" * 42)
            print("        NewLibrary - Biblioteca Pessoal")
            print("=" * 42)
            print("1. Cadastrar publicação")
            print("2. Listar todas as publicações")
            print("3. Pesquisar publicações com filtros")
            print("4. Adicionar anotação em uma publicação")
            print("5. Gerar relatório de leituras")
            print("0. Sair")
            escolha = input("Selecione uma opção: ").strip()

            if escolha == "0":
                print("Até logo!")
                return 0
            acao = acoes.get(escolha)
            if acao is None:
                print("Opção inválida. Escolha um número de 0 a 5.")
                continue
            acao(opcoes)
    except (EOFError, KeyboardInterrupt):
        print("\nAté logo!")
        return 0
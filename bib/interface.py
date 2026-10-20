"""Menu interativo para uso da biblioteca pelo terminal."""

import os
import sys
from collections.abc import Callable

from bib.cli import main as executar_comando


def limpar_terminal() -> None:
    """Limpa a tela quando a interface está sendo usada em um terminal."""
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


def _opcoes_persistencia() -> list[str]:
    limpar_terminal()
    print("\nOnde deseja salvar o acervo?")
    print("1. JSON")
    print("2. SQLite")
    while True:
        formato = input("Escolha [1]: ").strip() or "1"
        if formato in ("1", "2"):
            break
        print("Opção inválida. Escolha 1 ou 2.")

    opcoes = ["--formato", "json" if formato == "1" else "sqlite"]
    caminho = input("Caminho do arquivo (Enter para usar o padrão): ").strip()
    if caminho:
        opcoes.extend(["--arquivo", caminho])
    return opcoes


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


def _listar(opcoes: list[str]) -> None:
    limpar_terminal()
    print("\nFiltros opcionais (Enter para ignorar):")
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

    argumentos = ["relatorio", "--tipo", tipos[escolha]]
    if escolha == "5":
        argumentos.extend(
            [
                "--meta",
                str(_ler_inteiro("Meta anual de leituras: ", minimo=0)),
                "--ano",
                str(_ler_inteiro("Ano do relatório: ", minimo=1500)),
            ]
        )
    executar_comando([*argumentos, *opcoes])


def main() -> int:
    """Inicia a interface interativa da biblioteca."""
    acoes: dict[str, Callable[[list[str]], None]] = {
        "1": _cadastrar,
        "2": _listar,
        "3": _anotar,
        "4": _relatorio,
    }
    try:
        opcoes = _opcoes_persistencia()
        while True:
            limpar_terminal()
            print("\n" + "=" * 42)
            print("        NewLibrary - Biblioteca Pessoal")
            print("=" * 42)
            print("1. Cadastrar publicação")
            print("2. Listar coleção de publicações")
            print("3. Adicionar anotação em uma publicação")
            print("4. Gerar relatório de leituras")
            print("0. Sair")
            escolha = input("Selecione uma opção: ").strip()

            if escolha == "0":
                print("Até logo!")
                return 0
            acao = acoes.get(escolha)
            if acao is None:
                print("Opção inválida. Escolha um número de 0 a 4.")
                continue
            acao(opcoes)
    except (EOFError, KeyboardInterrupt):
        print("\nAté logo!")
        return 0
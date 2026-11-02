"""Menu interativo para uso da biblioteca pelo terminal."""

import json
import os
import sys
from collections.abc import Callable
from contextlib import redirect_stdout
from datetime import date
from io import StringIO

from bib.cli import main as executar_comando
from bib.config import Configuracoes


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


def _ler_inteiro_opcional(
    prompt: str, *, padrao: int | None, minimo: int
) -> int | None:
    while True:
        valor = input(prompt).strip()
        if not valor:
            return padrao
        try:
            numero = int(valor)
        except ValueError:
            print("Informe um número inteiro válido.")
            continue
        if numero < minimo:
            print(f"Informe um valor maior ou igual a {minimo}.")
            continue
        return numero


def _ler_nota_opcional(prompt: str) -> float | None:
    while True:
        valor = input(prompt).strip()
        if not valor:
            return None
        try:
            nota = float(valor)
        except ValueError:
            print("Informe uma nota numérica entre 0 e 10.")
            continue
        if not 0 <= nota <= 10:
            print("A nota deve estar entre 0 e 10.")
            continue
        return nota


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
    genero_favorito = Configuracoes.carregar().genero_favorito
    genero_padrao = genero_favorito or "Sem gênero"
    genero = input(f"Gênero [{genero_padrao}]: ").strip()
    if genero:
        argumentos.extend(["--genero", genero])
    elif genero_favorito:
        argumentos.extend(["--genero", genero_favorito])

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
    inicio = input("Data inicial da leitura (AAAA-MM-DD, opcional): ").strip()
    fim = input("Data final da leitura (AAAA-MM-DD, opcional): ").strip()
    if inicio or fim:
        try:
            date.fromisoformat(inicio)
            date.fromisoformat(fim)
        except ValueError:
            print("Informe as duas datas no formato AAAA-MM-DD.")
            _aguardar_retorno()
            return
        argumentos.extend(["--inicio", inicio, "--fim", fim])
    executar_comando([*argumentos, *opcoes])
    _aguardar_retorno()


def _editar(opcoes: list[str]) -> None:
    limpar_terminal()
    argumentos = ["editar", _ler_obrigatorio("ID da publicação: ")]
    for rotulo, opcao in (("Título", "--titulo"), ("Autor", "--autor"), ("Gênero", "--genero")):
        valor = input(f"{rotulo} (Enter para manter): ").strip()
        if valor:
            argumentos.extend([opcao, valor])
    for rotulo, opcao, minimo in (
        ("Ano", "--ano", 1500),
        ("Número de páginas", "--paginas", 1),
    ):
        valor = _ler_inteiro_opcional(
            f"{rotulo} (Enter para manter): ", padrao=None, minimo=minimo
        )
        if valor is not None:
            argumentos.extend([opcao, str(valor)])
    nota = _ler_nota_opcional("Nova avaliação (0 a 10, Enter mantém): ")
    if nota is not None:
        argumentos.extend(["--nota", str(nota)])
    elif input("Deseja limpar a avaliação atual? (s/N): ").strip().casefold() == "s":
        argumentos.append("--limpar-nota")
    tipo = input("Tipo (livro ou revista, Enter mantém): ").strip().lower()
    if tipo:
        if tipo not in ("livro", "revista"):
            print("Tipo inválido; a publicação não foi alterada.")
            _aguardar_retorno()
            return
        argumentos.extend(["--tipo", tipo])
    campos_tipo = (
        (("Editora", "--editora"), ("ISBN", "--isbn"))
        if tipo == "livro"
        else (("Edição", "--edicao"), ("ISSN", "--issn"))
        if tipo == "revista"
        else ()
    )
    for rotulo, opcao in campos_tipo:
        valor = input(f"{rotulo} (opcional): ").strip()
        if valor:
            argumentos.extend([opcao, valor])
    executar_comando([*argumentos, *opcoes])
    _aguardar_retorno()


def _remover(opcoes: list[str]) -> None:
    limpar_terminal()
    identificador = _ler_obrigatorio("ID da publicação: ")
    if input("Confirma a remoção? (s/N): ").strip().casefold() == "s":
        executar_comando(["remover", identificador, *opcoes])
        _aguardar_retorno()
        return
    print("Remoção cancelada.")


def _alterar_status(opcoes: list[str]) -> None:
    limpar_terminal()
    identificador = _ler_obrigatorio("ID da publicação: ")
    print("\n1. Iniciar leitura")
    print("2. Concluir leitura")
    while True:
        escolha = input("Escolha: ").strip()
        if escolha in ("1", "2"):
            break
        print("Opção inválida. Escolha 1 ou 2.")
    acao = "iniciar" if escolha == "1" else "concluir"
    executar_comando(["status", identificador, acao, *opcoes])
    _aguardar_retorno()


def _avaliar(opcoes: list[str]) -> None:
    limpar_terminal()
    saida = StringIO()
    with redirect_stdout(saida):
        codigo_saida = executar_comando(
            ["listar", "--status", "lido", "--tipo", "livro", *opcoes]
        )
    publicacoes_concluidas = saida.getvalue()
    if codigo_saida != 0:
        print(publicacoes_concluidas, end="")
        _aguardar_retorno()
        return
    if publicacoes_concluidas.startswith("Nenhuma publicação"):
        print("Não há livros concluídos para avaliar.")
        _aguardar_retorno()
        return
    print("\nLivros concluídos disponíveis para avaliação:\n")
    print(publicacoes_concluidas, end="")
    identificador = _ler_obrigatorio("ID da publicação: ")
    nota = _ler_nota_opcional("Avaliação (0 a 10): ")
    while nota is None:
        print("A avaliação é obrigatória.")
        nota = _ler_nota_opcional("Avaliação (0 a 10): ")
    resenha = input("Resenha (opcional): ").strip()
    argumentos = ["avaliar", identificador, str(nota)]
    if resenha:
        argumentos.extend(["--resenha", resenha])
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


def _listar_anotacoes(opcoes: list[str]) -> None:
    limpar_terminal()
    identificador = _ler_obrigatorio("ID da publicação: ")
    executar_comando(["anotacoes", identificador, *opcoes])
    _aguardar_retorno()


def _configurar(opcoes: list[str]) -> None:
    limpar_terminal()
    configuracoes = Configuracoes.carregar()
    print("\nConfigurações atuais:")
    print(f"Gênero favorito: {configuracoes.genero_favorito or 'não definido'}")
    print(
        "Limite de leituras simultâneas: "
        f"{configuracoes.limite_leituras_simultaneas}"
    )
    print(f"Meta anual de leituras: {configuracoes.meta_anual}")
    argumentos = ["configuracoes"]
    genero = input("Novo gênero favorito (Enter mantém, - limpa): ").strip()
    if genero == "-":
        argumentos.append("--limpar-genero")
    elif genero:
        argumentos.extend(["--genero-favorito", genero])
    limite = _ler_inteiro_opcional(
        "Novo limite simultâneo (Enter mantém): ",
        padrao=configuracoes.limite_leituras_simultaneas,
        minimo=1,
    )
    if limite != configuracoes.limite_leituras_simultaneas:
        argumentos.extend(["--limite-leituras", str(limite)])
    meta = _ler_inteiro_opcional(
        "Nova meta anual (Enter mantém): ",
        padrao=configuracoes.meta_anual,
        minimo=0,
    )
    if meta != configuracoes.meta_anual:
        argumentos.extend(["--meta-anual", str(meta)])
    if len(argumentos) > 1:
        executar_comando(argumentos)
    _aguardar_retorno()


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
    livros = relatorio.get("livros")
    if isinstance(livros, dict):
        print(f"\nLivros no acervo: {livros['total']}")
        for chave, rotulo in (
            ("lidos", "Lidos"),
            ("nao_lidos", "Não lidos"),
            ("lendo", "Em leitura"),
        ):
            dados = livros[chave]
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
        ranking = relatorio["melhores_avaliadas"]
        if isinstance(ranking, dict):
            _imprimir_top5(ranking)
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
    elif tipo == "top5":
        _imprimir_top5(relatorio)
    else:
        print(f"\n=== Progresso de leitura em {ano} ===")
        print(f"Leituras concluídas: {relatorio['concluidas']}")
        meta = relatorio["meta"]
        print(f"Meta anual: {meta}")
        percentual = relatorio["percentual_atingido"]
        if percentual is not None:
            print(f"Meta alcançada: {_formatar_percentual(percentual)}%")
        print(f"Situação: {relatorio['aviso']}")


def _imprimir_top5(relatorio: dict[str, object]) -> None:
    print("\nTop 5 publicações mais bem avaliadas:")
    if not relatorio["suficiente"]:
        print(relatorio["mensagem"])
        return
    for posicao, publicacao in enumerate(relatorio["publicacoes"], start=1):
        if isinstance(publicacao, dict):
            print(
                f"  {posicao}. {publicacao['titulo']} — {publicacao['autor']} "
                f"({publicacao['nota']}/10)"
            )


def _relatorio(opcoes: list[str]) -> None:
    limpar_terminal()
    print("\nRelatório:")
    print("1. Completo")
    print("2. Total")
    print("3. Por status")
    print("4. Média das avaliações")
    print("5. Top 5 mais bem avaliadas")
    print("6. Progresso anual")
    tipos = {
        "1": "completo",
        "2": "total",
        "3": "status",
        "4": "media",
        "5": "top5",
        "6": "anual",
    }
    while True:
        escolha = input("Escolha [1]: ").strip() or "1"
        if escolha in tipos:
            break
        print("Opção inválida. Escolha um número de 1 a 6.")

    tipo = tipos[escolha]
    argumentos = ["relatorio", "--tipo", tipo]
    ano_relatorio = None
    if escolha == "6":
        ano_relatorio = _ler_inteiro("Ano do relatório: ", minimo=1500)
        meta_configurada = Configuracoes.carregar().meta_anual
        meta = _ler_inteiro_opcional(
            f"Meta anual de leituras [{meta_configurada}]: ",
            padrao=meta_configurada,
            minimo=0,
        )
        argumentos.extend(
            [
                "--meta",
                str(meta),
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
        "4": _editar,
        "5": _remover,
        "6": _alterar_status,
        "7": _avaliar,
        "8": _anotar,
        "9": _listar_anotacoes,
        "10": _relatorio,
        "11": _configurar,
    }
    try:
        opcoes: list[str] = []
        while True:
            limpar_terminal()
            print("\n" + "=" * 42)
            print("📚 NewLibrary - Biblioteca Pessoal")
            print("=" * 42)
            print("1. Cadastrar publicação")
            print("2. Listar todas as publicações")
            print("3. Pesquisar publicações com filtros")
            print("4. Editar publicação")
            print("5. Remover publicação")
            print("6. Iniciar ou concluir leitura")
            print("7. Avaliar publicação")
            print("8. Adicionar anotação")
            print("9. Listar anotações de uma publicação")
            print("10. Gerar relatórios")
            print("11. Configurações")
            print("0. Sair")
            escolha = input("Selecione uma opção: ").strip()

            if escolha == "0":
                print("Até logo!")
                return 0
            acao = acoes.get(escolha)
            if acao is None:
                print("Opção inválida. Escolha um número de 0 a 11.")
                continue
            acao(opcoes)
    except (EOFError, KeyboardInterrupt):
        print("\nAté logo!")
        return 0
from unittest.mock import Mock, patch

from bib.interface import limpar_terminal, main


def test_menu_interativo_sai_com_selecao_do_usuario(capsys):
    with patch("builtins.input", side_effect=["0"]):
        assert main() == 0

    saida = capsys.readouterr().out
    assert "NewLibrary - Biblioteca Pessoal" in saida
    assert "Até logo!" in saida
    assert "SQLite" not in saida


def test_menu_interativo_cadastra_publicacao(tmp_path, capsys):
    entradas = [
        "1",
        "1",
        "Dom Casmurro",
        "Machado de Assis",
        "1899",
        "256",
        "romance",
        "Garnier",
        "",
        "0",
    ]
    with (
        patch("bib.cli._DIRETORIO_PADRAO", tmp_path),
        patch("builtins.input", side_effect=entradas),
    ):
        assert main() == 0

    saida = capsys.readouterr().out
    assert "Publicação cadastrada com ID" in saida
    assert "Até logo!" in saida
    assert (tmp_path / "publicacoes.db").exists()


def test_menu_interativo_rejeita_opcao_invalida(capsys):
    with patch("builtins.input", side_effect=["9", "0"]):
        assert main() == 0

    assert "Opção inválida. Escolha um número de 0 a 5." in capsys.readouterr().out


def test_menu_interativo_retorna_ao_inicio_apos_listar_e_pesquisar(capsys):
    with (
        patch(
            "builtins.input",
            side_effect=["2", "", "3", "Dom", "", "", "", "", "0"],
        ) as ler_entrada,
        patch("bib.interface.executar_comando") as executar,
    ):
        assert main() == 0

    assert executar.call_args_list[0].args[0] == ["listar"]
    assert executar.call_args_list[1].args[0] == ["listar", "--titulo", "dom"]
    saida = capsys.readouterr().out
    assert saida.count("NewLibrary - Biblioteca Pessoal") == 3
    assert sum(
        chamada.args == ("\nPressione Enter para voltar ao menu inicial...",)
        for chamada in ler_entrada.call_args_list
    ) == 2


def test_menu_interativo_exibe_relatorio_antes_de_retornar(tmp_path, capsys):
    with (
        patch("bib.cli._DIRETORIO_PADRAO", tmp_path),
        patch("builtins.input", side_effect=["5", "2", "", "0"]) as ler_entrada,
    ):
        assert main() == 0

    saida = capsys.readouterr().out
    assert "Publicações cadastradas: 0" in saida
    assert (
        "\nPressione Enter para voltar ao menu inicial...",
    ) in [chamada.args for chamada in ler_entrada.call_args_list]
    assert saida.index("Publicações cadastradas: 0") < saida.index("Até logo!")


def test_menu_interativo_formata_todos_os_tipos_de_relatorio(tmp_path, capsys):
    entradas = [
        "5", "1", "",
        "5", "2", "",
        "5", "3", "",
        "5", "4", "",
        "5", "5", "2026", "12", "",
        "0",
    ]
    with (
        patch("bib.cli._DIRETORIO_PADRAO", tmp_path),
        patch("builtins.input", side_effect=entradas),
    ):
        assert main() == 0

    saida = capsys.readouterr().out
    assert "=== Relatório completo ===" in saida
    assert "=== Total do acervo ===" in saida
    assert "=== Publicações por status ===" in saida
    assert "=== Média das avaliações ===" in saida
    assert "=== Progresso de leitura em 2026 ===" in saida
    assert "Publicações cadastradas: 0" in saida
    assert "Ainda não há publicações avaliadas." in saida
    assert "Leituras concluídas: 0" in saida
    assert '"total":' not in saida


def test_limpar_terminal_executa_comando_em_terminal_interativo():
    saida_terminal = Mock()
    saida_terminal.isatty.return_value = True
    with (
        patch("bib.interface.sys.stdout", saida_terminal),
        patch("bib.interface.os.name", "posix"),
        patch("bib.interface.os.system") as executar,
    ):
        limpar_terminal()

    executar.assert_called_once_with("clear")


def test_limpar_terminal_nao_executa_comando_quando_saida_nao_e_terminal():
    saida_terminal = Mock()
    saida_terminal.isatty.return_value = False
    with (
        patch("bib.interface.sys.stdout", saida_terminal),
        patch("bib.interface.os.system") as executar,
    ):
        limpar_terminal()

    executar.assert_not_called()
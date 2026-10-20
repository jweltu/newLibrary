from unittest.mock import Mock, patch

from bib.interface import limpar_terminal, main


def test_menu_interativo_sai_com_selecao_do_usuario(capsys):
    with patch("builtins.input", side_effect=["1", "", "0"]):
        assert main() == 0

    saida = capsys.readouterr().out
    assert "BIBLIOTECA PESSOAL" in saida
    assert "Até logo!" in saida


def test_menu_interativo_cadastra_publicacao(tmp_path, capsys):
    entradas = [
        "2",
        str(tmp_path / "biblioteca.db"),
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
    with patch("builtins.input", side_effect=entradas):
        assert main() == 0

    saida = capsys.readouterr().out
    assert "Publicação cadastrada com ID" in saida
    assert "Até logo!" in saida
    assert (tmp_path / "biblioteca.db").exists()


def test_menu_interativo_rejeita_opcao_invalida(capsys):
    with patch("builtins.input", side_effect=["1", "", "9", "0"]):
        assert main() == 0

    assert "Opção inválida. Escolha um número de 0 a 4." in capsys.readouterr().out


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
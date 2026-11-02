from unittest.mock import Mock, patch

from bib.cli import main as executar_cli
from bib.config import Configuracoes
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
    with patch("builtins.input", side_effect=["12", "0"]):
        assert main() == 0

    assert "Opção inválida. Escolha um número de 0 a 11." in capsys.readouterr().out


def test_menu_interativo_retorna_ao_inicio_apos_listar_e_pesquisar(capsys):
    with (
        patch(
            "builtins.input",
            side_effect=["2", "", "3", "Dom", "", "", "", "", "", "", "0"],
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
        patch("builtins.input", side_effect=["10", "2", "", "0"]) as ler_entrada,
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
        "10", "1", "",
        "10", "2", "",
        "10", "3", "",
        "10", "4", "",
        "10", "5", "",
        "10", "6", "2026", "12", "",
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


def test_menu_interativo_altera_configuracoes(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with patch(
        "builtins.input",
        side_effect=["11", "Ficção", "2", "12", "", "0"],
    ):
        assert main() == 0

    configuracoes = Configuracoes.carregar()
    assert configuracoes.genero_favorito == "Ficção"
    assert configuracoes.limite_leituras_simultaneas == 2
    assert configuracoes.meta_anual == 12
    assert "Configurações salvas." in capsys.readouterr().out


def test_remocao_cancelada_retorna_ao_menu_sem_remover_publicacao(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr("bib.cli._DIRETORIO_PADRAO", tmp_path)
    assert executar_cli(
        [
            "cadastrar",
            "livro",
            "--titulo",
            "Livro para manter",
            "--autor",
            "Autora",
            "--ano",
            "2024",
            "--paginas",
            "100",
        ]
    ) == 0
    capsys.readouterr()

    with patch("builtins.input", side_effect=["5", "1", "n", "0"]):
        assert main() == 0

    saida = capsys.readouterr().out
    assert "Remoção cancelada." in saida
    assert "Pressione Enter para voltar ao menu inicial..." not in saida
    assert "Livro para manter" in executar_cli_output(tmp_path)


def test_remocao_confirmada_informa_sucesso(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("bib.cli._DIRETORIO_PADRAO", tmp_path)
    assert executar_cli(
        [
            "cadastrar",
            "livro",
            "--titulo",
            "Livro para excluir",
            "--autor",
            "Autora",
            "--ano",
            "2024",
            "--paginas",
            "100",
        ]
    ) == 0
    capsys.readouterr()

    with patch("builtins.input", side_effect=["5", "1", "s", "", "0"]):
        assert main() == 0

    saida = capsys.readouterr().out
    assert "Publicação removida: Livro para excluir" in saida
    assert "Nenhuma publicação encontrada." in executar_cli_output(tmp_path)


def test_avaliacao_sem_livros_concluidos_mostra_aviso(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("bib.cli._DIRETORIO_PADRAO", tmp_path)

    with patch("builtins.input", side_effect=["7", "", "0"]):
        assert main() == 0

    saida = capsys.readouterr().out
    assert "Não há livros concluídos para avaliar." in saida
    assert "ID da publicação:" not in saida


def test_avaliacao_lista_livros_concluidos_antes_de_solicitar_id(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr("bib.cli._DIRETORIO_PADRAO", tmp_path)
    assert executar_cli(
        [
            "cadastrar",
            "livro",
            "--titulo",
            "Livro concluído",
            "--autor",
            "Autora",
            "--ano",
            "2024",
            "--paginas",
            "100",
        ]
    ) == 0
    assert executar_cli(["status", "1", "iniciar"]) == 0
    assert executar_cli(["status", "1", "concluir"]) == 0
    capsys.readouterr()

    with patch(
        "builtins.input",
        side_effect=["7", "1", "9", "Excelente", "", "0"],
    ) as ler_entrada:
        assert main() == 0

    saida = capsys.readouterr().out
    assert "Livros concluídos disponíveis para avaliação:" in saida
    assert "[1] livro: Livro concluído" in saida
    chamadas = [chamada.args[0] for chamada in ler_entrada.call_args_list]
    assert chamadas.index("ID da publicação: ") > chamadas.index(
        "Selecione uma opção: "
    )
    assert "Avaliação registrada: 9.0/10" in saida


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


def executar_cli_output(caminho):
    from contextlib import redirect_stdout
    from io import StringIO

    saida = StringIO()
    with redirect_stdout(saida):
        executar_cli(["listar", "--arquivo", str(caminho / "publicacoes.db")])
    return saida.getvalue()
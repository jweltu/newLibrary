import json

from bib.cli import main
from bib.repository.sqlite_repo import RepositorioSQLite


def test_cli_cadastra_lista_anota_e_gera_relatorio(tmp_path, capsys):
    arquivo = tmp_path / "acervo" / "publicacoes.db"
    opcoes_arquivo = ["--arquivo", str(arquivo)]

    assert main(
        [
            "cadastrar",
            "livro",
            "--titulo",
            "Dom Casmurro",
            "--autor",
            "Machado de Assis",
            "--ano",
            "1899",
            "--paginas",
            "256",
            *opcoes_arquivo,
        ]
    ) == 0
    saida_cadastro = capsys.readouterr().out
    id_publicacao = saida_cadastro.split("ID ", 1)[1].split(":", 1)[0]
    assert id_publicacao == "1"

    assert main(["listar", *opcoes_arquivo]) == 0
    assert "Dom Casmurro" in capsys.readouterr().out

    assert main(
        [
            "anotar",
            id_publicacao,
            "--texto",
            "Revisar passagem",
            "--pagina",
            "12",
            *opcoes_arquivo,
        ]
    ) == 0
    assert "Anotação registrada" in capsys.readouterr().out

    assert main(["relatorio", *opcoes_arquivo]) == 0
    resultado = json.loads(capsys.readouterr().out)
    assert resultado["total"] == {"total": 1}
    assert resultado["status"]["total"] == 1
    anotacao = (
        RepositorioSQLite(arquivo)
        .carregar()
        .publicacoes[id_publicacao]
        .anotacoes[0]
    )
    assert anotacao.texto == "Revisar passagem"


def test_cli_relatorio_anual_e_filtragem_de_lista(tmp_path, capsys):
    arquivo = tmp_path / "publicacoes.db"
    opcoes_arquivo = ["--arquivo", str(arquivo)]
    main(
        [
            "cadastrar",
            "revista",
            "--titulo",
            "Revista de História",
            "--autor",
            "Equipe Editorial",
            "--ano",
            "2024",
            "--paginas",
            "80",
            *opcoes_arquivo,
        ]
    )
    capsys.readouterr()

    assert main(["listar", "--titulo", "não encontrado", *opcoes_arquivo]) == 0
    assert "Nenhuma publicação" in capsys.readouterr().out

    assert main(
        [
            "relatorio",
            "--tipo",
            "anual",
            "--meta",
            "12",
            "--ano",
            "2026",
            *opcoes_arquivo,
        ]
    ) == 0
    resultado = json.loads(capsys.readouterr().out)
    assert resultado["meta"] == 12
    assert resultado["concluidas"] == 0


def test_cli_informa_publicacao_inexistente(tmp_path, capsys):
    codigo = main(
        [
            "anotar",
            "ausente",
            "--texto",
            "Minha anotação",
            "--arquivo",
            str(tmp_path / "acervo.db"),
        ]
    )

    assert codigo == 1
    assert "não encontrada" in capsys.readouterr().err


def test_cli_persiste_em_sqlite(tmp_path, capsys):
    arquivo = tmp_path / "acervo.db"
    opcoes_sqlite = ["--arquivo", str(arquivo)]

    assert main(
        [
            "cadastrar",
            "livro",
            "--titulo",
            "Dom Casmurro",
            "--autor",
            "Machado de Assis",
            "--ano",
            "1899",
            "--paginas",
            "256",
            *opcoes_sqlite,
        ]
    ) == 0
    capsys.readouterr()

    assert arquivo.exists()
    assert main(["listar", *opcoes_sqlite]) == 0
    assert "[1] livro: Dom Casmurro" in capsys.readouterr().out


def test_cli_gera_ids_numericos_sequenciais(tmp_path, capsys):
    arquivo = tmp_path / "acervo.db"
    opcoes_arquivo = ["--arquivo", str(arquivo)]

    for titulo in ("Primeiro", "Segundo"):
        assert main(
            [
                "cadastrar",
                "livro",
                "--titulo",
                titulo,
                "--autor",
                f"Autor {titulo}",
                "--ano",
                "2020",
                "--paginas",
                "100",
                *opcoes_arquivo,
            ]
        ) == 0

    saidas = capsys.readouterr().out
    assert "ID 1: Primeiro" in saidas
    assert "ID 2: Segundo" in saidas

import json
from datetime import date

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


def test_cli_crud_transicoes_anotacoes_e_avaliacao(tmp_path, capsys):
    arquivo = tmp_path / "acervo.db"
    opcoes = ["--arquivo", str(arquivo)]
    assert main(
        [
            "cadastrar",
            "livro",
            "--titulo",
            "Livro inicial",
            "--autor",
            "Autora",
            "--ano",
            "2024",
            "--paginas",
            "100",
            *opcoes,
        ]
    ) == 0
    capsys.readouterr()

    assert main(
        [
            "editar",
            "1",
            "--titulo",
            "Livro atualizado",
            "--tipo",
            "revista",
            "--edicao",
            "42",
            *opcoes,
        ]
    ) == 0
    assert main(["status", "1", "iniciar", *opcoes]) == 0
    dados = RepositorioSQLite(arquivo).carregar().obter("1").to_dict()
    assert dados["status"] == "LENDO"
    assert dados["data_inicio"] is not None
    assert main(["status", "1", "concluir", *opcoes]) == 0
    assert main(["avaliar", "1", "9", "--resenha", "Muito bom", *opcoes]) == 0
    assert main(
        ["anotar", "1", "--texto", "Nota", "--trecho", "Trecho", *opcoes]
    ) == 0
    assert main(["anotacoes", "1", *opcoes]) == 0
    assert "Trecho: Trecho" in capsys.readouterr().out
    final = RepositorioSQLite(arquivo).carregar().obter("1")
    assert final.tipo() == "revista"
    assert final.status.name == "LIDO"
    assert final.nota == 9
    assert final.resenha == "Muito bom"

    assert main(["remover", "1", *opcoes]) == 0
    assert RepositorioSQLite(arquivo).carregar().publicacoes == {}


def test_cli_impede_concluir_sem_iniciar(tmp_path, capsys):
    arquivo = tmp_path / "acervo.db"
    opcoes = ["--arquivo", str(arquivo)]
    assert main(
        [
            "cadastrar",
            "revista",
            "--titulo",
            "Revista",
            "--autor",
            "Equipe",
            "--ano",
            "2024",
            "--paginas",
            "20",
            *opcoes,
        ]
    ) == 0
    capsys.readouterr()

    assert main(["status", "1", "concluir", *opcoes]) == 1
    assert "Não é possível concluir" in capsys.readouterr().err


def test_cli_configuracoes_persistem_settings_json(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    assert main(
        [
            "configuracoes",
            "--genero-favorito",
            "Fantasia",
            "--limite-leituras",
            "2",
            "--meta-anual",
            "15",
        ]
    ) == 0

    configuracoes = json.loads((tmp_path / "settings.json").read_text())
    assert configuracoes == {
        "genero_favorito": "Fantasia",
        "limite_leituras_simultaneas": 2,
        "meta_anual": 15,
    }


def test_cli_aplica_limite_de_leituras_simultaneas(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    arquivo = tmp_path / "acervo.db"
    opcoes = ["--arquivo", str(arquivo)]
    assert main(["configuracoes", "--limite-leituras", "1"]) == 0
    for titulo in ("Primeira", "Segunda"):
        assert main(
            [
                "cadastrar",
                "livro",
                "--titulo",
                titulo,
                "--autor",
                f"Autor {titulo}",
                "--ano",
                "2024",
                "--paginas",
                "100",
                *opcoes,
            ]
        ) == 0
    capsys.readouterr()

    assert main(["status", "1", "iniciar", *opcoes]) == 0
    assert main(["status", "2", "iniciar", *opcoes]) == 1
    assert "limite de leituras simultâneas" in capsys.readouterr().err


def test_cli_filtra_publicacoes_por_periodo_de_leitura(tmp_path, capsys):
    arquivo = tmp_path / "acervo.db"
    opcoes = ["--arquivo", str(arquivo)]
    assert main(
        [
            "cadastrar",
            "livro",
            "--titulo",
            "Livro lido",
            "--autor",
            "Autora",
            "--ano",
            "2024",
            "--paginas",
            "100",
            *opcoes,
        ]
    ) == 0
    capsys.readouterr()
    assert main(["status", "1", "iniciar", *opcoes]) == 0
    capsys.readouterr()
    hoje = date.today().isoformat()

    assert main(
        ["listar", "--inicio", hoje, "--fim", hoje, *opcoes]
    ) == 0
    assert "Livro lido" in capsys.readouterr().out


def test_cli_top5_informa_falta_de_dados(tmp_path, capsys):
    assert main(["relatorio", "--tipo", "top5", "--arquivo", str(tmp_path / "a.db")]) == 0

    relatorio = json.loads(capsys.readouterr().out)
    assert relatorio["suficiente"] is False
    assert "informações suficientes" in relatorio["mensagem"]

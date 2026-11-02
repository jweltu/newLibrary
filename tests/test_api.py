from datetime import date

from fastapi.testclient import TestClient

from bib.api import create_app
from bib.config import Configuracoes


def test_api_cadastra_lista_consulta_anota_e_relata(tmp_path):
    client = TestClient(create_app(tmp_path / "acervo" / "publicacoes.db"))

    resposta = client.post(
        "/publicacoes",
        json={
            "tipo": "livro",
            "titulo": "Dom Casmurro",
            "autor": "Machado de Assis",
            "ano": 1899,
            "paginas": 256,
            "genero": "romance",
            "editora": "Garnier",
        },
    )
    assert resposta.status_code == 201
    publicacao = resposta.json()
    assert publicacao["tipo"] == "livro"
    publicacao_id = publicacao["id"]
    assert publicacao_id == "1"

    assert client.get("/publicacoes", params={"titulo": "casmurro"}).json() == [
        publicacao
    ]
    assert client.get(f"/publicacoes/{publicacao_id}").json() == publicacao

    anotacao = client.post(
        f"/publicacoes/{publicacao_id}/anotacoes",
        json={"texto": "Revisar passagem", "pagina": 12, "categoria": "destaque"},
    )
    assert anotacao.status_code == 201
    assert anotacao.json()["categoria"] == "destaque"
    assert anotacao.json()["pagina"] == 12

    relatorio = client.get("/relatorios/completo")
    assert relatorio.status_code == 200
    assert relatorio.json()["total"] == {"total": 1}
    assert relatorio.json()["status"]["total"] == 1
    assert client.get(f"/publicacoes/{publicacao_id}").json()["anotacoes"] == [
        anotacao.json()
    ]


def test_api_valida_entradas_e_reporta_erros_de_dominio(tmp_path):
    client = TestClient(create_app(tmp_path / "acervo.db"))
    dados_publicacao = {
        "tipo": "revista",
        "titulo": "Revista de História",
        "autor": "Equipe Editorial",
        "ano": 2024,
        "paginas": 80,
    }
    assert (
        client.post("/publicacoes", json={**dados_publicacao, "ano": 1400}).status_code
        == 422
    )

    assert client.post("/publicacoes", json=dados_publicacao).status_code == 201
    duplicada = client.post("/publicacoes", json=dados_publicacao)
    assert duplicada.status_code == 409
    assert "já está na coleção" in duplicada.json()["detail"]

    inexistente = client.get("/publicacoes/id-inexistente")
    assert inexistente.status_code == 404
    assert "não encontrada" in inexistente.json()["detail"]


def test_api_relatorio_anual(tmp_path):
    client = TestClient(create_app(tmp_path / "acervo.db"))

    resposta = client.get("/relatorios/anual", params={"meta": 12, "ano": 2026})

    assert resposta.status_code == 200
    assert resposta.json()["meta"] == 12
    assert resposta.json()["concluidas"] == 0


def test_api_persiste_em_sqlite(tmp_path):
    caminho_db = tmp_path / "dados" / "biblioteca.db"
    client = TestClient(create_app(caminho_db))
    cadastro = client.post(
        "/publicacoes",
        json={
            "tipo": "revista",
            "titulo": "Revista de História",
            "autor": "Equipe Editorial",
            "ano": 2024,
            "paginas": 80,
            "edicao": "42",
        },
    )

    assert cadastro.status_code == 201
    assert caminho_db.exists()
    resposta = client.get("/publicacoes")
    assert resposta.status_code == 200
    assert resposta.json()[0]["id"] == cadastro.json()["id"]


def test_api_realiza_crud_transicoes_anotacoes_e_filtro_de_leitura(tmp_path):
    client = TestClient(create_app(tmp_path / "acervo.db"))
    resposta = client.post(
        "/publicacoes",
        json={
            "tipo": "livro",
            "titulo": "Livro inicial",
            "autor": "Autora",
            "ano": 2024,
            "paginas": 100,
        },
    )
    publicacao_id = resposta.json()["id"]
    assert resposta.json()["status"] == "NÃO LIDO"

    alterada = client.patch(
        f"/publicacoes/{publicacao_id}",
        json={"titulo": "Livro atualizado", "genero": "Ficção"},
    )
    assert alterada.status_code == 200
    assert alterada.json()["titulo"] == "Livro atualizado"
    alterada_tipo = client.patch(
        f"/publicacoes/{publicacao_id}",
        json={"tipo": "revista", "edicao": "42"},
    )
    assert alterada_tipo.json()["tipo"] == "revista"
    assert alterada_tipo.json()["edicao"] == "42"

    sem_inicio = client.patch(
        f"/publicacoes/{publicacao_id}/status", json={"acao": "concluir"}
    )
    assert sem_inicio.status_code == 422

    iniciada = client.patch(
        f"/publicacoes/{publicacao_id}/status", json={"acao": "iniciar"}
    )
    assert iniciada.json()["status"] == "LENDO"
    assert iniciada.json()["data_inicio"] is not None
    assert client.patch(
        f"/publicacoes/{publicacao_id}/progresso", params={"pagina": 25}
    ).json()["pagina_atual"] == 25
    concluida = client.patch(
        f"/publicacoes/{publicacao_id}/status", json={"acao": "concluir"}
    )
    assert concluida.json()["status"] == "LIDO"
    assert concluida.json()["data_termino"] is not None

    avaliada = client.post(
        f"/publicacoes/{publicacao_id}/avaliacao",
        params={"nota": 9, "resenha": "Muito bom"},
    )
    assert avaliada.json()["nota"] == 9
    periodo = client.get(
        "/publicacoes",
        params={"inicio": date.today().isoformat(), "fim": date.today().isoformat()},
    )
    assert len(periodo.json()) == 1

    anotacao = client.post(
        f"/publicacoes/{publicacao_id}/anotacoes",
        json={"texto": "Nota de leitura", "trecho": "Trecho destacado"},
    )
    assert anotacao.status_code == 201
    assert client.get(
        f"/publicacoes/{publicacao_id}/anotacoes"
    ).json() == [anotacao.json()]

    assert client.delete(f"/publicacoes/{publicacao_id}").status_code == 204
    assert client.get(f"/publicacoes/{publicacao_id}").status_code == 404


def test_api_relatorio_top5_informa_dados_insuficientes(tmp_path):
    client = TestClient(create_app(tmp_path / "acervo.db"))

    resposta = client.get("/relatorios/top5")

    assert resposta.status_code == 200
    assert resposta.json()["suficiente"] is False
    assert resposta.json()["publicacoes"] == []


def test_api_configuracoes_persistem_em_settings_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = TestClient(create_app(tmp_path / "acervo.db"))

    atualizada = client.put(
        "/configuracoes",
        json={
            "genero_favorito": "Ficção",
            "limite_leituras_simultaneas": 2,
            "meta_anual": 12,
        },
    )

    assert atualizada.status_code == 200
    assert atualizada.json() == {
        "genero_favorito": "Ficção",
        "limite_leituras_simultaneas": 2,
        "meta_anual": 12,
    }
    assert Configuracoes.carregar().meta_anual == 12


def test_api_respeita_limite_de_leituras_simultaneas(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    Configuracoes(limite_leituras_simultaneas=1).salvar()
    client = TestClient(create_app(tmp_path / "acervo.db"))
    ids = []
    for titulo in ("Primeira", "Segunda"):
        resposta = client.post(
            "/publicacoes",
            json={
                "tipo": "livro",
                "titulo": titulo,
                "autor": f"Autor {titulo}",
                "ano": 2024,
                "paginas": 100,
            },
        )
        ids.append(resposta.json()["id"])

    assert client.patch(
        f"/publicacoes/{ids[0]}/status", json={"acao": "iniciar"}
    ).status_code == 200
    limite = client.patch(
        f"/publicacoes/{ids[1]}/status", json={"acao": "iniciar"}
    )
    assert limite.status_code == 422
    assert "limite de leituras simultâneas" in limite.json()["detail"]

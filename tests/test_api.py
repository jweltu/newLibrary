from fastapi.testclient import TestClient

from bib.api import create_app


def test_api_cadastra_lista_consulta_anota_e_relata(tmp_path):
    client = TestClient(create_app(tmp_path / "acervo" / "publicacoes.json"))

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
    client = TestClient(create_app(tmp_path / "acervo.json"))
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
    client = TestClient(create_app(tmp_path / "acervo.json"))

    resposta = client.get("/relatorios/anual", params={"meta": 12, "ano": 2026})

    assert resposta.status_code == 200
    assert resposta.json()["meta"] == 12
    assert resposta.json()["concluidas"] == 0


def test_api_persiste_em_sqlite(tmp_path):
    caminho_db = tmp_path / "dados" / "biblioteca.db"
    client = TestClient(create_app(caminho_db, formato="sqlite"))
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

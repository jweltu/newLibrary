import json
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4

from bib.models.colecao import Colecao
from bib.models.livro import Livro
from bib.models.revista import Revista
from bib.repository.base import RepositorioPublicacoes


class RepositorioSQLite(RepositorioPublicacoes):
    def __init__(self, caminho_db):
        self._caminho_db = Path(caminho_db)

    def _conectar(self):
        self._caminho_db.parent.mkdir(parents=True, exist_ok=True)
        conexao = sqlite3.connect(self._caminho_db)
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS publicacoes (
                id TEXT PRIMARY KEY,
                tipo TEXT NOT NULL CHECK (tipo IN ('livro', 'revista')),
                dados TEXT NOT NULL
            )
            """
        )
        conexao.commit()
        return conexao

    def salvar(self, colecao: Colecao):
        registros = [
            (
                str(publicacao.id),
                publicacao.tipo(),
                json.dumps(publicacao.to_dict(), ensure_ascii=False),
            )
            for publicacao in colecao.publicacoes.values()
        ]
        with closing(self._conectar()) as conexao:
            with conexao:
                conexao.execute("DELETE FROM publicacoes")
                conexao.executemany(
                    "INSERT INTO publicacoes (id, tipo, dados) VALUES (?, ?, ?)",
                    registros,
                )

    def carregar(self):
        if not self._caminho_db.exists():
            return Colecao()

        tipos = {"livro": Livro, "revista": Revista}
        publicacoes = {}
        with closing(self._conectar()) as conexao:
            self._migrar_ids_numericos(conexao)
            registros = conexao.execute(
                "SELECT id, tipo, dados FROM publicacoes ORDER BY rowid"
            ).fetchall()

        for id_publicacao, tipo, dados in registros:
            classe = tipos.get(tipo)
            if classe is None:
                raise ValueError(f"Tipo de publicação inválido no SQLite: {tipo!r}")
            registro = json.loads(dados)
            if not isinstance(registro, dict):
                raise ValueError(
                    f"Os dados da publicação {id_publicacao!r} devem ser um objeto"
                )
            publicacao = classe.from_dict(registro)
            if publicacao.id != id_publicacao:
                raise ValueError(
                    f"ID da publicação inconsistente no SQLite: {id_publicacao!r}"
                )
            publicacoes[publicacao.id] = publicacao
        return Colecao(publicacoes)

    @staticmethod
    def _migrar_ids_numericos(conexao: sqlite3.Connection) -> None:
        with conexao:
            registros = conexao.execute(
                "SELECT rowid, id, dados FROM publicacoes ORDER BY rowid"
            ).fetchall()
            if not any(not str(id_publicacao).isdecimal() for _, id_publicacao, _ in registros):
                return

            registros_com_novos_ids = []
            for novo_id, (rowid, id_publicacao, dados) in enumerate(registros, start=1):
                registro = json.loads(dados)
                if not isinstance(registro, dict):
                    raise ValueError(
                        f"Os dados da publicação {id_publicacao!r} devem ser um objeto"
                    )
                if registro.get("id") != id_publicacao:
                    raise ValueError(
                        f"ID da publicação inconsistente no SQLite: {id_publicacao!r}"
                    )

                novo_id_texto = str(novo_id)
                for anotacao in registro.get("anotacoes", []):
                    if anotacao.get("publicacao_id") == id_publicacao:
                        anotacao["publicacao_id"] = novo_id_texto
                registro["id"] = novo_id_texto
                registros_com_novos_ids.append(
                    (rowid, id_publicacao, novo_id_texto, json.dumps(registro, ensure_ascii=False))
                )

            ids_temporarios = {
                rowid: f"__migrando_{uuid4()}__" for rowid, _, _, _ in registros_com_novos_ids
            }
            for rowid, id_temporario in ids_temporarios.items():
                conexao.execute(
                    "UPDATE publicacoes SET id = ? WHERE rowid = ?",
                    (id_temporario, rowid),
                )
            for rowid, _, novo_id, dados in registros_com_novos_ids:
                conexao.execute(
                    "UPDATE publicacoes SET id = ?, dados = ? WHERE rowid = ?",
                    (novo_id, dados, rowid),
                )
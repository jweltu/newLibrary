from pathlib import Path

from bib.repository.json_repo import RepositorioJSON
from bib.repository.sqlite_repo import RepositorioSQLite


def criar_repositorio(formato: str, caminho: str | Path):
    """Cria o repositório de persistência selecionado."""
    if formato == "json":
        return RepositorioJSON(caminho)
    if formato == "sqlite":
        return RepositorioSQLite(caminho)
    raise ValueError(f"Formato de persistência inválido: {formato!r}")


__all__ = ["RepositorioJSON", "RepositorioSQLite", "criar_repositorio"]
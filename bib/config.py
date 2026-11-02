import json
from pathlib import Path

from bib.excecoes import ValidacaoError


class Configuracoes:
    def __init__(
        self,
        genero_favorito: str | None = None,
        limite_leituras_simultaneas: int = 3,
        meta_anual: int = 0,
    ):
        self.limite_leituras_simultaneas = limite_leituras_simultaneas
        self.genero_favorito = genero_favorito
        self.meta_anual = meta_anual

    @property
    def limite_leituras_simultaneas(self) -> int:
        return self._limite_leituras_simultaneas

    @limite_leituras_simultaneas.setter
    def limite_leituras_simultaneas(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:
            raise ValidacaoError(
                "O limite de leituras simultâneas deve ser um inteiro positivo"
            )
        self._limite_leituras_simultaneas = valor

    @property
    def genero_favorito(self) -> str | None:
        return self._genero_favorito

    @genero_favorito.setter
    def genero_favorito(self, valor: str | None) -> None:
        if valor is not None and (not isinstance(valor, str) or not valor.strip()):
            raise ValidacaoError(
                "O gênero favorito deve ser um texto não vazio ou None"
            )
        self._genero_favorito = valor.strip() if isinstance(valor, str) else None

    @property
    def meta_anual(self) -> int:
        return self._meta_anual

    @meta_anual.setter
    def meta_anual(self, valor: int) -> None:
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
            raise ValidacaoError("A meta anual deve ser um inteiro não negativo")
        self._meta_anual = valor

    @classmethod
    def carregar(cls, caminho: str | Path = "settings.json") -> "Configuracoes":
        arquivo = Path(caminho)
        if not arquivo.exists() or arquivo.stat().st_size == 0:
            return cls()
        try:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
        except json.JSONDecodeError as erro:
            raise ValueError(f"Arquivo de configurações inválido: {arquivo}") from erro
        if not isinstance(dados, dict):
            raise ValueError("O arquivo de configurações deve conter um objeto JSON")
        return cls(
            genero_favorito=dados.get("genero_favorito"),
            limite_leituras_simultaneas=dados.get(
                "limite_leituras_simultaneas", 3
            ),
            meta_anual=dados.get("meta_anual", 0),
        )

    def salvar(self, caminho: str | Path = "settings.json") -> None:
        arquivo = Path(caminho)
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        dados = {
            "genero_favorito": self.genero_favorito,
            "limite_leituras_simultaneas": self.limite_leituras_simultaneas,
            "meta_anual": self.meta_anual,
        }
        arquivo.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
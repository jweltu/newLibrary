from bib.models.colecao import Colecao
from bib.relatorio.base import EstrategiaRelatorio


class GeradorRelatorios:
    def __init__(self, estrategia: EstrategiaRelatorio) -> None:
        self.definir_estrategia(estrategia)

    def definir_estrategia(self, estrategia: EstrategiaRelatorio) -> None:
        if not isinstance(estrategia, EstrategiaRelatorio):
            raise TypeError("A estratégia deve implementar EstrategiaRelatorio")
        self._estrategia = estrategia

    def executar(self, colecao: Colecao) -> dict[str, object]:
        return self._estrategia.gerar(colecao)

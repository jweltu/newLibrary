from abc import ABC, abstractmethod

from bib.models.colecao import Colecao


class EstrategiaRelatorio(ABC):
    @abstractmethod
    def gerar(self, colecao: Colecao) -> dict[str, object]:
        raise NotImplementedError

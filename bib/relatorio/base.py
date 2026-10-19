from abc import ABC, abstractmethod
from typing import Any

from bib.models.colecao import Colecao


class EstrategiaRelatorio(ABC):
    @abstractmethod
    def gerar(self, colecao: Colecao) -> dict[str, Any]:
        raise NotImplementedError

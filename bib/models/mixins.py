# bib/modelos/mixins.py
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Self


class SerializavelMixin:
    """Converte o objeto em dict compatível com JSON e o reconstrói.

    Não importa nenhuma classe de domínio: só conhece tipos primitivos,
    Enum, date e outros objetos serializáveis.
    """

    # Atributos que não devem ir para o dict
    _campos_ignorados: frozenset[str] = frozenset()

    def to_dict(self) -> dict[str, Any]:
        return {
            chave.lstrip("_"): self._serializar(valor)
            for chave, valor in vars(self).items()
            if chave not in self._campos_ignorados
        }

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> Self:
        """Contrato: cada classe concreta define como se reconstrói."""
        raise NotImplementedError(f"{cls.__name__} não implementa from_dict")

    @classmethod
    def _serializar(cls, valor: Any) -> Any:
        if isinstance(valor, SerializavelMixin):
            return valor.to_dict()
        if isinstance(valor, Enum):
            return valor.value
        if isinstance(valor, date):
            return valor.isoformat()
        if isinstance(valor, (list, tuple)):
            return [cls._serializar(v) for v in valor]
        if isinstance(valor, dict):
            return {k: cls._serializar(v) for k, v in valor.items()}
        return valor

    @staticmethod
    def _parse_data(valor: str | None) -> date | None:
        return date.fromisoformat(valor) if valor else None

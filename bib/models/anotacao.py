from datetime import date

from .enums import CategoriaAnotacao
from ..excecoes import ValidacaoError


class Anotacao:
    def __init__(self, texto, id, publicacao_id, categoria, data, trecho=None, pagina=None):
        self.texto = texto
        self._id = id
        self._publicacao_id = publicacao_id
        self.categoria = categoria
        self.data = data
        self.trecho = trecho
        self.pagina = pagina

    @property
    def texto(self):
        return self._texto

    @texto.setter
    def texto(self, valor):
        if not isinstance(valor, str) or not valor.strip():
            raise ValidacaoError("O texto da anotação não pode ser vazio")
        self._texto = valor.strip()

    @property
    def id(self):
        return self._id

    @property
    def publicacao_id(self):
        return self._publicacao_id

    @property
    def categoria(self):
        return self._categoria

    @categoria.setter
    def categoria(self, valor):
        if not isinstance(valor, CategoriaAnotacao):
            try:
                valor = CategoriaAnotacao(valor)
            except (TypeError, ValueError):
                raise ValidacaoError("Categoria de anotação inválida") from None
        self._categoria = valor

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, valor):
        if isinstance(valor, str):
            valor = date.fromisoformat(valor)
        if not isinstance(valor, date):
            raise ValidacaoError("A data da anotação deve ser uma data válida")
        self._data = valor

    @property
    def trecho(self):
        return self._trecho

    @trecho.setter
    def trecho(self, valor):
        self._trecho = valor

    @property
    def pagina(self):
        return self._pagina

    @pagina.setter
    def pagina(self, valor):
        if valor is not None and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 1
        ):
            raise ValidacaoError("A página da anotação deve ser um inteiro positivo")
        self._pagina = valor

    def __repr__(self):
        return f"Anotacao(texto={self.texto}, id={self.id}, publicacao_id={self.publicacao_id}, categoria={self.categoria}, data={self.data}, trecho={self.trecho}, pagina={self.pagina})"

    def __str__(self):
        return self.texto

    def to_dict(self):
        return {
            "texto": self.texto,
            "id": self.id,
            "publicacao_id": self.publicacao_id,
            "categoria": self.categoria.value,
            "data": self.data.isoformat(),
            "trecho": self.trecho,
            "pagina": self.pagina
        }

    @classmethod
    def from_dict(cls, dados):
        return cls(
            texto=dados.get("texto"),
            id=dados.get("id"),
            publicacao_id=dados.get("publicacao_id"),
            categoria=dados.get("categoria"),
            data=dados.get("data"),
            trecho=dados.get("trecho"),
            pagina=dados.get("pagina")
        )
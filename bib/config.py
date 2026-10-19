from bib.excecoes import ValidacaoError


class Configuracoes:
    def __init__(self):
        self.limite_leituras_simultaneas = 3
        self.genero_favorito = None
        self.meta_anual = 0

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
from base import EstrategiaRelatorio

class RelatorioTotal(EstrategiaRelatorio):
    def gerar(colecao):
        pass

class RelatorioPorStatus(EstrategiaRelatorio):
    def gerar(colecao):
        pass

class RelatorioMediaAvaliacoes(EstrategiaRelatorio):
    def gerar(colecao):
        pass

class RelatorioProgressoAnual(EstrategiaRelatorio):
    def __init__(self, meta, ano):
        self._meta = meta
        self._ano = ano

    def gerar(colecao):
        pass
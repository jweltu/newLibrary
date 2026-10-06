from enums import *
from excecoes import TransicaoStatusError

class EstadoLeitura:

    def status():
        pass

    def iniciar(pub, data=None):
        pass

    def concluir(pub, data=None):
        pass

    def pode_avaliar():
        pass

class EstadoNaoLido(EstadoLeitura):

    def status():
        return EstadoLeitura.NAO_LIDO

    def iniciar(pub, data=None):
        pass

    def concluir(pub, data=None):
        pass

    def pode_avaliar():
        return False

class EstadoLendo(EstadoLeitura):

    def status():
        return EstadoLeitura.LENDO

    def iniciar(pub, data=None):
        pass

    def concluir(pub, data=None):
        pass

    def pode_avaliar():
        return False

class EstadoLido(EstadoLeitura):

    def status():
        return EstadoLeitura.LIDO

    def iniciar(pub, data=None):
        pass

    def concluir(pub, data=None):
        raise TransicaoStatusError()

    def pode_avaliar():
        return True
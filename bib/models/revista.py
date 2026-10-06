from .publicacao import Publicacao

class Revista(Publicacao):
    def __init__(self, titulo, autor, ano, nota, status, id, genero, paginas, pagina_atual, data_inclusao, data_inicio, data_termino, resenha, anotacoes, estado, edicao, issn):
        super().__init__(titulo, autor, ano, nota, status, id, genero, paginas, pagina_atual, data_inclusao, data_inicio, data_termino, resenha, anotacoes, estado)
        self._edicao = edicao
        self._issn = issn

    @property
    def edicao(self):
        return self._edicao

    @edicao.setter
    def edicao(self, valor):
        self._edicao = valor

    @property
    def issn(self):
        return self._issn

    @issn.setter
    def issn(self, valor):
        self._issn = valor

    def tipo(self): return "revista"
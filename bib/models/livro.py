from .publicacao import Publicacao

class Livro(Publicacao):
    def __init__(self, titulo, autor, ano, nota, status, id, genero, paginas, pagina_atual, data_inclusao, data_inicio, data_termino, resenha, anotacoes, estado, editora, isbn):
        super().__init__(titulo, autor, ano, nota, status, id, genero, paginas, pagina_atual, data_inclusao, data_inicio, data_termino, resenha, anotacoes, estado)
        self._editora = editora
        self._isbn = isbn

    @property
    def editora(self):
        return self._editora

    @editora.setter
    def editora(self, valor):
        self._editora = valor

    @property
    def isbn(self):
        return self._isbn

    @isbn.setter
    def isbn(self, valor):
        self._isbn = valor
    
    def tipo(self): return "livro"
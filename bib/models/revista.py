from .publicacao import Publicacao

"""Subclasse de Publicação, representando uma revista."""
class Revista(Publicacao):
    def __init__(self, titulo, autor, ano, nota, status, id, genero, paginas, pagina_atual, data_inclusao, data_inicio, data_termino, resenha, anotacoes, estado, edicao, issn):
        super().__init__(titulo, autor, ano, nota, status, id, genero, paginas, pagina_atual, data_inclusao, data_inicio, data_termino, resenha, anotacoes, estado)
        self.edicao = edicao
        self.issn = issn

    def tipo(self): return "revista"
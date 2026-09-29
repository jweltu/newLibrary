from publicacao import Publicacao

class Revista(Publicacao):
    def __init__(self, titulo, autor, ano, nota, status, id, genero, paginas, pagina_atual, data_inclusao, data_inicio, data_termino, resenha, anotacoes, estado, editora, issn):
        super().__init__(titulo, autor, ano, nota, status, id, genero, paginas, pagina_atual, data_inclusao, data_inicio, data_termino, resenha, anotacoes, estado)
        self.editora = editora
        self.issn = issn
class Anotacao:
    def __init__(self, texto, id, publicacao_id, categoria, data, trecho=None, pagina=None):
        self.texto = texto
        self.id = id
        self.publicacao_id = publicacao_id
        self.categoria = categoria
        self.data = data
        self.trecho = trecho
        self.pagina = pagina
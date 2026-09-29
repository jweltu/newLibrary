class Anotacao:
    def __init__(self, texto, id, publicacao_id, categoria, data, trecho=None, pagina=None):
        self.texto = texto
        self.id = id
        self.publicacao_id = publicacao_id
        self.categoria = categoria
        self.data = data
        self.trecho = trecho
        self.pagina = pagina

    def __repr__(self):
        return f"Anotacao(texto={self.texto}, id={self.id}, publicacao_id={self.publicacao_id}, categoria={self.categoria}, data={self.data}, trecho={self.trecho}, pagina={self.pagina})"

    def to_dict(self):
        return {
            "texto": self.texto,
            "id": self.id,
            "publicacao_id": self.publicacao_id,
            "categoria": self.categoria,
            "data": self.data,
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
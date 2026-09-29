class RegistroLeitura:
    def __init__(self, publicacao_id, data_inicio, data_final, pagina_final):
        self.publicacao_id = publicacao_id
        self.data_inicio = data_inicio
        self.data_final = data_final
        self.pagina_final = pagina_final

    def duracao_dias(self):
        from datetime import datetime
        if self.data_inicio and self.data_final:
            inicio = datetime.strptime(self.data_inicio, "%Y-%m-%d")
            final = datetime.strptime(self.data_final, "%Y-%m-%d")
            return (final - inicio).days
        return None
    
    def to_dict(self):
        return {
            "publicacao_id": self.publicacao_id,
            "data_inicio": self.data_inicio,
            "data_final": self.data_final,
            "pagina_final": self.pagina_final
        }
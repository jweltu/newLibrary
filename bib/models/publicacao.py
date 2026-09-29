from mixins import SerializavelMixin
from abc import ABC

class Publicacao(SerializavelMixin, ABC):
    def __init__(self, titulo, autor, ano, nota, status, id, genero, paginas, pagina_atual, data_inclusao, data_inicio, data_termino, resenha, anotacoes, estado):
        self._titulo = titulo
        self._autor = autor
        self._ano = ano
        self._nota = nota
        self._status = status
        self.id = id
        self.genero = genero
        self.paginas = paginas
        self.pagina_atual = pagina_atual
        self.data_inclusao = data_inclusao
        self.data_inicio = data_inicio
        self.data_termino = data_termino
        self.resenha = resenha
        self.anotacoes = anotacoes
        self.estado = estado

    @property
    def __str__(self):
        return f"{self._titulo} by {self._autor} ({self._ano})"

    @property
    def __eq__(self, outro):
        return (self._titulo, self._autor) == (outro._titulo, outro._autor)

    def __lt__(self, outro): return self._ano < outro._ano

    def __hash__(self): return hash((self._titulo, self._autor))

    def __repr__(self):
        return f"Publicacao(titulo={self._titulo}, autor={self._autor}, ano={self._ano})"

    def tipo(self):
        pass
    
    def iniciar_leitura(self, data):
        pass

    def atualizar_progresso(self, pagina):
        pass
    
    def concluir_leitura(self, data):
        pass
    
    def avaliar(self, nota, resenha):
        pass
    
    def percentual_lido(self):
        pass

    def dias_de_leitura(self):
        pass
    
    def adicionar_anotacao(self, texto, categoria, trecho=None, pagina=None, ):
        pass
    
    def listar_anotacoes(self):
        pass
    
    def to_dict(self):
        pass

    




        
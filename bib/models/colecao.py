class Colecao:
    def __init__(self, publicacoes):
        self._publicacoes = publicacoes

    @property
    def publicacoes(self):
        return self._publicacoes

    def __len__(self):
        return len(self._publicacoes)

    def __iter__(self):
        return iter(self._publicacoes)

    def adicionar(self, pub):
        pass

    def remover(self, id):
        pass

    def obter(self, id):
        pass

    def existe(self, titulo, autor):
        pass

    def buscar(self, titulo=None, autor=None, genero=None, status=None):
        pass

    def filtrar(self, inicio, fim):
        pass

    def em_leitura(self):
        pass

    def concluidas_no_ano(self):
        pass

    def contar_por_status(self, status):
        pass

    def ordenadas(self):
        pass
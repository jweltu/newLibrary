from abc import ABC, abstractmethod
from datetime import date

from .anotacao import Anotacao
from .enums import CategoriaAnotacao, StatusLeitura
from .mixins import SerializavelMixin
from ..excecoes import TransicaoStatusError, ValidacaoError

class Publicacao(SerializavelMixin, ABC):
    def __init__(self, titulo, autor, ano, nota, status, id, genero, paginas, pagina_atual, data_inclusao, data_inicio, data_termino, resenha, anotacoes, estado):
        self.titulo = titulo
        self.autor = autor
        self.ano = ano
        self.nota = nota
        self._status = self._normalizar_status(status)
        self._id = id
        self._genero = genero
        self.paginas = paginas
        self.pagina_atual = pagina_atual
        self._data_inclusao = data_inclusao
        self._data_inicio = data_inicio
        self._data_termino = data_termino
        self._resenha = resenha
        self._anotacoes = list(anotacoes or [])
        self._estado = estado

    @staticmethod
    def _normalizar_status(status):
        if isinstance(status, StatusLeitura):
            return status
        if hasattr(status, "status") and callable(status.status):
            status = status.status()
        try:
            return StatusLeitura(status)
        except (TypeError, ValueError):
            try:
                return StatusLeitura[status]
            except (KeyError, TypeError):
                raise ValidacaoError("Status inválido") from None

    @property
    def titulo(self):
        return self._titulo

    @titulo.setter
    def titulo(self, valor):
        if not isinstance(valor, str) or not valor.strip():
            raise ValidacaoError("O título não pode ser vazio")
        self._titulo = valor.strip()

    @property
    def autor(self):
        return self._autor

    @autor.setter
    def autor(self, valor):
        if not isinstance(valor, str) or not valor.strip():
            raise ValidacaoError("O autor não pode ser vazio")
        self._autor = valor.strip()

    @property
    def ano(self):
        return self._ano

    @ano.setter
    def ano(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1500:
            raise ValidacaoError("O ano deve ser um inteiro maior ou igual a 1500")
        self._ano = valor

    @property
    def nota(self):
        return self._nota

    @nota.setter
    def nota(self, valor):
        if valor is not None and (
            isinstance(valor, bool)
            or not isinstance(valor, (int, float))
            or not 0 <= valor <= 10
        ):
            raise ValidacaoError("A nota deve estar entre 0 e 10")
        self._nota = float(valor) if valor is not None else None

    @property
    def status(self):
        return self._status

    @property
    def id(self):
        return self._id

    @property
    def genero(self):
        return self._genero

    @genero.setter
    def genero(self, valor):
        self._genero = valor

    @property
    def paginas(self):
        return self._paginas

    @paginas.setter
    def paginas(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ValidacaoError("A publicação deve ter ao menos uma página")
        if hasattr(self, "_pagina_atual") and self._pagina_atual > valor:
            raise ValidacaoError("O total de páginas não pode ser menor que o progresso")
        self._paginas = valor

    @property
    def pagina_atual(self):
        return self._pagina_atual

    @pagina_atual.setter
    def pagina_atual(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
            raise ValidacaoError("A página atual deve ser um inteiro não negativo")
        if hasattr(self, "_paginas") and valor > self._paginas:
            raise ValidacaoError("A página atual não pode superar o total de páginas")
        self._pagina_atual = valor

    @property
    def data_inclusao(self):
        return self._data_inclusao

    @data_inclusao.setter
    def data_inclusao(self, valor):
        self._data_inclusao = valor

    @property
    def data_inicio(self):
        return self._data_inicio

    @data_inicio.setter
    def data_inicio(self, valor):
        self._data_inicio = valor

    @property
    def data_termino(self):
        return self._data_termino

    @data_termino.setter
    def data_termino(self, valor):
        self._data_termino = valor

    @property
    def resenha(self):
        return self._resenha

    @resenha.setter
    def resenha(self, valor):
        self._resenha = valor

    @property
    def anotacoes(self):
        return self._anotacoes.copy()

    @property
    def estado(self):
        return self._estado

    def __str__(self):
        return f"{self._titulo} by {self._autor} ({self._ano})"

    def __eq__(self, outro):
        if not isinstance(outro, Publicacao):
            return NotImplemented
        return (self._titulo, self._autor) == (outro._titulo, outro._autor)

    def __lt__(self, outro): return self._ano < outro._ano

    def __hash__(self): return hash((self._titulo, self._autor))

    def __repr__(self):
        return f"Publicacao(titulo={self._titulo}, autor={self._autor}, ano={self._ano})"

    @abstractmethod
    def tipo(self):
        raise NotImplementedError
    
    def iniciar_leitura(self, data=None):
        if self.status is not StatusLeitura.NAO_LIDO:
            raise TransicaoStatusError("A leitura só pode ser iniciada para uma publicação não lida")
        self.data_inicio = data or date.today()
        self.data_termino = None
        self._status = StatusLeitura.LENDO

    def atualizar_progresso(self, pagina):
        if self.status is not StatusLeitura.LENDO:
            raise TransicaoStatusError("O progresso só pode ser atualizado durante a leitura")
        self.pagina_atual = pagina
    
    def concluir_leitura(self, data=None):
        if self.status is not StatusLeitura.LENDO or self.data_inicio is None:
            raise TransicaoStatusError("Não é possível concluir uma leitura que não foi iniciada")
        data_termino = data or date.today()
        if data_termino < self.data_inicio:
            raise ValidacaoError("A data de término não pode anteceder a data de início")
        self.data_termino = data_termino
        self.pagina_atual = self.paginas
        self._status = StatusLeitura.LIDO
    
    def avaliar(self, nota, resenha=None):
        if self.status is not StatusLeitura.LIDO:
            raise TransicaoStatusError("A publicação só pode ser avaliada após a leitura")
        self.nota = nota
        self.resenha = resenha
    
    def percentual_lido(self):
        return self.pagina_atual / self.paginas * 100

    def dias_de_leitura(self):
        if self.data_inicio is None or self.data_termino is None:
            return None
        return (self.data_termino - self.data_inicio).days
    
    def adicionar_anotacao(self, texto, trecho=None, pagina=None, categoria=CategoriaAnotacao.ANOTACAO):
        from uuid import uuid4

        anotacao = Anotacao(
            texto=texto,
            id=str(uuid4()),
            publicacao_id=str(self.id),
            categoria=categoria,
            data=date.today(),
            trecho=trecho,
            pagina=pagina,
        )
        if pagina is not None and (pagina < 1 or pagina > self.paginas):
            raise ValidacaoError("A página da anotação deve estar dentro da publicação")
        self._anotacoes.append(anotacao)
        return anotacao
    
    def listar_anotacoes(self):
        return self.anotacoes
    
    def to_dict(self):
        dados = {
            "titulo": self.titulo,
            "autor": self.autor,
            "ano": self.ano,
            "nota": self.nota,
            "status": self.status.value,
            "id": self.id,
            "genero": self.genero,
            "paginas": self.paginas,
            "pagina_atual": self.pagina_atual,
            "data_inclusao": self._serializar(self.data_inclusao),
            "data_inicio": self._serializar(self.data_inicio),
            "data_termino": self._serializar(self.data_termino),
            "resenha": self.resenha,
            "anotacoes": [anotacao.to_dict() for anotacao in self._anotacoes],
        }
        for nome in ("editora", "isbn", "edicao", "issn"):
            if hasattr(self, nome):
                dados[nome] = getattr(self, nome)
        return dados

    @classmethod
    def from_dict(cls, dados):
        parse_data = cls._parse_data
        anotacoes = [Anotacao.from_dict(item) for item in dados.get("anotacoes", [])]
        argumentos = [
            dados.get("titulo"), dados.get("autor"), dados.get("ano"),
            dados.get("nota"), dados.get("status", StatusLeitura.NAO_LIDO.value),
            dados.get("id"), dados.get("genero"), dados.get("paginas"),
            dados.get("pagina_atual", 0), parse_data(dados.get("data_inclusao")),
            parse_data(dados.get("data_inicio")), parse_data(dados.get("data_termino")),
            dados.get("resenha"), anotacoes, None,
        ]
        for campo in ("editora", "isbn", "edicao", "issn"):
            if campo in dados:
                argumentos.append(dados[campo])
        return cls(*argumentos)

    




        
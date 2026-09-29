from enum import Enum

class StatusLeitura(Enum):
    """Estados possíveis de leitura de uma publicação."""
    NAO_LIDO = "NÃO LIDO"
    LENDO = "LENDO"
    LIDO = "LIDO"


class CategoriaAnotacao(Enum):
    """Distingue anotações livres de destaques."""
    ANOTACAO = "anotacao"
    DESTAQUE = "destaque"
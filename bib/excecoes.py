"""Exceções do domínio da biblioteca pessoal."""


class BibliotecaError(Exception):
    def __init__(self, mensagem: str = "") -> None:
        self.mensagem = mensagem
        super().__init__(mensagem)


class ValidacaoError(BibliotecaError):
    """Lançada quando um valor de uma publicação não atende à validação."""


class TransicaoStatusError(BibliotecaError):
    """Lançada quando uma transição inválida de status de leitura é tentada."""


class PublicacaoDuplicadaError(BibliotecaError):
    """Lançada quando uma publicação com mesmo título e autor já existe."""


class LimiteLeiturasError(BibliotecaError):
    """Lançada quando o limite de leituras simultâneas é excedido."""


class PublicacaoNaoEncontradaError(BibliotecaError):
    """Lançada quando uma publicação não é localizada no acervo."""


__all__ = [
    "BibliotecaError",
    "ValidacaoError",
    "TransicaoStatusError",
    "PublicacaoDuplicadaError",
    "LimiteLeiturasError",
    "PublicacaoNaoEncontradaError",
]

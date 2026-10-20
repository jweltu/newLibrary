from bib.repository import criar_repositorio


def salvar_publicacoes(colecao, caminho, formato="json"):
    criar_repositorio(formato, caminho).salvar(colecao)


def carregar_publicacoes(caminho, formato="json"):
    return criar_repositorio(formato, caminho).carregar()

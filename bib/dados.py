from bib.repository.json_repo import RepositorioJSON


def salvar_publicacoes(colecao, caminho):
    RepositorioJSON(caminho).salvar(colecao)


def carregar_publicacoes(caminho):
    return RepositorioJSON(caminho).carregar()

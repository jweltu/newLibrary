# UML textual do NewLibrary

Este documento descreve a estrutura implementada no projeto. A persistência
operacional padrão é SQLite; o repositório JSON permanece disponível como
alternativa interna. Os diagramas usam uma notação textual simplificada.

## Modelo de domínio

```text
«enum» StatusLeitura
-------------------------------------------
NAO_LIDO = "NÃO LIDO"
LENDO    = "LENDO"
LIDO     = "LIDO"

«enum» CategoriaAnotacao
-------------------------------------------
ANOTACAO = "anotacao"
DESTAQUE = "destaque"

BibliotecaError(Exception)
├── ValidacaoError
├── TransicaoStatusError
├── PublicacaoDuplicadaError
├── LimiteLeiturasError
└── PublicacaoNaoEncontradaError

SerializavelMixin
-------------------------------------------
+ to_dict(): dict
+ @classmethod from_dict(dados): Self
+ _serializar(valor): Any
+ _parse_data(valor): date | None

«abstract» Publicacao(SerializavelMixin, ABC)
-------------------------------------------
- _titulo: str
- _autor: str
- _ano: int
- _nota: float | None
- _status: StatusLeitura
- _id: str
- _paginas: int
- _pagina_atual: int
- _anotacoes: list[Anotacao]
- _estado: object | None
+ genero: str
+ data_inclusao: date | None
+ data_inicio: date | None
+ data_termino: date | None
+ resenha: str | None
+ status: StatusLeitura «somente leitura»
+ anotacoes: list[Anotacao] «cópia»
-------------------------------------------
+ tipo(): str «abstrato»
+ iniciar_leitura(data: date | None): None
+ atualizar_progresso(pagina: int): None
+ concluir_leitura(data: date | None): None
+ avaliar(nota: float, resenha: str | None): None
+ percentual_lido(): float
+ dias_de_leitura(): int | None
+ adicionar_anotacao(texto, trecho, pagina, categoria): Anotacao
+ listar_anotacoes(): list[Anotacao]
+ to_dict(): dict
+ from_dict(dados): Publicacao «implementado nas subclasses»

Livro(Publicacao)
-------------------------------------------
+ editora: str | None
+ isbn: str | None
+ tipo(): str  «"livro"»

Revista(Publicacao)
-------------------------------------------
+ edicao: str | None
+ issn: str | None
+ tipo(): str  «"revista"»

Anotacao
-------------------------------------------
- _texto: str
- _id: str
- _publicacao_id: str
- _categoria: CategoriaAnotacao
- _data: date
- _trecho: str | None
- _pagina: int | None
-------------------------------------------
+ to_dict(): dict
+ @classmethod from_dict(dados): Anotacao

Colecao
-------------------------------------------
- _publicacoes: dict[str, Publicacao]
-------------------------------------------
+ publicacoes: dict[str, Publicacao]
+ proximo_id(): str
+ adicionar(pub: Publicacao): None
+ remover(id: str): None
+ obter(id: str): Publicacao
+ existe(titulo: str, autor: str): bool
+ buscar(titulo, autor, genero, status): list[Publicacao]
+ filtrar(inicio: date, fim: date): list[Publicacao]
+ filtrar_por_periodo(inicio: date, fim: date): list[Publicacao]
+ filtrar_por_periodo_leitura(inicio: date, fim: date): list[Publicacao]
+ em_leitura(): list[Publicacao]
+ concluidas_no_ano(ano: int): int
+ contar_por_status(status: StatusLeitura): int
+ ordenadas(): list[Publicacao]
+ __len__(): int
+ __iter__(): Iterator[Publicacao]

RegistroLeitura
-------------------------------------------
+ publicacao_id: str
+ data_inicio: str
+ data_final: str | None
+ pagina_final: int | None
-------------------------------------------
+ duracao_dias(): int | None
+ to_dict(): dict
```

### Regras e relações do domínio

```text
Publicacao <|-- Livro
Publicacao <|-- Revista
Publicacao ..|> SerializavelMixin
Publicacao "1" *-- "0..*" Anotacao
Colecao "1" o-- "0..*" Publicacao
Publicacao ..> StatusLeitura
Anotacao ..> CategoriaAnotacao
Colecao ..> PublicacaoDuplicadaError
Colecao ..> PublicacaoNaoEncontradaError
Publicacao ..> ValidacaoError
Publicacao ..> TransicaoStatusError
```

- `Livro` e `Revista` implementam `tipo()` e a reconstrução a partir de dados
  serializados herdados de `Publicacao`.
- O status é controlado diretamente por `Publicacao`: iniciar uma publicação
  não lida define a data de início; concluir exige uma leitura iniciada e define
  a data de término; avaliar exige status `LIDO`.
- A coleção rejeita IDs repetidos e publicações com mesmo título e autor.
  `proximo_id()` gera o próximo identificador numérico como texto.
- A busca combina filtros parciais de título, autor e gênero com status. Os
  filtros de período de leitura consideram leituras em andamento que se
  sobreponham ao intervalo informado.
- `RegistroLeitura` existe como classe, mas não está associado à publicação nem
  é utilizado pelo fluxo ativo de leitura.
- O pacote `bib.states` contém classes de estado legadas, mas elas não
  implementam o fluxo de transição usado pelo modelo. As operações de leitura
  atualmente são implementadas diretamente em `Publicacao`.

## Persistência e configurações

```text
RepositorioPublicacoes
-------------------------------------------
+ salvar(colecao: Colecao): None
+ carregar(): Colecao

RepositorioSQLite(RepositorioPublicacoes)
-------------------------------------------
- _caminho_db: Path
-------------------------------------------
+ salvar(colecao: Colecao): None
+ carregar(): Colecao
+ _migrar_ids_numericos(conexao): None «estático»

RepositorioJSON(RepositorioPublicacoes)
-------------------------------------------
- _caminho: Path
-------------------------------------------
+ salvar(colecao: Colecao): None
+ carregar(): Colecao

Configuracoes
-------------------------------------------
- _genero_favorito: str | None
- _limite_leituras_simultaneas: int
- _meta_anual: int
-------------------------------------------
+ carregar(caminho: str | Path = "settings.json"): Configuracoes
+ salvar(caminho: str | Path = "settings.json"): None
```

```text
«módulo» bib.dados
+ salvar_publicacoes(colecao, caminho, formato = "sqlite"): None
+ carregar_publicacoes(caminho, formato = "sqlite"): Colecao

«módulo» bib.repository
+ criar_repositorio(formato, caminho): RepositorioPublicacoes
```

`RepositorioPublicacoes` fornece os métodos de contrato usados pelos
repositórios concretos. `RepositorioSQLite` é o padrão para persistência do
acervo, enquanto `RepositorioJSON` pode ser escolhido explicitamente em código
por `formato="json"`. O repositório SQLite armazena as publicações e seus dados
serializados na tabela `publicacoes`; ao carregar, migra IDs legados para IDs
numéricos sequenciais e atualiza os vínculos das anotações.

`Configuracoes` valida o gênero favorito, o limite positivo de publicações em
leitura simultânea e a meta anual não negativa. A configuração é persistida em
`settings.json`, separadamente do acervo SQLite.

```text
RepositorioPublicacoes <|-- RepositorioSQLite
RepositorioPublicacoes <|-- RepositorioJSON
RepositorioSQLite ..> Colecao
RepositorioJSON ..> Colecao
bib.dados ..> RepositorioSQLite
bib.dados ..> RepositorioJSON
```

## Relatórios

```text
«abstract» EstrategiaRelatorio
-------------------------------------------
+ gerar(colecao: Colecao): dict[str, object]

RelatorioTotal(EstrategiaRelatorio)
RelatorioPorStatus(EstrategiaRelatorio)
RelatorioMediaAvaliacoes(EstrategiaRelatorio)
RelatorioTopAvaliadas(EstrategiaRelatorio)
RelatorioProgressoAnual(EstrategiaRelatorio)
-------------------------------------------
RelatorioProgressoAnual:
- _meta: int
- _ano: int
+ __init__(meta: int, ano: int)

GeradorRelatorios
-------------------------------------------
- _estrategia: EstrategiaRelatorio
-------------------------------------------
+ definir_estrategia(estrategia): None
+ executar(colecao: Colecao): dict[str, object]
```

```text
EstrategiaRelatorio <|-- RelatorioTotal
EstrategiaRelatorio <|-- RelatorioPorStatus
EstrategiaRelatorio <|-- RelatorioMediaAvaliacoes
EstrategiaRelatorio <|-- RelatorioTopAvaliadas
EstrategiaRelatorio <|-- RelatorioProgressoAnual
GeradorRelatorios o-- EstrategiaRelatorio
```

As estratégias geram o total do acervo, quantidades e percentuais por status,
média das avaliações de publicações lidas, top 5 avaliadas e progresso anual.
O top 5 informa quando não há pelo menos cinco publicações lidas e avaliadas.

## Interfaces e módulos de entrada

```text
bib.interface
  Interface CLI interativa; apresenta menus, operações do acervo,
  configurações e relatórios em texto legível.

bib.cli
  Interface de linha de comando por argumentos; cadastra, lista, edita,
  remove, altera status, avalia, anota e gera relatórios.

bib.api
  create_app(arquivo) -> FastAPI
  Endpoints HTTP para publicações, status, progresso, anotações,
  relatórios e configurações.

bib.__main__
  Ponto de entrada para executar a aplicação como módulo Python.
```

```text
bib.interface ..> Colecao
bib.interface ..> Configuracoes
bib.cli ..> Colecao
bib.cli ..> bib.dados
bib.api ..> Colecao
bib.api ..> bib.dados
bib.api ..> GeradorRelatorios
```

## Organização do código

```text
bib/
├── api.py
├── cli.py
├── config.py
├── dados.py
├── excecoes.py
├── interface.py
├── service.py
├── models/
│   ├── anotacao.py
│   ├── colecao.py
│   ├── enums.py
│   ├── livro.py
│   ├── mixins.py
│   ├── publicacao.py
│   ├── registro_leitura.py
│   └── revista.py
├── relatorio/
│   ├── base.py
│   ├── estrategias.py
│   └── gerador.py
├── repository/
│   ├── base.py
│   ├── json_repo.py
│   └── sqlite_repo.py
└── states/
    └── estado_leitura.py
```

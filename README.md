# 📚NewLibrary - Projeto de Biblioteca Pessoal Digital desenvolvida em Python

## 1. Definição do Projeto

O **NewLibrary** é um sistema para o gerenciamento e manutenção de uma biblioteca pessoal de livros e revistas digitais, com a finalidade de controle de leitura do usuário. Algumas funcionalidades que serão implementadas no projeto consiste em:

- Cadastro de Publicações;
- Registro de Leituras;
- Controle de Status de Leitura;
- Relatórios Sobre o Acervo pessoal.


## 2. UML do Projeto

### 2.1. Enumeração e Exceções:

```
«enumeration»
StatusLeitura
------------------------------
NAO_LIDO = "NÃO LIDO"
LENDO    = "LENDO"
LIDO     = "LIDO"

«enumeration»
CategoriaAnotacao
------------------------------
ANOTACAO = "anotacao"
DESTAQUE = "destaque"

BibliotecaError(Exception)
├── ValidacaoError                      (título vazio, ano < 1500, nota fora de 0–10)
├── TransicaoStatusError                (LIDO sem início, avaliar antes de LIDO)
├── PublicacaoDuplicadaError            (mesmo título + autor)
├── LimiteLeiturasError                 (excede leituras simultâneas)
└── PublicacaoNaoEncontradaError
```

### 2.2. Mixins (Herança Multipla)

```
«mixin»
SerializavelMixin
------------------------------------------------------------
(sem atributos)
------------------------------------------------------------
+ to_dict(): dict
+ @classmethod from_dict(dados: dict): Publicacao

```

### 2.3. Modelo de Domínio das Classes

```
«abstract»
Publicacao(SerializavelMixin, ABC)
------------------------------------------------------------
- _titulo: str                          «property» validado (não vazio)
- _autor: str
- _ano: int                             «property» validado (>= 1500)
- _nota: float | None                   «property» validado (0–10)
- _status: StatusLeitura                «property» somente leitura
+ id: str
+ genero: str
+ paginas: int
+ pagina_atual: int
+ data_inclusao: date
+ data_inicio: date | None
+ data_termino: date | None
+ resenha: str | None
+ anotacoes: list[Anotacao]
+ leituras: list[RegistroLeitura]
- _estado: EstadoLeitura                (padrão State)

------------------------------------------------------------
+ «abstract» tipo(): str
+ iniciar_leitura(data: date = None): None
+ atualizar_progresso(pagina: int): None
+ concluir_leitura(data: date = None): None
+ avaliar(nota: float, resenha: str = None): None
+ percentual_lido(): float
+ dias_de_leitura(): int | None
+ adicionar_anotacao(texto, trecho=None, pagina=None, categoria=ANOTACAO): Anotacao
+ listar_anotacoes(): list[Anotacao]
+ to_dict(): dict
+ __str__(): str
+ __repr__(): str
+ __lt__(outro: Publicacao): bool       (ordena por ano)
+ __eq__(outro: Publicacao): bool       (título + autor)
+ __hash__(): int

Livro(Publicacao)
------------------------------------------------------------
+ isbn: str | None
+ editora: str | None
------------------------------------------------------------
+ tipo(): str                           (retorna "livro")

Revista(Publicacao)
------------------------------------------------------------
+ edicao: str | None
+ issn: str | None
------------------------------------------------------------
+ tipo(): str                           (retorna "revista")

Anotacao
------------------------------------------------------------
- _texto: str                           «property» validado (não vazio)
+ id: str
+ publicacao_id: str                    (associação com Publicacao)
+ trecho: str | None                    (opcional)
+ pagina: int | None
+ categoria: CategoriaAnotacao
+ data: date
------------------------------------------------------------
+ to_dict(): dict
+ @classmethod from_dict(dados: dict): Anotacao
+ __str__(): str

RegistroLeitura
------------------------------------------------------------
+ data_inicio: date
+ data_termino: date | None
+ pagina_final: int | None
------------------------------------------------------------
+ duracao_dias(): int | None
+ to_dict(): dict

Colecao
------------------------------------------------------------
- _publicacoes: dict[str, Publicacao]   (chave = id)
------------------------------------------------------------
+ adicionar(pub: Publicacao): None      (lança PublicacaoDuplicadaError)
+ remover(id: str): None
+ obter(id: str): Publicacao
+ existe(titulo: str, autor: str): bool
+ buscar(titulo=None, autor=None, genero=None, status=None): list[Publicacao]
+ filtrar_por_periodo(inicio: date, fim: date): list[Publicacao]
+ em_leitura(): list[Publicacao]
+ concluidas_no_ano(ano: int): int
+ contar_por_status(status: StatusLeitura): int
+ ordenadas(): list[Publicacao]         (usa __lt__)
+ __len__(): int
+ __iter__(): Iterator[Publicacao]

`Colecao` recebe um dicionário de publicações indexado por ID (ou pode ser
criada vazia) e a iteração percorre os objetos `Publicacao`. `adicionar`
rejeita IDs duplicados e publicações com o mesmo título e autor;
`obter`/`remover` lançam `PublicacaoNaoEncontradaError` quando o ID não existe.
`buscar` combina filtros de texto parciais, sem diferenciar maiúsculas, e um
status opcional. `filtrar` e `filtrar_por_periodo` incluem os limites do período
de data de inclusão; `concluidas_no_ano(ano)` conta publicações lidas cuja data
de término pertence ao ano informado.

Configuracoes
------------------------------------------------------------
+ genero_favorito: str | None
+ limite_leituras_simultaneas: int      (padrão: 3)
+ meta_anual: int                       (padrão: 0)
------------------------------------------------------------
+ @classmethod carregar(caminho: str = "settings.json"): Configuracoes
+ salvar(caminho: str = "settings.json"): None

```

O arquivo `Configuracoes` valida os valores ao inicializar e sempre que um atributo é
alterado: `limite_leituras_simultaneas` deve ser inteiro positivo, `meta_anual`
deve ser inteiro não negativo (zero desativa a meta) e `genero_favorito` deve
ser um texto não vazio ou `None`.

### 2.4. Padrão State

```
«abstract»
EstadoLeitura
------------------------------------------------------------
(sem atributos)
------------------------------------------------------------
+ «abstract» status(): StatusLeitura
+ «abstract» iniciar(pub: Publicacao, data: date): None
+ «abstract» concluir(pub: Publicacao, data: date): None
+ «abstract» pode_avaliar(): bool

EstadoNaoLido(EstadoLeitura)
------------------------------------------------------------
+ status(): StatusLeitura               (NAO_LIDO)
+ iniciar(pub, data): None              (define data_inicio, muda para EstadoLendo)
+ concluir(pub, data): None             (lança TransicaoStatusError: sem data de início)
+ pode_avaliar(): bool                  (False)

EstadoLendo(EstadoLeitura)
------------------------------------------------------------
+ status(): StatusLeitura               (LENDO)
+ iniciar(pub, data): None              (lança TransicaoStatusError)
+ concluir(pub, data): None             (exige data_inicio, define data_termino, muda para EstadoLido)
+ pode_avaliar(): bool                  (False)

EstadoLido(EstadoLeitura)
------------------------------------------------------------
+ status(): StatusLeitura               (LIDO)
+ iniciar(pub, data): None              (lança TransicaoStatusError)
+ concluir(pub, data): None             (lança TransicaoStatusError)
+ pode_avaliar(): bool                  (True)

```

### 2.5. Padrão Repository e Módulo

```
«abstract»
RepositorioPublicacoes
------------------------------------------------------------
(sem atributos)
------------------------------------------------------------
+ «abstract» salvar(colecao: Colecao): None
+ «abstract» carregar(): Colecao

RepositorioJSON(RepositorioPublicacoes)
------------------------------------------------------------
- _caminho: str
------------------------------------------------------------
+ salvar(colecao: Colecao): None        (json.dump)
+ carregar(): Colecao                   (json.load)

RepositorioSQLite(RepositorioPublicacoes)      «opcional»
------------------------------------------------------------
- _caminho_db: str
------------------------------------------------------------
+ salvar(colecao: Colecao): None
+ carregar(): Colecao

«módulo» dados.py
------------------------------------------------------------
+ salvar_publicacoes(colecao: Colecao, caminho: str): None
+ carregar_publicacoes(caminho: str): Colecao
```

O repositório grava uma lista JSON de publicações, incluindo suas anotações e o
tipo concreto (`livro` ou `revista`). Exemplo de uso:

```python
from bib.dados import carregar_publicacoes, salvar_publicacoes

salvar_publicacoes(colecao, "data/publicacoes.json")
colecao = carregar_publicacoes("data/publicacoes.json")
```

### 2.6. Padrão Strategy

```
«abstract»
EstrategiaRelatorio
------------------------------------------------------------
(sem atributos)
------------------------------------------------------------
+ «abstract» gerar(colecao: Colecao): dict

RelatorioTotal(EstrategiaRelatorio)
------------------------------------------------------------
+ gerar(colecao): dict                  ({"total": int})

RelatorioPorStatus(EstrategiaRelatorio)
------------------------------------------------------------
+ gerar(colecao): dict                  (quantidade e percentual: lidos, não lidos, lendo)

RelatorioMediaAvaliacoes(EstrategiaRelatorio)
------------------------------------------------------------
+ gerar(colecao): dict                  (média das notas das publicações LIDAS)

RelatorioProgressoAnual(EstrategiaRelatorio)
------------------------------------------------------------
- _meta: int
- _ano: int
------------------------------------------------------------
+ __init__(meta: int, ano: int)
+ gerar(colecao): dict                  (concluídas no ano, meta, % atingido, aviso)

GeradorRelatorios
------------------------------------------------------------
- _estrategia: EstrategiaRelatorio
------------------------------------------------------------
+ definir_estrategia(e: EstrategiaRelatorio): None
+ executar(colecao: Colecao): dict
```

As estratégias retornam dicionários prontos para a interface apresentar. O
relatório de status inclui quantidade e percentual por estado; a média considera
somente publicações lidas e avaliadas. Sem avaliações ou sem meta anual, o
percentual correspondente é `None`. O gerador pode trocar de estratégia sem
alterar a coleção:

```python
from bib.relatorio import GeradorRelatorios, RelatorioPorStatus

gerador = GeradorRelatorios(RelatorioPorStatus())
resultado = gerador.executar(colecao)
print(resultado["lidos"]["quantidade"])
```

As estratégias disponíveis são `RelatorioTotal`, `RelatorioPorStatus`,
`RelatorioMediaAvaliacoes` e `RelatorioProgressoAnual(meta, ano)`.

### 2.7. Relacionamentos:

```
Publicacao ◁── Livro, Revista                         herança simples
Publicacao ◁── SerializavelMixin, ABC                 herança múltipla
Publicacao  ◆── 0..* Anotacao                         composição
Publicacao  ◆── 0..* RegistroLeitura                  composição
Publicacao  ──► 1 EstadoLeitura                       State
Colecao     ◇── 0..* Publicacao                       agregação
EstadoLeitura ◁── EstadoNaoLido, EstadoLendo, EstadoLido
RepositorioPublicacoes ◁── RepositorioJSON, RepositorioSQLite
EstrategiaRelatorio ◁── Relatorio* (4 implementações)
GeradorRelatorios ◇── EstrategiaRelatorio             Strategy
```

## Estrutura de Arquivos:

```
biblioteca-pessoal/
├── README.md
├── settings.json
├── data/
├── bib/
│   ├── __init__.py
│   ├── __main__.py
│   ├── interface.py
│   ├── service.py
│   ├── config.py
│   ├── excecoes.py
│   ├── dados.py
│   ├── modelos/
│   │   ├── __init__.py
│   │   ├── enums.py
│   │   ├── mixins.py
│   │   ├── publicacao.py
│   │   ├── livro.py
│   │   ├── revista.py
│   │   ├── anotacao.py
│   │   ├── registro_leitura.py
│   │   └── colecao.py
│   ├── estados/
│   │   ├── __init__.py
│   │   └── estado_leitura.py
│   ├── repositorio/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── json_repo.py
│   │   └── sqlite_repo.py
│   └── relatorios/
│       ├── __init__.py
│       ├── base.py
│       ├── estrategias.py
│       └── gerador.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_publicacao.py
    ├── test_anotacao.py
    ├── test_estados.py
    ├── test_colecao.py
    ├── test_regras_negocio.py
    ├── test_persistencia.py
    ├── test_relatorios.py
    └── test_cli.py
```

## Interface de linha de comando

Instale o projeto para disponibilizar o comando `bib`:

```bash
python -m pip install .
```

O acervo é salvo por padrão em `~/.bib/publicacoes.json`. Use `--formato sqlite`
para persistir em SQLite (padrão `~/.bib/publicacoes.db`) e `--arquivo caminho`
para escolher explicitamente o caminho do arquivo.

```bash
bib cadastrar livro --titulo "Dom Casmurro" --autor "Machado de Assis" \
  --ano 1899 --paginas 256 --genero romance --editora Garnier
bib cadastrar revista --titulo "Revista de História" --autor "Equipe Editorial" \
  --ano 2024 --paginas 80 --edicao 42
bib listar
bib listar --status lendo
bib anotar ID_DA_PUBLICACAO --texto "Revisar este trecho" \
  --trecho "Trecho destacado" --pagina 12 --categoria destaque
bib relatorio
bib relatorio --tipo anual --meta 12 --ano 2026
bib listar --formato sqlite
```

Também é possível executar sem instalar o comando com `python -m bib` no lugar
de `bib`.

## API HTTP com FastAPI

A instalação do projeto inclui FastAPI e Uvicorn. Inicie o servidor com:

```bash
python -m pip install .
uvicorn bib.api:app --reload
```

A documentação interativa está em `http://127.0.0.1:8000/docs`. A API usa JSON
por padrão. Defina `BIB_FORMATO=sqlite` para usar SQLite ou `BIB_ARQUIVO` para
escolher o caminho do arquivo. A CLI e a API podem compartilhar o mesmo arquivo
e formato de persistência.

- `POST /publicacoes`: cadastra um livro ou uma revista.
- `GET /publicacoes`: lista com filtros opcionais `titulo`, `autor`, `genero`
  e `status`.
- `GET /publicacoes/{id}`: consulta uma publicação.
- `POST /publicacoes/{id}/anotacoes`: adiciona uma anotação ou destaque.
- `GET /relatorios/{tipo}`: retorna `completo`, `total`, `status`, `media` ou
  `anual` (com os parâmetros opcionais `meta` e `ano`).

## Testes automatizados

Instale o projeto e as dependências de desenvolvimento — isso também instala
FastAPI e Uvicorn, necessários para coletar e testar a API — e execute o pytest:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Para executar somente os testes de criação de objetos ou de validação:

```bash
python -m pytest tests/test_criacao_objetos.py
python -m pytest tests/test_validacao.py
```

## Componente Curricular

O **NewLibrary** é um projeto desenvolvido como componente para aplicar os conceitos e diretrizes da Programação Orientada a Objetos, como encapsulamento, herança (simples e múltipla), métodos especiais e regras de negócio configuráveis, utilizando o python como linguagem principal.

Além disso, também utiliza-se linguagens complementares, como **JSON** e **SQLite** para armazenamento e persistência de dados, além da implementação de testes por meio do **Pytest**.

O **NewLibrary** foi desenvolvido como componente da disciplina de Programação Orientada a Objetos, ministrada pelo professor Jayr Pereira, da graduação de Engenharia de Software na Universidade Federal do Cariri (UFCA).

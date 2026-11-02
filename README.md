# 📚NewLibrary - Projeto de Biblioteca Pessoal Digital desenvolvida em Python

## 1. Definição do Projeto

O **NewLibrary** é um sistema para o gerenciamento de uma biblioteca pessoal de livros e revistas digitais e para o controle de leitura do usuário. Entre suas funcionalidades estão:

- Cadastro de Publicações;
- Registro de Leituras;
- Controle de Status de Leitura;
- Relatórios Sobre o Acervo pessoal.


## UML do Projeto

A UML textual da implementação atual, incluindo modelo de domínio, persistência,
relatórios e módulos de interface, está documentada em [UML.md](UML.md).

## Estrutura de Arquivos

```text
newLibrary/
├── README.md
├── UML.md
├── settings.json
├── bib/
│   ├── api.py
│   ├── cli.py
│   ├── config.py
│   ├── dados.py
│   ├── excecoes.py
│   ├── interface.py
│   ├── models/
│   ├── relatorio/
│   ├── repository/
│   └── states/
└── tests/
```

## Interface de linha de comando

Para abrir a interface interativa com menus, execute o arquivo principal:

```bash
python main.py
```

Instale o projeto para disponibilizar o comando `bib`:

```bash
python -m pip install .
```

```bash
bib cadastrar livro --titulo "Dom Casmurro" --autor "Machado de Assis" \
  --ano 1899 --paginas 256 --genero romance --editora Garnier
bib cadastrar revista --titulo "Revista de História" --autor "Equipe Editorial" \
  --ano 2024 --paginas 80 --edicao 42
bib listar
bib listar --status lendo
bib listar --inicio 2026-01-01 --fim 2026-12-31
bib editar 1 --titulo "Dom Casmurro - edição revisada"
bib status 1 iniciar
bib status 1 concluir
bib avaliar 1 9.5 --resenha "Uma ótima leitura"
bib anotar ID_DA_PUBLICACAO --texto "Revisar este trecho" \
  --trecho "Trecho destacado" --pagina 12 --categoria destaque
bib anotacoes 1
bib remover 1
bib relatorio
bib relatorio --tipo top5
bib relatorio --tipo anual --meta 12 --ano 2026
bib configuracoes --genero-favorito "Ficção" --limite-leituras 3 --meta-anual 12
bib listar --arquivo caminho/para/publicacoes.db
```

As publicações são cadastradas inicialmente como **NÃO LIDO**. Use `status`
para iniciar e concluir uma leitura; as datas são registradas automaticamente,
e uma leitura não pode ser concluída antes de ser iniciada. Avaliações de 0 a
10 só podem ser atribuídas depois da conclusão. `editar`, `remover`, `anotar` e
`anotacoes` completam as operações do acervo. O filtro `--inicio`/`--fim`
considera o intervalo da leitura e inclui leituras em andamento que se
sobreponham ao período informado.

Os relatórios de status mostram as publicações e, separadamente, os livros.
As configurações opcionais são armazenadas em `settings.json`. O limite controla
quantas publicações podem estar simultaneamente em leitura; o gênero favorito é
sugerido no cadastro pelo menu e a meta anual é usada como valor inicial no
relatório anual. O relatório `top5` exige pelo menos cinco publicações lidas e
avaliadas; caso contrário, informa que faltam dados suficientes para o ranking.

Também é possível executar sem instalar o comando com `python -m bib` no lugar
de `bib`.

## API HTTP com FastAPI

A instalação do projeto inclui FastAPI e Uvicorn. Inicie o servidor com:

```bash
python -m pip install .
uvicorn bib.api:app --reload
```

A documentação interativa está em `http://127.0.0.1:8000/docs`. A API persiste
os dados em SQLite por padrão, no caminho `~/.bib/publicacoes.db`. Defina
`BIB_ARQUIVO` para escolher o caminho do banco. A CLI e a API podem compartilhar
o mesmo banco SQLite.

- `POST /publicacoes`: cadastra um livro ou uma revista.
- `GET /publicacoes`: lista com filtros opcionais `titulo`, `autor`, `genero`
  e `status`, além do período de leitura `inicio`/`fim`.
- `GET /publicacoes/{id}`: consulta uma publicação.
- `PATCH` e `DELETE /publicacoes/{id}`: atualiza ou remove uma publicação.
- `PATCH /publicacoes/{id}/status`: inicia ou conclui a leitura.
- `PATCH /publicacoes/{id}/progresso` e `POST /publicacoes/{id}/avaliacao`:
  atualizam o progresso e registram a avaliação após a leitura.
- `GET /publicacoes/{id}/anotacoes`: lista as anotações.
- `POST /publicacoes/{id}/anotacoes`: adiciona uma anotação ou destaque.
- `GET` e `PUT /configuracoes`: consulta e atualiza `settings.json`.
- `GET /relatorios/{tipo}`: retorna `completo`, `total`, `status`, `media`,
  `top5` ou `anual` (com os parâmetros opcionais `meta` e `ano`).

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

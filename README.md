# 📚NewLibrary - Projeto de Biblioteca Pessoal Digital desenvolvida em Python

## 1. Definição do Projeto

O **NewLibrary** é um sistema para o gerenciamento e manutenção de uma biblioteca pessoal de livros e revistas digitais, com a finalidade de controle de leitura do usuário. Algumas funcionalidades que serão implementadas no projeto consiste em:

- Cadastro de Publicações;
- Registro de Leituras;
- Controle de Status de Leitura;
- Relatórios Sobre o Acervo pessoal.


## 2. UML Textual

### 2.1. Publicação:

- Atributos:
  - id;
  - tipoPublicacao;
  - titulo;
  - ano;
  - autor;
  - paginas;
  - gênero;
  - dataInclusao;
  - dataInicioLeitura;
  - dataTerminoLeitura;
  - notaUsuario;
  - anotacoes - List[Anotacao];
  - leituras List[RegistroLeitura].

 
- Métodos:
  - tipo();
  - iniciarLeitura(data=None);
  - atualizarProgresso(pagina);
  - concluirLeitura(data=None);
  - avaliar(nota, resenha=None);
  - percentualLido();
  - diasLeitura();
  - listarAnotacoes();
  - adicionarAnotacao(texto, trecho=None, Pagina=None);
  - listarAnotacoes();

- Subclasses:
  - Livro(Publicacao);
    - isbn;
    - editora;
    - edicao.
    
  - revista(Publicacao);
    - numeroEdicao;
    - issn;
    - periodicidade (mensal, semanal, …);
    - editora.
    
- Herança Múltipla:
  - SerializavelMixin;
    - to_dict();
    - from_dict().
  - MidiaDigitalMixin.
    - abrirArquivo();

 
### 2.4. Leitura:

- Atributos:
- Métodos:

### 2.5. Anotação:

- Atributos:
- Métodos:

### 2.6. Coleção:

- Atributos:
- Métodos:

## 3. Componente Curricular

O **NewLibrary** é um projeto desenvolvido como componente para aplicar os conceitos e diretrizes da Programação Orientada a Objetos, como encapsulamento, herança (simples e múltipla), métodos especiais e regras de negócio configuráveis, utilizando o python como linguagem principal.

Além disso, também utiliza-se linguagens complementares, como **JSON** e **SQLite** para armazenamento e persistência de dados, além da implementação de testes por meio do **Pytest**.

O **NewLibrary** foi desenvolvido como componente da disciplina de Programação Orientada a Objetos, ministrada pelo professor Jayr Pereira, da graduação de Engenharia de Software na Universidade Federal do Cariri (UFCA).

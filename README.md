# Sistema de Emissão de Termos de Empréstimo e Transferência de Equipamentos

> **Propriedade Institucional e Desenvolvimento Interno**
> Este software foi **desenvolvido internamente** e pertence à **Secretaria Municipal de Educação, Cultura, Inclusão, Ciência e Tecnologia (SMECICT)** da **Prefeitura Municipal de Saquarema — Estado do Rio de Janeiro**. Todos os direitos e diretrizes de uso são reservados à administração pública municipal.

---

## 📋 Visão Geral

Aplicação de alta performance para geração automatizada de documentos oficiais em PDF — especificamente o **Termo de Empréstimo e Responsabilidade de Equipamento** da SMECICT / Prefeitura de Saquarema.

A solução combina uma **API REST em Python (FastAPI + Granian)** com um **motor nativo de compilação tipográfica em Rust (Typst + PyO3)**, permitindo gerar PDFs institucionais completos com tabelas dinâmicas e assinaturas digitais em imagem (Base64) em poucos milissegundos, sem depender de binários externos instalados no sistema operacional.

---

## 🏗️ Arquitetura e Stack Tecnológica

```mermaid
flowchart LR
    Client["Sistemas Internos / Frontend\n(Payload JSON + Assinatura Base64)"] -->|POST /api/v1/pdf/gerar\nPOST /api/v1/pdf/download| Granian["Granian ASGI Server\n+ FastAPI (Python)"]
    Granian -->|Chamada FFI Nativa\n(PyO3 / Maturin)| Rust["Módulo Rust\n(transferencia_pdf + Typst)"]
    PublicImages[("Pasta Pública\npublic/images/\ncabecalho.png\nrodape.png")] -->|Hot-Swap em Disco| Rust
    Rust -->|Gravação Física| PdfDir[("Pasta /pdf")]
    Rust -->|Bytestream Memória| Granian
```

| Camada | Tecnologia | Finalidade |
| :--- | :--- | :--- |
| **Motor de PDF** | **Rust** (`typst`, `typst-pdf`, `typst-as-lib`) | Compilação tipográfica 100% nativa em memória, sem dependência de CLI externo |
| **Ponte FFI** | **PyO3** + **Maturin** | Exposição do módulo Rust (`transferencia_pdf`) como extensão nativa para o Python |
| **API Web** | **FastAPI** + **Pydantic v2** | Validação estrita do payload JSON, documentação OpenAPI/Swagger e roteamento HTTP |
| **Servidor ASGI** | **Granian** | Servidor HTTP/ASGI de alta performance escrito em Rust |
| **Gerenciador Python** | **uv** | Gerenciamento ultrarrápido de pacotes, ambientes virtuais (`.venv`) e lockfile (`uv.lock`) |

---

## 📂 Estrutura do Projeto

```text
transferencia_equipamentos/
├── .env.example                 # Modelo de variáveis de ambiente e segurança
├── .gitignore                   # Regras de exclusão do Git (target, .venv, .env, PDFs gerados)
├── CHANGELOG.md                 # Histórico de versões e alterações vinculado aos commits
├── README.md                    # Documentação principal da aplicação
├── pdf/                         # Diretório de saída onde os PDFs gerados são armazenados
├── public/
│   └── images/                  # Imagens institucionais lidas dinamicamente em tempo de execução
│       ├── cabecalho.png        # Cabeçalho oficial da Prefeitura de Saquarema / SMECICT
│       └── rodape.png           # Rodapé institucional da Prefeitura de Saquarema
├── python/                      # Camada de API REST (FastAPI + Granian + uv)
│   ├── app.py                   # Aplicação FastAPI, middlewares de segurança e rotas
│   ├── main.py                  # Ponto de entrada do servidor Granian configurável via .env
│   ├── schemas.py               # Schemas Pydantic com validação estrita dos campos do termo
│   ├── test_api.py              # Suíte de testes automatizados (pytest)
│   ├── pyproject.toml           # Manifesto do projeto Python gerenciado pelo uv
│   └── uv.lock                  # Lockfile determinístico de dependências
└── rust/                        # Módulo nativo gerador de PDF (Rust + Typst + PyO3)
    ├── Cargo.toml               # Manifesto e dependências do crate Rust
    ├── pyproject.toml           # Configuração de build do Maturin (bindings PyO3)
    ├── src/
    │   ├── lib.rs               # Biblioteca principal, decodificador Base64 e bindings PyO3
    │   └── main.rs              # Executável CLI para testes diretos no terminal
    └── templates/
        └── termo.typ            # Template Typst oficial do Termo de Empréstimo (Saquarema)
```

---

## 🖼️ Substituição de Cabeçalho e Rodapé (`public/images/`)

Os arquivos visuais do cabeçalho e rodapé da Prefeitura Municipal de Saquarema estão localizados em:
- `public/images/cabecalho.png`
- `public/images/rodape.png`

O módulo Rust lê esses arquivos **diretamente do disco a cada geração de PDF** (*hot-swap*). Para atualizar para imagens de maior resolução ou novo layout institucional, basta substituir `cabecalho.png` e/ou `rodape.png` dentro de `public/images/` mantendo exatamente os mesmos nomes de arquivo — **não é necessário recompilar o módulo Rust nem reiniciar o servidor**.

---

## 🔒 Quesitos de Segurança Implementados

1. **Prevenção contra Path Traversal**:
   - O parâmetro `nome_arquivo` passa por higienização com `os.path.basename`, expressão regular restritiva e verificação criptográfica de caminho relativo (`Path.resolve().is_relative_to(PDF_DIR)`), garantindo que nenhum arquivo possa ser gravado fora do diretório `pdf/`.
2. **Proteção contra Exaustão de Memória (DoS) e Injeção de Campos**:
   - Schemas Pydantic configurados com `extra="forbid"` (rejeita qualquer atributo não mapeado com `HTTP 422`) e limites estritos de caracteres (`max_length`) em todos os campos.
   - Limite máximo de **5 MB** para imagens de assinatura em Base64 validado tanto na camada FastAPI quanto na camada Rust (`MAX_BASE64_SIGNATURE_LEN`).
   - Validação de assinatura binária (*magic bytes*) no Rust, aceitando exclusivamente imagens válidas (`PNG`, `JPEG`, `GIF` ou `SVG`).
3. **Autenticação Opcional por Chave de API (`X-API-Key`)**:
   - Quando a variável de ambiente `API_KEY` é definida, todas as rotas de geração de PDF exigem o cabeçalho `X-API-Key`, validado em tempo constante (`secrets.compare_digest`) contra *timing attacks*.
4. **Cabeçalhos HTTP de Segurança e CORS**:
   - Middleware nativo injetando `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` e `Referrer-Policy: strict-origin-when-cross-origin`.
   - Origens CORS controladas via variável `CORS_ORIGINS`.
5. **Ocultação de Detalhes Internos em Produção**:
   - Quando `APP_ENV=production`, caminhos absolutos do servidor e mensagens internas de exceção são ocultados nas respostas HTTP e registrados apenas no log interno.

---

## ⚙️ Variáveis de Ambiente (`.env`)

A aplicação funciona imediatamente sem configuração extra em ambiente de desenvolvimento, mas suporta um arquivo `.env` na raiz do projeto (baseado no [`.env.example`](file:///home/thyez/Documentos/softwares/transferencia_equipamentos/.env.example)):

| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `APP_ENV` | `development` | Define o modo de execução (`development` ou `production`) |
| `HOST` | `0.0.0.0` | Endereço de escuta do servidor Granian |
| `PORT` | `8000` | Porta HTTP do servidor Granian |
| `WORKERS` | `1` | Número de processos workers do Granian |
| `RELOAD` | `true` (dev) / `false` (prod) | Ativa/desativa o *hot-reload* automático |
| `CORS_ORIGINS` | `*` | Lista de origens permitidas separadas por vírgula |
| `API_KEY` | *(vazio)* | Se preenchida, exige o header `X-API-Key` nas requisições `POST` |
| `DOCS_ENABLED` | `true` | Habilita ou oculta as rotas `/docs`, `/redoc` e `/openapi.json` |
| `PDF_OUTPUT_DIR` | `./pdf` | Diretório onde os PDFs gerados são armazenados |
| `PUBLIC_IMAGES_DIR` | `./public/images` | Diretório das imagens `cabecalho.png` e `rodape.png` |

---

## 🚀 Como Executar o Projeto

### 1. Pré-requisitos
- **Rust** (`rustc` / `cargo`)
- **Python 3.10+** e gerenciador **`uv`**

### 2. Compilar o Módulo Rust e Sincronizar o Ambiente `uv`

```bash
cd python

# 1. Sincroniza as dependências Python via uv
uv sync

# 2. Compila e instala o módulo Rust (PyO3) no ambiente virtual do uv
uv run maturin develop -m ../rust/Cargo.toml --features python
```

### 3. Iniciar o Servidor da API (FastAPI + Granian)

```bash
cd python
uv run python main.py
```

Ou diretamente via CLI do Granian:

```bash
uv run granian --interface asgi app:app --host 0.0.0.0 --port 8000 --reload
```

Acesse a documentação interativa Swagger em: **`http://localhost:8000/docs`**

---

## 📨 Uso da API (Endpoints e Payload JSON)

### Endpoints Disponíveis
- `POST /api/v1/pdf/gerar`: Compila o Termo de Empréstimo, salva na pasta `pdf/` e retorna metadados do arquivo gerado (`HTTP 201 Created`).
- `POST /api/v1/pdf/download`: Compila o Termo de Empréstimo em memória e retorna diretamente o stream binário `application/pdf` para download (`HTTP 200 OK`).
- `GET /health`: Verifica a integridade do motor Rust e a presença de `cabecalho.png` e `rodape.png`.
- `GET /`: Informações institucionais e catálogo de rotas.

### Exemplo de Requisição (`cURL`)

```bash
curl -X POST "http://localhost:8000/api/v1/pdf/gerar" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "TERMO DE EMPRÉSTIMO E RESPONSABILIDADE DE EQUIPAMENTO",
    "unidade_saida": "Secretaria Municipal de Educação, Cultura, Inclusão, Ciência e Tecnologia (SMECICT)",
    "unidade_destino": "Escola Municipal Orgé Ferreira dos Santos",
    "responsavel_nome": "Thyéz de Oliveira Monteiro",
    "responsavel_matricula": "967703",
    "responsavel_cargo": "Assessor de Planejamento e Gestão de Tecnologia Educacional",
    "equipamentos": [
      {
        "descricao": "Notebook HP 240 G8 Intel Core i5 8GB SSD 256GB",
        "quantidade": "05"
      },
      {
        "descricao": "Projetor Multimídia Epson PowerLite E20",
        "quantidade": "01"
      }
    ],
    "data_retirada": "19/10/2026",
    "data_devolucao": "30/11/2026",
    "assinatura_responsavel_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "assinatura_solicitante_base64": null,
    "nome_arquivo": "termo_emprestimo_001.pdf"
  }'
```

---

## 🧪 Como Executar os Testes

### Testes da API FastAPI (via `uv` + `pytest`):
```bash
cd python
uv run pytest test_api.py -v
```

### Testes Unitários e Geração Direta via Terminal no Módulo Rust:
```bash
cd rust

# Rodar testes unitários do Rust
cargo test

# Gerar um PDF de exemplo diretamente em ../pdf/termo_transferencia_exemplo.pdf
cargo run
```

---

## 🏛️ Créditos e Licença

- **Órgão Proprietário:** Secretaria Municipal de Educação, Cultura, Inclusão, Ciência e Tecnologia (SMECICT) — Prefeitura Municipal de Saquarema / RJ.
- **Natureza do Projeto:** Software de desenvolvimento interno para gestão e controle patrimonial de equipamentos tecnológicos e educacionais.

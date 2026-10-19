# Módulo de Geração de PDF com Rust & Typst

Módulo nativo em Rust para geração de termos de transferência de equipamentos em PDF, utilizando a engine de diagramação tipográfica **Typst** (`typst-as-lib` e `typst-pdf`).

Projetado para alto desempenho, formatação profissional e integração nativa com **Python / FastAPI** via **PyO3** e **Maturin** ou FFI.

---

## 📁 Estrutura de Arquivos

```text
rust/
├── Cargo.toml                  # Configurações do Rust, dependências e feature "python" (PyO3)
├── README.md                   # Esta documentação
├── src/
│   ├── lib.rs                  # Biblioteca central com funções de compilação Typst -> PDF
│   └── main.rs                 # Ponto de entrada CLI para teste direto via terminal
└── templates/
    └── termo.typ               # Template visual profissional em Typst
```

---

## 🚀 Como Executar no Terminal

### 1. Gerar PDF de Exemplo (Executável CLI)

Diretamente da pasta `rust`:
```bash
cargo run
```

Ou da raiz do projeto:
```bash
cargo run --manifest-path rust/Cargo.toml
```

O PDF gerado será salvo automaticamente em `pdf/termo_transferencia_exemplo.pdf`.

Você também pode fornecer um caminho de saída personalizado como argumento:
```bash
cargo run -- ../pdf/meu_termo_customizado.pdf
```

### 2. Executar os Testes Automatizados

```bash
cargo test
```

---

## 🎨 O Template Typst (`templates/termo.typ`)

O template aceita dinamicamente os 5 campos solicitados:

| Campo | Descrição | Exemplo |
| :--- | :--- | :--- |
| `titulo` | Título principal em destaque | `"TERMO DE TRANSFERÊNCIA DE EQUIPAMENTOS"` |
| `cabecalho` | Metadados e dados adicionais | `"Setor Remetente: TI\nProtocolo: TRF-089"` |
| `corpo` | Texto descritivo e lista de bens | `"Declaramos a transferência de 1 Notebook..."` |
| `data` | Data e localidade | `"São Paulo - SP, 14 de Outubro de 2026"` |
| `assinatura` | Dados do signatário | `"Carlos Silva\nEngenheiro de Software"` |

### Características Visuais:
- **Papel A4** com margens padronizadas e numeração de página no rodapé (*Página 1 de 1*).
- **Tipografia refinada** utilizando fontes embutidas (*Libertinus Serif* / *DejaVu Sans Mono*).
- **Caixa de metadados** estilizada com fundo suave e bordas arredondadas para o cabeçalho.
- **Espaço para assinatura** formal com linha divisória e identificação do signatário.
- **Geração 100% nativa em memória**: Não depende de binários externos instalados no sistema operacional.

---

## 🐍 Integração com FastAPI (Python / PyO3)

A biblioteca já está totalmente preparada para ser compilada como uma biblioteca dinâmica compatível com Python (`cdylib`).

### Passo a passo para expor ao FastAPI:

1. **Instalar o Maturin** no ambiente virtual Python:
   ```bash
   pip install maturin
   ```

2. **Compilar e instalar o módulo Python** (executar dentro da pasta `rust/`):
   ```bash
   maturin develop --features python
   ```

3. **Utilizar diretamente no FastAPI**:
   ```python
   from fastapi import FastAPI, HTTPException
   from fastapi.responses import FileResponse, Response
   from pydantic import BaseModel
   import transferencia_pdf

   app = FastAPI()

   class TermoRequest(BaseModel):
       titulo: str
       cabecalho: str
       corpo: str
       data: str
       assinatura: str
       output_path: str = "pdf/termo_gerado.pdf"

   @app.post("/gerar-termo")
   def gerar_termo(dados: TermoRequest):
       try:
           # Gera o PDF salvando no disco
           caminho = transferencia_pdf.gerar_pdf(
               dados.titulo,
               dados.cabecalho,
               dados.corpo,
               dados.data,
               dados.assinatura,
               dados.output_path
           )
           return FileResponse(caminho, media_type="application/pdf", filename="termo.pdf")
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))

   @app.post("/gerar-termo-stream")
   def gerar_termo_stream(dados: TermoRequest):
       # Ou gere os bytes direto em memória sem salvar em disco!
       pdf_bytes = transferencia_pdf.gerar_pdf_bytes(
           dados.titulo,
           dados.cabecalho,
           dados.corpo,
           dados.data,
           dados.assinatura
       )
       return Response(content=bytes(pdf_bytes), media_type="application/pdf")
   ```

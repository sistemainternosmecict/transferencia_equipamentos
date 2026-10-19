# Changelog

Todas as alterações relevantes deste projeto desenvolvido internamente para a **Secretaria Municipal de Educação, Cultura, Inclusão, Ciência e Tecnologia (SMECICT)** da **Prefeitura Municipal de Saquarema — RJ** são documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e este projeto adota o padrão de [Commits Semânticos (Conventional Commits)](https://www.conventionalcommits.org/pt-br/v1.0.0/).

---

## [1.0.0] - 2026-10-19

### Adicionado (`feat`)
- **Módulo Gerador de PDF em Rust (`rust/`)**:
  - Compilação tipográfica 100% nativa em memória utilizando `typst` (`0.15`), `typst-pdf` e `typst-as-lib` (`0.17`), sem dependência de binários externos.
  - Integração FFI de alta performance com Python via `PyO3` (`0.29`) e `Maturin`, expondo as funções `gerar_pdf` e `gerar_pdf_bytes`.
  - Suporte a decodificação e validação de assinaturas enviadas em imagem **Base64** (formatos PNG, JPEG, GIF e SVG, com ou sem cabeçalho Data URI `data:image/...;base64,`).
  - CLI executável (`cargo run`) e suíte de testes unitários (`cargo test`).
- **Template Oficial da Prefeitura Municipal de Saquarema (`rust/templates/termo.typ`)**:
  - Layout completo do **Termo de Empréstimo e Responsabilidade de Equipamento** da SMECICT.
  - Cabeçalho e rodapé institucionais ocupando 100% da largura da folha A4.
  - Campos dinâmicos para Unidade de Saída, Unidade/Setor de Destino, Nome do Responsável, Matrícula e Função/Cargo.
  - Tabela dinâmica `ESPECIFICAÇÃO DO(S) EQUIPAMENTO(S)` com descrição e quantidade dos itens.
  - Áreas de assinatura para Responsável e Solicitante com suporte a sobreposição de imagem em Base64, além de datas de retirada e devolução.
- **Pasta Pública de Imagens com Hot-Swap (`public/images/`)**:
  - Extração e disponibilização de `cabecalho.png` e `rodape.png` com leitura dinâmica do disco a cada requisição, permitindo substituição imediata por arquivos de maior resolução mantendo o mesmo nome, sem necessidade de recompilar ou reiniciar o serviço.
- **API REST FastAPI com Granian e `uv` (`python/`)**:
  - Gerenciamento de dependências e ambiente virtual via **`uv`** (`pyproject.toml` e `uv.lock`).
  - Servidor ASGI **`Granian`** em Rust substituindo `uvicorn`.
  - Rota `POST /api/v1/pdf/gerar` para emissão e armazenamento do PDF na pasta `pdf/`.
  - Rota `POST /api/v1/pdf/download` para geração e download direto via streaming HTTP (`application/pdf`).
  - Rotas `GET /health` e `GET /` para monitoramento de integridade e catálogo institucional.
  - Suíte de testes automatizados com `pytest` (`python/test_api.py`).

### Segurança (`sec`)
- Sanitização rigorosa de nomes de arquivos e verificação de caminho relativo (`is_relative_to`) contra ataques de *Path Traversal*.
- Limites estritos de tamanho nos schemas Pydantic (`extra="forbid"`, `max_length`) e proteção contra exaustão de memória (limite de 5 MB para payloads Base64 e validação de *magic bytes* de imagem no Rust).
- Suporte a autenticação opcional por chave via cabeçalho `X-API-Key` com comparação em tempo constante (`secrets.compare_digest`).
- Middleware de cabeçalhos de segurança HTTP (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`) e configuração de CORS via variável de ambiente.
- Arquivo `.env.example` documentando todas as variáveis de ambiente e `.gitignore` configurado para proteger segredos, artefatos de compilação e documentos gerados.

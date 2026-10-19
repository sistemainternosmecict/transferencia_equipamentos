# API de Empréstimo e Responsabilidade de Equipamentos — Prefeitura de Saquarema

API REST construída com **FastAPI**, servida via **Granian**, gerenciada com **uv** e integrada ao motor nativo de geração de PDF em **Rust** (`Typst` + `PyO3`).

---

## 🖼️ Pasta Pública de Imagens (`public/images/`)

O cabeçalho e o rodapé oficiais da Prefeitura Municipal de Saquarema ficam armazenados em:
- `../public/images/cabecalho.png`
- `../public/images/rodape.png`

> **Substituição Direta (Hot-Swap):** O módulo Rust lê esses dois arquivos diretamente do disco a cada geração de PDF. Para substituir por versões em resolução maior, basta sobrescrever `cabecalho.png` ou `rodape.png` na pasta `public/images/` mantendo o mesmo nome — **não é necessário recompilar o Rust nem reiniciar o servidor**.

---

## 🚀 Como Iniciar a API

```bash
cd /home/thyez/Documentos/softwares/transferencia_equipamentos/python
export PATH="/root/.local/bin:$PATH"

# Compilar/atualizar extensão Rust (se houver mudanças no código Rust)
uv sync --reinstall-package transferencia-pdf

# Iniciar servidor Granian
uv run python main.py
```

Acesse o Swagger UI interativo em: **`http://localhost:8000/docs`**

---

## 📨 Exemplo de Payload JSON (`POST /api/v1/pdf/gerar` ou `/api/v1/pdf/download`)

```json
{
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
  "assinatura_responsavel_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "assinatura_solicitante_base64": null,
  "nome_arquivo": "termo_emprestimo_001.pdf"
}
```

---

## 🧪 Rodar Testes Automatizados

```bash
uv run pytest test_api.py -v
```

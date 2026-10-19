import logging
import os
import re
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

# Configuração de diretórios base
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent


def _carregar_dotenv() -> None:
    """Carrega variáveis de ambiente de arquivos .env (na raiz ou em python/) se existirem."""
    for env_path in (PROJECT_ROOT / ".env", CURRENT_DIR / ".env"):
        if env_path.is_file():
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip().strip("'").strip('"')
                    if key and key not in os.environ:
                        os.environ[key] = val


_carregar_dotenv()

try:
    import transferencia_pdf
except ImportError as err:
    raise RuntimeError(
        "Módulo Rust 'transferencia_pdf' não encontrado. "
        "Certifique-se de compilá-lo com 'uv run maturin develop -m ../rust/Cargo.toml --features python'."
    ) from err

from schemas import GerarPdfResponse, TermoTransferenciaPayload

# Configuração de Logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("smecict.transferencia_api")

# Variáveis de Ambiente e Diretórios
APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV == "production"
DOCS_ENABLED = os.getenv("DOCS_ENABLED", "true").lower() in ("true", "1", "yes")
API_KEY_CONFIGURED = os.getenv("API_KEY", "").strip()

DEFAULT_PDF_DIR = PROJECT_ROOT / "pdf"
PUBLIC_DIR = PROJECT_ROOT / "public"
DEFAULT_PUBLIC_IMAGES_DIR = PUBLIC_DIR / "images"

PDF_DIR = Path(os.getenv("PDF_OUTPUT_DIR", str(DEFAULT_PDF_DIR))).resolve()
PUBLIC_IMAGES_DIR = Path(
    os.getenv("PUBLIC_IMAGES_DIR", str(DEFAULT_PUBLIC_IMAGES_DIR))
).resolve()

PDF_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Propaga PUBLIC_IMAGES_DIR para o módulo Rust
os.environ["PUBLIC_IMAGES_DIR"] = str(PUBLIC_IMAGES_DIR)

# Configuração de CORS segura via variável de ambiente
raw_origins = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]
ALLOW_CREDENTIALS = "*" not in CORS_ORIGINS

app = FastAPI(
    title="API de Empréstimo e Responsabilidade de Equipamentos — SMECICT Saquarema",
    description=(
        "Sistema interno da Secretaria Municipal de Educação, Cultura, Inclusão, Ciência e Tecnologia "
        "(Prefeitura Municipal de Saquarema - RJ) para geração automatizada de Termos de Empréstimo e "
        "Responsabilidade de Equipamentos com motor nativo em Rust (Typst + PyO3)."
    ),
    version="2.0.0",
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


@app.middleware("http")
async def adicionar_security_headers(request: Request, call_next):
    """Adiciona cabeçalhos HTTP de segurança em todas as respostas."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Servir pasta pública de imagens (cabecalho.png e rodape.png)
if PUBLIC_DIR.exists():
    app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")


def verificar_api_key(
    x_api_key: Optional[str] = Header(
        default=None,
        alias="X-API-Key",
        description="Chave de API opcional (exigida apenas quando a variável de ambiente API_KEY estiver configurada)",
    ),
) -> None:
    """Valida a chave de acesso X-API-Key em tempo constante caso API_KEY esteja definida no ambiente."""
    if not API_KEY_CONFIGURED:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, API_KEY_CONFIGURED):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado: chave X-API-Key ausente ou inválida.",
        )


def _sanitizar_caminho_pdf(nome: str | None) -> tuple[str, Path]:
    """Higieniza o nome de arquivo e garante que o caminho final permaneça estritamente dentro de PDF_DIR."""
    if not nome or not nome.strip():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_limpo = f"termo_emprestimo_{timestamp}.pdf"
    else:
        nome_base = os.path.basename(nome.strip())
        nome_limpo = re.sub(r"[^\w\-. ]", "_", nome_base).strip(" .")
        if not nome_limpo:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_limpo = f"termo_emprestimo_{timestamp}.pdf"
        elif not nome_limpo.lower().endswith(".pdf"):
            nome_limpo += ".pdf"

    caminho_completo = (PDF_DIR / nome_limpo).resolve()
    if not caminho_completo.is_relative_to(PDF_DIR):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de arquivo inválido.",
        )
    return nome_limpo, caminho_completo


def _converter_equipamentos(payload: TermoTransferenciaPayload) -> list[tuple[str, str]]:
    """Converte a lista de objetos Pydantic para lista de tuplas (descricao, quantidade) esperada pelo Rust."""
    return [(item.descricao, str(item.quantidade)) for item in payload.equipamentos]


@app.get("/", tags=["Info"])
def root_info():
    """Retorna informações institucionais e catálogo de rotas da API."""
    return {
        "app": "API de Empréstimo e Responsabilidade de Equipamentos — SMECICT Saquarema",
        "orgao": "Secretaria Municipal de Educação, Cultura, Inclusão, Ciência e Tecnologia — Prefeitura de Saquarema",
        "versao": "2.0.0",
        "ambiente": APP_ENV,
        "status": "online",
        "autenticacao_api_key_ativa": bool(API_KEY_CONFIGURED),
        "docs_url": "/docs" if DOCS_ENABLED else None,
        "imagens_publicas": {
            "diretorio_local": str(PUBLIC_IMAGES_DIR) if not IS_PRODUCTION else "public/images",
            "cabecalho_url": "/public/images/cabecalho.png",
            "rodape_url": "/public/images/rodape.png",
        },
        "rotas": [
            "POST /api/v1/pdf/gerar",
            "POST /api/v1/pdf/download",
            "GET /health",
        ],
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint de verificação de integridade da API e disponibilidade dos recursos."""
    return {
        "status": "ok",
        "backend_rust": "transferencia_pdf",
        "cabecalho_presente": (PUBLIC_IMAGES_DIR / "cabecalho.png").exists(),
        "rodape_presente": (PUBLIC_IMAGES_DIR / "rodape.png").exists(),
    }


@app.post(
    "/api/v1/pdf/gerar",
    response_model=GerarPdfResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["PDF"],
    dependencies=[Depends(verificar_api_key)],
    summary="Gerar e salvar PDF no servidor",
    description=(
        "Compila o template Typst da Prefeitura de Saquarema com os dados das unidades, "
        "responsável, tabela de equipamentos e assinatura em Base64, salvando na pasta 'pdf/'."
    ),
)
def gerar_pdf_endpoint(payload: TermoTransferenciaPayload):
    nome_arquivo, caminho_completo = _sanitizar_caminho_pdf(payload.nome_arquivo)
    equipamentos_tuplas = _converter_equipamentos(payload)
    assinatura_resp = payload.resolver_assinatura_responsavel()

    try:
        caminho_gerado = transferencia_pdf.gerar_pdf(
            unidade_saida=payload.unidade_saida,
            unidade_destino=payload.unidade_destino,
            responsavel_nome=payload.responsavel_nome,
            responsavel_matricula=payload.responsavel_matricula,
            responsavel_cargo=payload.responsavel_cargo,
            equipamentos=equipamentos_tuplas,
            output_path=str(caminho_completo),
            titulo=payload.titulo,
            data_retirada=payload.data_retirada,
            data_devolucao=payload.data_devolucao,
            assinatura_responsavel_base64=assinatura_resp,
            assinatura_solicitante_base64=payload.assinatura_solicitante_base64,
        )

        tamanho = os.path.getsize(caminho_gerado)
        caminho_exibicao = (
            f"pdf/{nome_arquivo}" if IS_PRODUCTION else str(caminho_gerado)
        )

        return GerarPdfResponse(
            status="success",
            mensagem="PDF gerado e armazenado com sucesso",
            nome_arquivo=nome_arquivo,
            caminho=caminho_exibicao,
            tamanho_bytes=tamanho,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dados inválidos para geração do PDF: {str(e)}",
        )
    except Exception as e:
        logger.exception("Erro interno ao gerar PDF no módulo Rust")
        detalhe = (
            "Erro interno ao processar a geração do documento PDF."
            if IS_PRODUCTION
            else f"Falha ao gerar PDF no módulo Rust: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detalhe,
        )


@app.post(
    "/api/v1/pdf/download",
    status_code=status.HTTP_200_OK,
    tags=["PDF"],
    dependencies=[Depends(verificar_api_key)],
    summary="Gerar e fazer download direto do PDF",
    description="Retorna os bytes brutos do PDF via streaming HTTP com cabeçalho Content-Disposition para download direto.",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Arquivo PDF gerado dinamicamente com sucesso.",
        }
    },
)
def download_pdf_endpoint(payload: TermoTransferenciaPayload):
    nome_arquivo, _ = _sanitizar_caminho_pdf(payload.nome_arquivo)
    equipamentos_tuplas = _converter_equipamentos(payload)
    assinatura_resp = payload.resolver_assinatura_responsavel()

    try:
        pdf_bytes = transferencia_pdf.gerar_pdf_bytes(
            unidade_saida=payload.unidade_saida,
            unidade_destino=payload.unidade_destino,
            responsavel_nome=payload.responsavel_nome,
            responsavel_matricula=payload.responsavel_matricula,
            responsavel_cargo=payload.responsavel_cargo,
            equipamentos=equipamentos_tuplas,
            titulo=payload.titulo,
            data_retirada=payload.data_retirada,
            data_devolucao=payload.data_devolucao,
            assinatura_responsavel_base64=assinatura_resp,
            assinatura_solicitante_base64=payload.assinatura_solicitante_base64,
        )

        headers = {
            "Content-Disposition": f'attachment; filename="{nome_arquivo}"',
            "Content-Length": str(len(pdf_bytes)),
        }

        return Response(
            content=bytes(pdf_bytes),
            media_type="application/pdf",
            headers=headers,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dados inválidos para geração do PDF: {str(e)}",
        )
    except Exception as e:
        logger.exception("Erro interno ao renderizar bytes do PDF no módulo Rust")
        detalhe = (
            "Erro interno ao processar a geração do documento PDF."
            if IS_PRODUCTION
            else f"Falha ao renderizar bytes do PDF no módulo Rust: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detalhe,
        )

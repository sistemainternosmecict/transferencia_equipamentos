from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_BASE64_LEN = 7 * 1024 * 1024  # ~5 MB decodificado


class EquipamentoItemSchema(BaseModel):
    """Representa um equipamento/material e sua respectiva quantidade."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    descricao: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Descrição ou especificação do equipamento/material",
        examples=["Notebook Dell Latitude 5440 (Patrimônio: PAT-2026-4412)"],
    )
    quantidade: Union[int, str] = Field(
        ...,
        description="Quantidade do item emprestado",
        examples=["02"],
    )

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: Union[int, str]) -> str:
        s = str(v).strip()
        if not s or len(s) > 30:
            raise ValueError("A quantidade deve ter entre 1 e 30 caracteres")
        return s


class TermoTransferenciaPayload(BaseModel):
    """Payload de entrada para geração do Termo de Empréstimo e Responsabilidade de Equipamento (Prefeitura de Saquarema)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    titulo: str = Field(
        default="TERMO DE EMPRÉSTIMO E RESPONSABILIDADE DE EQUIPAMENTO",
        min_length=1,
        max_length=200,
        description="Título principal do documento",
        examples=["TERMO DE EMPRÉSTIMO E RESPONSABILIDADE DE EQUIPAMENTO"],
    )
    unidade_saida: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Unidade de Saída que está emprestando os equipamentos",
        examples=[
            "Secretaria Municipal de Educação, Cultura, Inclusão, Ciência e Tecnologia (SMECICT)"
        ],
    )
    unidade_destino: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Unidade ou Setor de Destino que está recebendo os equipamentos",
        examples=["Escola Municipal Orgé Ferreira dos Santos"],
    )
    responsavel_nome: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nome completo do responsável pelos equipamentos na unidade de saída",
        examples=["Thyéz de Oliveira Monteiro"],
    )
    responsavel_matricula: str = Field(
        ...,
        min_length=1,
        max_length=60,
        description="Número da matrícula do responsável",
        examples=["967703"],
    )
    responsavel_cargo: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Função ou cargo exercido pelo responsável",
        examples=["Assessor de Planejamento e Gestão de Tecnologia Educacional"],
    )
    equipamentos: list[EquipamentoItemSchema] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Lista de equipamentos e quantidades a serem discriminados na tabela (máx. 100 itens)",
        examples=[
            [
                {
                    "descricao": "Notebook HP 240 G8 i5 8GB SSD 256GB",
                    "quantidade": "05",
                },
                {
                    "descricao": "Projetor Multimídia Epson PowerLite E20",
                    "quantidade": "01",
                },
            ]
        ],
    )
    data_retirada: str = Field(
        default="___/___/___",
        max_length=50,
        description="Data da movimentação/retirada dos equipamentos",
        examples=["19/10/2026"],
    )
    data_devolucao: str = Field(
        default="___/___/___",
        max_length=50,
        description="Data prevista para devolução/entrega dos equipamentos",
        examples=["30/11/2026"],
    )
    assinatura_responsavel_base64: Optional[str] = Field(
        default=None,
        max_length=MAX_BASE64_LEN,
        description="Imagem da assinatura do responsável codificada em Base64 (PNG, JPEG, GIF ou SVG, máx. 5MB)",
        examples=[
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        ],
    )
    assinatura_solicitante_base64: Optional[str] = Field(
        default=None,
        max_length=MAX_BASE64_LEN,
        description="Imagem da assinatura do solicitante codificada em Base64 (opcional, máx. 5MB)",
        examples=[None],
    )
    assinatura_base64: Optional[str] = Field(
        default=None,
        max_length=MAX_BASE64_LEN,
        description="Atalho opcional para enviar uma única assinatura em Base64 (caso assinatura_responsavel_base64 não seja informada)",
        examples=[None],
    )
    nome_arquivo: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Nome opcional para o arquivo PDF gerado (se não informado, será gerado automaticamente)",
        examples=["termo_emprestimo_saquarema_001.pdf"],
    )

    def resolver_assinatura_responsavel(self) -> Optional[str]:
        """Retorna a assinatura do responsável ou o alias assinatura_base64 se preenchido."""
        if self.assinatura_responsavel_base64 and self.assinatura_responsavel_base64.strip():
            return self.assinatura_responsavel_base64.strip()
        if self.assinatura_base64 and self.assinatura_base64.strip():
            return self.assinatura_base64.strip()
        return None


class GerarPdfResponse(BaseModel):
    """Resposta com detalhes do PDF gerado e salvo em disco."""

    status: str = Field(default="success", description="Status da operação")
    mensagem: str = Field(
        default="PDF gerado com sucesso", description="Mensagem descritiva"
    )
    nome_arquivo: str = Field(..., description="Nome do arquivo salvo")
    caminho: str = Field(..., description="Caminho relativo/absoluto do arquivo PDF")
    tamanho_bytes: int = Field(
        ..., description="Tamanho do arquivo PDF gerado em bytes"
    )

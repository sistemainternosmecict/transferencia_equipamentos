import os
import pytest
from fastapi.testclient import TestClient

from app import app, PDF_DIR

client = TestClient(app)

SAMPLE_SIGNATURE_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAUAAAABaCAYAAADJqo/jAAAE50lEQVR4nO3dzXXbMBBFYTgnBWiTDlROelEt7iXluANv3IGzyOEJTRMiQfzNzLvfJhtHBCnyCqBk+eXz8zMBgKIfswcAALMQQACyCCAAWQQQgCwCCEAWAQQgiwACkEUAAcgigABkEUAAsgggAFkEEIAsAghAFgEEIIsAApBFAAHIIoAAZBFAALLCBvB2f7zPHgMA214i/k2Qbfw+3l5/zRoLALvCzgAB4Ei4AO4tfVkOA9gTKoCEDkCJUAHcWt/7I46alued5x97wgSQNz6wtY0fEcRWiAByYmPtdn+8584JzhWshQjg1nr2xzJYC88xSrgPIEtfLPbi9/H2+mt7ThBJLFwH8OyJHG0WyD2t73LxK/l56HEdwC2F2R839r/K3e/bngt754b6sYPjACoufbmx/1Vuv3PngsI5gjIuA3jlgve+DD4as8d9qnH2ft/ezxw9DnS4DOCW4iu76pLu7JK39DHrRgWv3AWwZunrdRaY22e1CJYueXPUjhvyXAVQ8SQ9Cr7KxXx1yZujuGrAd64CuBX9JL7yMZ/S/+tB6yVv7jEiHTOc4yaArd719bIMLr3oI0awx/2+M9vs9diwx0UA1U7Kqxd9pAi2ut93JNIxQzkXAdyqvQgszwJrZzwRLujW9/uORL+VgjzzAVT6wHOr5Z7XCM5Y8ua24eF4oZ7pAKqfhDUXvrcIjlrylrB8vHpR22fTfxWu9+xv/fizZ5a99nXWjKqEpTFaGssoNZ828M5sAEcsfa0EcGToe23jKotjU7jt0nKm5/n4mAzgyItidgRH7au10Fhc8q5FjOCz6B3tX2kwvRwvFwEc9bmv0U+ahc+4WYn+rLHkWDlWtWqiV/v4vbbZkrkAjn7lnRXAWRfY7At79vZLeBrr4ihIo8bvJYymAmghCkRo3DZHbLeWh6Vw71leK7VfY9eD6QDOeLWaEQIry9AR91lHbK81ixH0Er0zZu6LmQDOPslGRXD2fj4bS0pa70CfZWUfIkXvjNv98S4RQAsn2IgAWorfouext/C8tmLh9syM7Uf3c/YA9kR8Yi3GL6V/49iOrfaV1/uSd8/eceqF6I0zfQZoKQy9ZoEeZkKtxhgxfmsjf2On9Tbw3dQZoMLvHXqIX0ptZoJe9rWlmtky0Ztv6gzQ0uxv0XIW6DEIV8Ycfda3dfV5tfIZPfw3bQZoMX4teYxfSuUzQbX4pVR2P5BZnm1TZoCW49BiBmh5/846sw8R9rNG7kWc6PlhIoDWToraCFrfv7OeBU49filpf41UFMMD6CEONQH0sH8luMifU7wFEMnQAHqaNVyJYLT4Lbh5/9xyfNSPg0dTPwYT6YSJ/JGe3E3/SM9fDY6DX8P+JkjU2VFKvma2Vy37s/0X8GxIAD3OjtYX+LPxK8RvQfzwzO3++DN7DKWmLIGjXEBK8UMMHiPVU/c3QbwvfXNvhhA/9NA7UB9vr797Pr433WeAI79FYybip4NIxTFkCbxEMEokvM9qoyNQOGv612F5wK82tUekYIHJL0TFfAQKCpgBnmTxTQ8iBdRhBnjRye9/I1CAYfIzQCIF6DI/AyRQAHoxH8CUiBSAPuSXwAB0Dfs2GACwhgACkEUAAcgigABkEUAAsgggAFkEEIAsAghAFgEEIIsAApBFAAHIIoAAZBFAALIIIABZBBCArL85OtzX371tSgAAAABJRU5ErkJggg=="
)


def test_root_info_and_security_headers():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    data = response.json()
    assert data["status"] == "online"
    assert "Secretaria Municipal de Educação" in data["orgao"]
    assert "imagens_publicas" in data
    assert any("/api/v1/pdf/gerar" in r for r in data["rotas"])


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["backend_rust"] == "transferencia_pdf"
    assert data["cabecalho_presente"] is True
    assert data["rodape_presente"] is True


def test_gerar_pdf_endpoint():
    test_filename = "test_termo_saquarema_api.pdf"
    file_path = PDF_DIR / test_filename
    if file_path.exists():
        file_path.unlink()

    payload = {
        "titulo": "TERMO DE EMPRÉSTIMO E RESPONSABILIDADE DE EQUIPAMENTO",
        "unidade_saida": "Secretaria Municipal de Educação, Cultura, Inclusão, Ciência e Tecnologia (SMECICT)",
        "unidade_destino": "Escola Municipal Orgé Ferreira dos Santos",
        "responsavel_nome": "Thyéz de Oliveira Monteiro",
        "responsavel_matricula": "967703",
        "responsavel_cargo": "Assessor de Planejamento e Gestão de Tecnologia Educacional",
        "equipamentos": [
            {
                "descricao": "Notebook HP 240 G8 Intel Core i5 8GB SSD 256GB",
                "quantidade": "05",
            },
            {
                "descricao": "Projetor Multimídia Epson PowerLite E20",
                "quantidade": 1,
            },
            {
                "descricao": "Caixa de Som Amplificada 300W com Microfone",
                "quantidade": "02",
            },
        ],
        "data_retirada": "19/10/2026",
        "data_devolucao": "30/11/2026",
        "assinatura_responsavel_base64": f"data:image/png;base64,{SAMPLE_SIGNATURE_B64}",
        "nome_arquivo": test_filename,
    }

    response = client.post("/api/v1/pdf/gerar", json=payload)
    assert response.status_code == 201, f"Erro: {response.text}"

    data = response.json()
    assert data["status"] == "success"
    assert data["nome_arquivo"] == test_filename
    assert data["tamanho_bytes"] > 10000
    assert os.path.exists(data["caminho"])

    with open(data["caminho"], "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-", "O arquivo salvo deve ser um PDF válido"


def test_download_pdf_endpoint():
    payload = {
        "unidade_saida": "SMECICT - Departamento de Tecnologia Educacional",
        "unidade_destino": "Creche Municipal Tia Merice",
        "responsavel_nome": "Carlos Eduardo Pereira",
        "responsavel_matricula": "77489-A",
        "responsavel_cargo": "Coordenador Técnico",
        "equipamentos": [
            {"descricao": "Impressora Multifuncional EcoTank L3250", "quantidade": "01"}
        ],
        "data_retirada": "19/10/2026",
        "data_devolucao": "15/12/2026",
        "assinatura_base64": SAMPLE_SIGNATURE_B64,
        "nome_arquivo": "comprovante_download_saquarema.pdf",
    }

    response = client.post("/api/v1/pdf/download", json=payload)
    assert response.status_code == 200, f"Erro: {response.text}"
    assert response.headers["content-type"] == "application/pdf"
    assert 'attachment; filename="comprovante_download_saquarema.pdf"' in response.headers["content-disposition"]
    assert len(response.content) > 10000
    assert response.content.startswith(b"%PDF-")


def test_protecao_path_traversal_nome_arquivo():
    payload = {
        "unidade_saida": "SMECICT",
        "unidade_destino": "Escola Destino",
        "responsavel_nome": "João Silva",
        "responsavel_matricula": "12345",
        "responsavel_cargo": "Analista",
        "equipamentos": [{"descricao": "Notebook", "quantidade": "1"}],
        "nome_arquivo": "../../../etc/malicioso.pdf",
    }

    response = client.post("/api/v1/pdf/gerar", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["nome_arquivo"] == "malicioso.pdf"
    assert str(PDF_DIR) in data["caminho"]
    if os.path.exists(data["caminho"]):
        os.remove(data["caminho"])


def test_validacao_base64_invalido():
    payload = {
        "unidade_saida": "SMECICT",
        "unidade_destino": "Escola Destino",
        "responsavel_nome": "João Silva",
        "responsavel_matricula": "12345",
        "responsavel_cargo": "Analista",
        "equipamentos": [{"descricao": "Notebook", "quantidade": "1"}],
        "assinatura_responsavel_base64": "base64_invalido_nao_eh_imagem_###",
    }

    response = client.post("/api/v1/pdf/gerar", json=payload)
    assert response.status_code == 400


def test_rejeicao_campos_extras_nao_permitidos():
    payload = {
        "unidade_saida": "SMECICT",
        "unidade_destino": "Escola Destino",
        "responsavel_nome": "João Silva",
        "responsavel_matricula": "12345",
        "responsavel_cargo": "Analista",
        "equipamentos": [{"descricao": "Notebook", "quantidade": "1"}],
        "campo_injetado_malicioso": "valor",
    }

    response = client.post("/api/v1/pdf/gerar", json=payload)
    assert response.status_code == 422


def test_validacao_payload_invalido():
    payload_invalido = {
        "titulo": "Apenas Titulo",
    }

    response = client.post("/api/v1/pdf/gerar", json=payload_invalido)
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main(["-v", __file__])

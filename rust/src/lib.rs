use std::env;
use std::fs;
use std::path::{Path, PathBuf};

use base64::engine::general_purpose::{STANDARD, STANDARD_NO_PAD};
use base64::Engine;
use serde::{Deserialize, Serialize};
use typst::foundations::{Dict, IntoValue};
use typst_as_lib::typst_kit_options::TypstKitFontOptions;
use typst_as_lib::TypstEngine;
use typst_layout::PagedDocument;
use typst_pdf::{pdf, PdfOptions};

/// Template Typst padrão embutido na compilação.
pub const DEFAULT_TEMPLATE: &str = include_str!("../templates/termo.typ");

/// Título oficial padrão do modelo da Prefeitura de Saquarema.
pub const DEFAULT_TITULO: &str = "TERMO DE EMPRÉSTIMO E RESPONSABILIDADE DE EQUIPAMENTO";

/// Representa um item na tabela de especificação de equipamentos.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct EquipamentoItem {
    /// Nome ou descrição detalhada do equipamento/material.
    pub descricao: String,
    /// Quantidade emprestada (ex: "1", "02", "5 un").
    pub quantidade: String,
}

impl EquipamentoItem {
    pub fn new(descricao: impl Into<String>, quantidade: impl Into<String>) -> Self {
        Self {
            descricao: descricao.into(),
            quantidade: quantidade.into(),
        }
    }
}

/// Estrutura completa de dados para o Termo de Empréstimo e Responsabilidade de Equipamento.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct DocumentData {
    /// Título do documento
    pub titulo: String,
    /// Unidade que está emprestando o equipamento
    pub unidade_saida: String,
    /// Unidade ou setor destinatário
    pub unidade_destino: String,
    /// Nome completo do responsável pelos equipamentos na unidade de saída
    pub responsavel_nome: String,
    /// Matrícula do responsável
    pub responsavel_matricula: String,
    /// Função ou cargo do responsável
    pub responsavel_cargo: String,
    /// Lista de equipamentos e respectivas quantidades
    pub equipamentos: Vec<EquipamentoItem>,
    /// Data da retirada dos equipamentos (ex: "19/10/2026")
    pub data_retirada: String,
    /// Data prevista para devolução dos equipamentos (ex: "30/10/2026")
    pub data_devolucao: String,
    /// Assinatura do responsável codificada em Base64 (opcional)
    pub assinatura_responsavel_base64: Option<String>,
    /// Assinatura do solicitante codificada em Base64 (opcional)
    pub assinatura_solicitante_base64: Option<String>,
}

impl Default for DocumentData {
    fn default() -> Self {
        Self {
            titulo: DEFAULT_TITULO.to_string(),
            unidade_saida: String::new(),
            unidade_destino: String::new(),
            responsavel_nome: String::new(),
            responsavel_matricula: String::new(),
            responsavel_cargo: String::new(),
            equipamentos: Vec::new(),
            data_retirada: "___/___/___".to_string(),
            data_devolucao: "___/___/___".to_string(),
            assinatura_responsavel_base64: None,
            assinatura_solicitante_base64: None,
        }
    }
}

/// Localiza a pasta pública de imagens (`public/images/`), permitindo que o usuário
/// substitua `cabecalho.png` e `rodape.png` por versões de maior resolução sem recompilar.
pub fn resolve_public_images_dir() -> PathBuf {
    if let Ok(custom_dir) = env::var("PUBLIC_IMAGES_DIR") {
        let p = PathBuf::from(custom_dir);
        if p.exists() {
            return p;
        }
    }

    let candidates = [
        PathBuf::from("public/images"),
        PathBuf::from("../public/images"),
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../public/images"),
    ];

    for candidate in candidates {
        if candidate.exists() {
            return candidate;
        }
    }

    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../public/images")
}

/// Limite máximo para string Base64 de assinatura (~5 MB decodificado) para prevenção de DoS.
pub const MAX_BASE64_SIGNATURE_LEN: usize = 7 * 1024 * 1024;

/// Decodifica uma string Base64 (com ou sem prefixo Data URI `data:image/...;base64,`)
/// e retorna os bytes da imagem junto com a extensão apropriada (`.png`, `.jpg`, `.gif`, `.svg`).
pub fn decode_base64_image(input: &str) -> Result<(Vec<u8>, &'static str), String> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err("String Base64 vazia".to_string());
    }
    if trimmed.len() > MAX_BASE64_SIGNATURE_LEN {
        return Err("A imagem Base64 excede o tamanho máximo permitido (5 MB)".to_string());
    }

    // Remove o cabeçalho Data URI se existir (ex: "data:image/png;base64,iVBOR...")
    let b64_payload = match trimmed.split_once(',') {
        Some((prefix, data)) if prefix.contains("base64") => data.trim(),
        _ => trimmed,
    };

    // Remove quebras de linha ou espaços em branco internos do base64
    let cleaned: String = b64_payload.chars().filter(|c| !c.is_whitespace()).collect();

    let bytes = STANDARD
        .decode(&cleaned)
        .or_else(|_| STANDARD_NO_PAD.decode(&cleaned))
        .map_err(|e| format!("Imagem Base64 inválida: {}", e))?;

    if bytes.len() < 4 {
        return Err("Conteúdo binário da imagem Base64 é muito curto ou inválido".to_string());
    }

    // Identifica a extensão pelos magic bytes para que o Typst escolha o decodificador correto
    let ext = if bytes.starts_with(b"\x89PNG\r\n\x1a\n") {
        "png"
    } else if bytes.starts_with(b"\xff\xd8\xff") {
        "jpg"
    } else if bytes.starts_with(b"GIF87a") || bytes.starts_with(b"GIF89a") {
        "gif"
    } else if bytes.starts_with(b"<svg") || bytes.starts_with(b"<?xml") {
        "svg"
    } else {
        return Err(
            "Formato de imagem não suportado no Base64 (envie PNG, JPEG, GIF ou SVG)".to_string(),
        );
    };

    Ok((bytes, ext))
}

/// Gera os bytes brutos do PDF utilizando o template padrão da Prefeitura de Saquarema.
pub fn generate_pdf_bytes(data: &DocumentData) -> Result<Vec<u8>, String> {
    generate_pdf_bytes_with_template(data, DEFAULT_TEMPLATE)
}

/// Gera os bytes brutos do PDF com suporte às imagens dinâmicas da pasta `public/images/`
/// e às assinaturas em Base64.
pub fn generate_pdf_bytes_with_template(
    data: &DocumentData,
    template_typst: &str,
) -> Result<Vec<u8>, String> {
    let images_dir = resolve_public_images_dir();
    let cabecalho_path = images_dir.join("cabecalho.png");
    let rodape_path = images_dir.join("rodape.png");

    let mut binary_files: Vec<(String, Vec<u8>)> = Vec::new();
    let mut inputs = Dict::new();

    // 1. Lê dinamicamente o cabeçalho e rodapé da pasta pública (hot-swap sem recompilar)
    if let Ok(bytes) = fs::read(&cabecalho_path) {
        binary_files.push(("cabecalho.png".to_string(), bytes));
        inputs.insert("tem_cabecalho_img".into(), "true".into_value());
    } else {
        inputs.insert("tem_cabecalho_img".into(), "false".into_value());
    }

    if let Ok(bytes) = fs::read(&rodape_path) {
        binary_files.push(("rodape.png".to_string(), bytes));
        inputs.insert("tem_rodape_img".into(), "true".into_value());
    } else {
        inputs.insert("tem_rodape_img".into(), "false".into_value());
    }

    // 2. Decodifica a assinatura do responsável (se fornecida em Base64)
    if let Some(ref b64) = data.assinatura_responsavel_base64 {
        if !b64.trim().is_empty() {
            let (img_bytes, ext) = decode_base64_image(b64)?;
            let filename = format!("assinatura_responsavel.{}", ext);
            binary_files.push((filename.clone(), img_bytes));
            inputs.insert("tem_assinatura_responsavel".into(), "true".into_value());
            inputs.insert("assinatura_responsavel_arquivo".into(), filename.into_value());
        } else {
            inputs.insert("tem_assinatura_responsavel".into(), "false".into_value());
        }
    } else {
        inputs.insert("tem_assinatura_responsavel".into(), "false".into_value());
    }

    // 3. Decodifica a assinatura do solicitante (se fornecida em Base64)
    if let Some(ref b64) = data.assinatura_solicitante_base64 {
        if !b64.trim().is_empty() {
            let (img_bytes, ext) = decode_base64_image(b64)?;
            let filename = format!("assinatura_solicitante.{}", ext);
            binary_files.push((filename.clone(), img_bytes));
            inputs.insert("tem_assinatura_solicitante".into(), "true".into_value());
            inputs.insert("assinatura_solicitante_arquivo".into(), filename.into_value());
        } else {
            inputs.insert("tem_assinatura_solicitante".into(), "false".into_value());
        }
    } else {
        inputs.insert("tem_assinatura_solicitante".into(), "false".into_value());
    }

    // 4. Serializa a lista de equipamentos para o template Typst ("descricao\tquantidade\n...")
    let equipamentos_raw = data
        .equipamentos
        .iter()
        .map(|item| {
            let desc_clean = item.descricao.replace(['\t', '\n', '\r'], " ");
            let qtd_clean = item.quantidade.replace(['\t', '\n', '\r'], " ");
            format!("{}\t{}", desc_clean, qtd_clean)
        })
        .collect::<Vec<_>>()
        .join("\n");

    // 5. Insere os campos textuais no dicionário `sys.inputs`
    let titulo = if data.titulo.trim().is_empty() {
        DEFAULT_TITULO.to_string()
    } else {
        data.titulo.clone()
    };

    inputs.insert("titulo".into(), titulo.into_value());
    inputs.insert("unidade_saida".into(), data.unidade_saida.clone().into_value());
    inputs.insert("unidade_destino".into(), data.unidade_destino.clone().into_value());
    inputs.insert("responsavel_nome".into(), data.responsavel_nome.clone().into_value());
    inputs.insert(
        "responsavel_matricula".into(),
        data.responsavel_matricula.clone().into_value(),
    );
    inputs.insert("responsavel_cargo".into(), data.responsavel_cargo.clone().into_value());
    inputs.insert("equipamentos_raw".into(), equipamentos_raw.into_value());
    inputs.insert("data_retirada".into(), data.data_retirada.clone().into_value());
    inputs.insert("data_devolucao".into(), data.data_devolucao.clone().into_value());

    // 6. Inicializa a engine Typst com os arquivos binários resolvidos em memória
    let static_files: Vec<(&str, &[u8])> = binary_files
        .iter()
        .map(|(name, bytes)| (name.as_str(), bytes.as_slice()))
        .collect();

    let engine = TypstEngine::builder()
        .main_file(template_typst)
        .search_fonts_with(TypstKitFontOptions::default())
        .with_static_file_resolver(static_files)
        .build();

    // 7. Compila o documento e renderiza o PDF
    let warned = engine.compile_with_input::<_, PagedDocument>(inputs);
    let doc = warned
        .output
        .map_err(|e| format!("Erro na compilação do documento Typst: {:?}", e))?;

    let options = PdfOptions::default();
    let pdf_bytes = pdf(&doc, &options)
        .map_err(|e| format!("Erro na renderização dos bytes PDF: {:?}", e))?;

    Ok(pdf_bytes)
}

/// Gera o PDF e grava no caminho especificado, criando diretórios pai automaticamente.
pub fn generate_pdf(data: &DocumentData, output_path: impl AsRef<Path>) -> Result<PathBuf, String> {
    let path = output_path.as_ref();

    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() && !parent.exists() {
            fs::create_dir_all(parent)
                .map_err(|e| format!("Falha ao criar diretório {:?}: {}", parent, e))?;
        }
    }

    let bytes = generate_pdf_bytes(data)?;

    fs::write(path, bytes)
        .map_err(|e| format!("Falha ao escrever arquivo PDF em {:?}: {}", path, e))?;

    Ok(path.to_path_buf())
}

// ============================================================================
// Módulo de integração com PyO3 (usado pela API FastAPI)
// ============================================================================
#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(
    name = "gerar_pdf",
    signature = (
        unidade_saida,
        unidade_destino,
        responsavel_nome,
        responsavel_matricula,
        responsavel_cargo,
        equipamentos,
        output_path,
        titulo = "TERMO DE EMPRÉSTIMO E RESPONSABILIDADE DE EQUIPAMENTO",
        data_retirada = "___/___/___",
        data_devolucao = "___/___/___",
        assinatura_responsavel_base64 = None,
        assinatura_solicitante_base64 = None,
    )
)]
#[allow(clippy::too_many_arguments)]
fn py_gerar_pdf(
    unidade_saida: &str,
    unidade_destino: &str,
    responsavel_nome: &str,
    responsavel_matricula: &str,
    responsavel_cargo: &str,
    equipamentos: Vec<(String, String)>,
    output_path: &str,
    titulo: &str,
    data_retirada: &str,
    data_devolucao: &str,
    assinatura_responsavel_base64: Option<String>,
    assinatura_solicitante_base64: Option<String>,
) -> PyResult<String> {
    let itens = equipamentos
        .into_iter()
        .map(|(desc, qtd)| EquipamentoItem::new(desc, qtd))
        .collect();

    let doc_data = DocumentData {
        titulo: titulo.to_string(),
        unidade_saida: unidade_saida.to_string(),
        unidade_destino: unidade_destino.to_string(),
        responsavel_nome: responsavel_nome.to_string(),
        responsavel_matricula: responsavel_matricula.to_string(),
        responsavel_cargo: responsavel_cargo.to_string(),
        equipamentos: itens,
        data_retirada: data_retirada.to_string(),
        data_devolucao: data_devolucao.to_string(),
        assinatura_responsavel_base64,
        assinatura_solicitante_base64,
    };

    let path = generate_pdf(&doc_data, output_path)
        .map_err(pyo3::exceptions::PyValueError::new_err)?;
    Ok(path.to_string_lossy().to_string())
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(
    name = "gerar_pdf_bytes",
    signature = (
        unidade_saida,
        unidade_destino,
        responsavel_nome,
        responsavel_matricula,
        responsavel_cargo,
        equipamentos,
        titulo = "TERMO DE EMPRÉSTIMO E RESPONSABILIDADE DE EQUIPAMENTO",
        data_retirada = "___/___/___",
        data_devolucao = "___/___/___",
        assinatura_responsavel_base64 = None,
        assinatura_solicitante_base64 = None,
    )
)]
#[allow(clippy::too_many_arguments)]
fn py_gerar_pdf_bytes(
    unidade_saida: &str,
    unidade_destino: &str,
    responsavel_nome: &str,
    responsavel_matricula: &str,
    responsavel_cargo: &str,
    equipamentos: Vec<(String, String)>,
    titulo: &str,
    data_retirada: &str,
    data_devolucao: &str,
    assinatura_responsavel_base64: Option<String>,
    assinatura_solicitante_base64: Option<String>,
) -> PyResult<Vec<u8>> {
    let itens = equipamentos
        .into_iter()
        .map(|(desc, qtd)| EquipamentoItem::new(desc, qtd))
        .collect();

    let doc_data = DocumentData {
        titulo: titulo.to_string(),
        unidade_saida: unidade_saida.to_string(),
        unidade_destino: unidade_destino.to_string(),
        responsavel_nome: responsavel_nome.to_string(),
        responsavel_matricula: responsavel_matricula.to_string(),
        responsavel_cargo: responsavel_cargo.to_string(),
        equipamentos: itens,
        data_retirada: data_retirada.to_string(),
        data_devolucao: data_devolucao.to_string(),
        assinatura_responsavel_base64,
        assinatura_solicitante_base64,
    };

    generate_pdf_bytes(&doc_data).map_err(pyo3::exceptions::PyValueError::new_err)
}

#[cfg(feature = "python")]
#[pymodule]
fn transferencia_pdf(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(py_gerar_pdf, m)?)?;
    m.add_function(wrap_pyfunction!(py_gerar_pdf_bytes, m)?)?;
    Ok(())
}

// ============================================================================
// Testes unitários
// ============================================================================
#[cfg(test)]
mod tests {
    use super::*;

    // Pequeno PNG transparente 1x1 válido em Base64 para testes
    const SAMPLE_PNG_B64: &str = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";

    #[test]
    fn test_decode_base64_image_raw_and_data_uri() {
        let (bytes1, ext1) = decode_base64_image(SAMPLE_PNG_B64).expect("Deve decodificar raw b64");
        assert_eq!(ext1, "png");
        assert!(bytes1.starts_with(b"\x89PNG"));

        let data_uri = format!("data:image/png;base64,{}", SAMPLE_PNG_B64);
        let (bytes2, ext2) = decode_base64_image(&data_uri).expect("Deve decodificar Data URI");
        assert_eq!(ext2, "png");
        assert_eq!(bytes1, bytes2);
    }

    #[test]
    fn test_generate_pdf_bytes_with_saquarema_model() {
        let data = DocumentData {
            titulo: DEFAULT_TITULO.to_string(),
            unidade_saida: "Secretaria Municipal de Educação - Departamento de TI".to_string(),
            unidade_destino: "E. M. Orgé Ferreira dos Santos".to_string(),
            responsavel_nome: "Carlos Eduardo Silveira".to_string(),
            responsavel_matricula: "48921-2".to_string(),
            responsavel_cargo: "Coordenador de Tecnologia Educacional".to_string(),
            equipamentos: vec![
                EquipamentoItem::new("Notebook Dell Latitude 5440 - Patrimônio 10452", "02"),
                EquipamentoItem::new("Projetor Multimídia Epson PowerLite E20", "01"),
            ],
            data_retirada: "19/10/2026".to_string(),
            data_devolucao: "30/11/2026".to_string(),
            assinatura_responsavel_base64: Some(SAMPLE_PNG_B64.to_string()),
            assinatura_solicitante_base64: None,
        };

        let bytes = generate_pdf_bytes(&data).expect("Erro ao gerar bytes PDF");
        assert!(!bytes.is_empty());
        assert_eq!(&bytes[0..4], b"%PDF");
    }

    #[test]
    fn test_generate_pdf_saves_to_disk() {
        let temp_file = std::env::temp_dir().join("termo_saquarema_test.pdf");
        if temp_file.exists() {
            let _ = fs::remove_file(&temp_file);
        }

        let data = DocumentData {
            unidade_saida: "SMECICT - Almoxarifado Central".to_string(),
            unidade_destino: "Subsecretaria de Ciência e Tecnologia".to_string(),
            responsavel_nome: "Maria Fernanda Costa".to_string(),
            responsavel_matricula: "99201".to_string(),
            responsavel_cargo: "Diretora de Patrimônio".to_string(),
            equipamentos: vec![EquipamentoItem::new("Monitor LG 24\" IPS Full HD", "04")],
            data_retirada: "19/10/2026".to_string(),
            data_devolucao: "19/12/2026".to_string(),
            assinatura_responsavel_base64: Some(format!("data:image/png;base64,{}", SAMPLE_PNG_B64)),
            ..Default::default()
        };

        let res = generate_pdf(&data, &temp_file);
        assert!(res.is_ok());
        assert!(temp_file.exists());
        let _ = fs::remove_file(&temp_file);
    }
}

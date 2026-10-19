use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use transferencia_pdf::{generate_pdf, DocumentData, EquipamentoItem, DEFAULT_TITULO};

/// Assinatura de exemplo em PNG transparente codificada em Base64
const ASSINATURA_EXEMPLO_B64: &str = "iVBORw0KGgoAAAANSUhEUgAAAUAAAABaCAYAAADJqo/jAAAE50lEQVR4nO3dzXXbMBBFYTgnBWiTDlROelEt7iXluANv3IGzyOEJTRMiQfzNzLvfJhtHBCnyCqBk+eXz8zMBgKIfswcAALMQQACyCCAAWQQQgCwCCEAWAQQgiwACkEUAAcgigABkEUAAsgggAFkEEIAsAghAFgEEIIsAApBFAAHIIoAAZBFAALLCBvB2f7zPHgMA214i/k2Qbfw+3l5/zRoLALvCzgAB4Ei4AO4tfVkOA9gTKoCEDkCJUAHcWt/7I46alued5x97wgSQNz6wtY0fEcRWiAByYmPtdn+8584JzhWshQjg1nr2xzJYC88xSrgPIEtfLPbi9/H2+mt7ThBJLFwH8OyJHG0WyD2t73LxK/l56HEdwC2F2R839r/K3e/bngt754b6sYPjACoufbmx/1Vuv3PngsI5gjIuA3jlgve+DD4as8d9qnH2ft/ezxw9DnS4DOCW4iu76pLu7JK39DHrRgWv3AWwZunrdRaY22e1CJYueXPUjhvyXAVQ8SQ9Cr7KxXx1yZujuGrAd64CuBX9JL7yMZ/S/+tB6yVv7jEiHTOc4yaArd719bIMLr3oI0awx/2+M9vs9diwx0UA1U7Kqxd9pAi2ut93JNIxQzkXAdyqvQgszwJrZzwRLujW9/uORL+VgjzzAVT6wHOr5Z7XCM5Y8ua24eF4oZ7pAKqfhDUXvrcIjlrylrB8vHpR22fTfxWu9+xv/fizZ5a99nXWjKqEpTFaGssoNZ828M5sAEcsfa0EcGToe23jKotjU7jt0nKm5/n4mAzgyItidgRH7au10Fhc8q5FjOCz6B3tX2kwvRwvFwEc9bmv0U+ahc+4WYn+rLHkWDlWtWqiV/v4vbbZkrkAjn7lnRXAWRfY7At79vZLeBrr4ihIo8bvJYymAmghCkRo3DZHbLeWh6Vw71leK7VfY9eD6QDOeLWaEQIry9AR91lHbK81ixH0Er0zZu6LmQDOPslGRXD2fj4bS0pa70CfZWUfIkXvjNv98S4RQAsn2IgAWorfouext/C8tmLh9syM7Uf3c/YA9kR8Yi3GL6V/49iOrfaV1/uSd8/eceqF6I0zfQZoKQy9ZoEeZkKtxhgxfmsjf2On9Tbw3dQZoMLvHXqIX0ptZoJe9rWlmtky0Ztv6gzQ0uxv0XIW6DEIV8Ycfda3dfV5tfIZPfw3bQZoMX4teYxfSuUzQbX4pVR2P5BZnm1TZoCW49BiBmh5/846sw8R9rNG7kWc6PlhIoDWToraCFrfv7OeBU49filpf41UFMMD6CEONQH0sH8luMifU7wFEMnQAHqaNVyJYLT4Lbh5/9xyfNSPg0dTPwYT6YSJ/JGe3E3/SM9fDY6DX8P+JkjU2VFKvma2Vy37s/0X8GxIAD3OjtYX+LPxK8RvQfzwzO3++DN7DKWmLIGjXEBK8UMMHiPVU/c3QbwvfXNvhhA/9NA7UB9vr797Pr433WeAI79FYybip4NIxTFkCbxEMEokvM9qoyNQOGv612F5wK82tUekYIHJL0TFfAQKCpgBnmTxTQ8iBdRhBnjRye9/I1CAYfIzQCIF6DI/AyRQAHoxH8CUiBSAPuSXwAB0Dfs2GACwhgACkEUAAcgigABkEUAAsgggAFkEEIAsAghAFgEEIIsAApBFAAHIIoAAZBFAALIIIABZBBCArL85OtzX371tSgAAAABJRU5ErkJggg==";

fn resolve_output_path(custom_arg: Option<String>) -> PathBuf {
    if let Some(arg) = custom_arg {
        return PathBuf::from(arg);
    }

    let parent_pdf = Path::new("../pdf");
    if parent_pdf.exists() || (!Path::new("../Cargo.toml").exists() && Path::new("templates").exists()) {
        return parent_pdf.join("termo_transferencia_exemplo.pdf");
    }

    PathBuf::from("pdf/termo_transferencia_exemplo.pdf")
}

fn main() {
    println!("╔══════════════════════════════════════════════════════════════════╗");
    println!("║   PREFEITURA DE SAQUAREMA - GERADOR DE TERMO DE EMPRÉSTIMO PDF   ║");
    println!("║                Módulo Rust + Typst (FastAPI Ready)              ║");
    println!("╚══════════════════════════════════════════════════════════════════╝\n");

    let custom_output = env::args().nth(1);
    let output_path = resolve_output_path(custom_output);

    println!("📄 Preparando dados do Termo de Empréstimo e Responsabilidade...");

    let data = DocumentData {
        titulo: DEFAULT_TITULO.to_string(),
        unidade_saida: "Secretaria Municipal de Educação, Cultura, Inclusão, Ciência e Tecnologia (SMECICT)".to_string(),
        unidade_destino: "Escola Municipal Orgé Ferreira dos Santos".to_string(),
        responsavel_nome: "Carlos Eduardo Silveira".to_string(),
        responsavel_matricula: "48921-0".to_string(),
        responsavel_cargo: "Coordenador de Tecnologia da Informação".to_string(),
        equipamentos: vec![
            EquipamentoItem::new("Notebook Dell Latitude 5440 (Patrimônio: PAT-2026-4412)", "02"),
            EquipamentoItem::new("Monitor Dell 27\" UltraSharp 4K (Patrimônio: PAT-2026-8891)", "02"),
            EquipamentoItem::new("Projetor Multimídia Epson PowerLite E20 3400 Lumens", "01"),
            EquipamentoItem::new("Kit Teclado e Mouse Sem Fio Logitech MK235", "02"),
        ],
        data_retirada: "19/10/2026".to_string(),
        data_devolucao: "30/11/2026".to_string(),
        assinatura_responsavel_base64: Some(format!("data:image/png;base64,{}", ASSINATURA_EXEMPLO_B64)),
        assinatura_solicitante_base64: None,
    };

    println!("⚙️  Compilando template Typst com cabeçalho/rodapé de public/images/ e assinatura Base64...");

    match generate_pdf(&data, &output_path) {
        Ok(path) => {
            let metadata = fs::metadata(&path).unwrap();
            let size_kb = metadata.len() as f64 / 1024.0;
            let abs_path = fs::canonicalize(&path).unwrap_or(path.clone());

            println!("\n✅ SUCESSO! PDF gerado com êxito!");
            println!("   📍 Destino: {}", abs_path.display());
            println!("   📦 Tamanho: {:.2} KB ({} bytes)", size_kb, metadata.len());
        }
        Err(err) => {
            eprintln!("\n❌ ERRO ao gerar o PDF: {}", err);
            std::process::exit(1);
        }
    }
}

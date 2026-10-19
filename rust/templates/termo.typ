// Template Typst — Termo de Empréstimo e Responsabilidade de Equipamento (Prefeitura de Saquarema)
#import sys: inputs

// Extração dos parâmetros de entrada
#let titulo = inputs.at("titulo", default: "TERMO DE EMPRÉSTIMO E RESPONSABILIDADE DE EQUIPAMENTO")
#let unidade_saida = inputs.at("unidade_saida", default: "")
#let unidade_destino = inputs.at("unidade_destino", default: "")
#let responsavel_nome = inputs.at("responsavel_nome", default: "")
#let responsavel_matricula = inputs.at("responsavel_matricula", default: "")
#let responsavel_cargo = inputs.at("responsavel_cargo", default: "")
#let data_retirada = inputs.at("data_retirada", default: "___/___/___")
#let data_devolucao = inputs.at("data_devolucao", default: "___/___/___")

// Flags de presença de imagens (injetadas pelo módulo Rust)
#let tem_cabecalho_img = inputs.at("tem_cabecalho_img", default: "false") == "true"
#let tem_rodape_img = inputs.at("tem_rodape_img", default: "false") == "true"
#let tem_assinatura_responsavel = inputs.at("tem_assinatura_responsavel", default: "false") == "true"
#let tem_assinatura_solicitante = inputs.at("tem_assinatura_solicitante", default: "false") == "true"
#let assinatura_responsavel_arquivo = inputs.at("assinatura_responsavel_arquivo", default: "assinatura_responsavel.png")
#let assinatura_solicitante_arquivo = inputs.at("assinatura_solicitante_arquivo", default: "assinatura_solicitante.png")

// Lista de equipamentos serializada (formato: "descricao\tquantidade\ndescricao2\tquantidade2")
#let equipamentos_raw = inputs.at("equipamentos_raw", default: "")

// Configuração da página A4 com cabeçalho e rodapé de ponta a ponta
#set page(
  paper: "a4",
  margin: (top: 4.3cm, bottom: 3.2cm, left: 2.2cm, right: 2.2cm),
  background: {
    if tem_cabecalho_img {
      place(top + left, image("cabecalho.png", width: 100%))
    }
    if tem_rodape_img {
      place(bottom + left, image("rodape.png", width: 100%))
    }
  }
)

#set text(
  font: ("Liberation Sans", "DejaVu Sans", "Libertinus Serif"),
  size: 10.5pt,
  fill: rgb("#0f172a"),
  lang: "pt"
)

// Helper para renderizar campo sublinhado no corpo do texto
#let campo_sublinhado(valor, largura_minima) = {
  if valor.trim() != "" {
    box(
      width: auto,
      stroke: (bottom: 0.6pt + black),
      inset: (bottom: 2pt, x: 8pt),
      baseline: 2pt,
      align(center)[#text(weight: "bold")[#valor]]
    )
  } else {
    box(
      width: largura_minima,
      stroke: (bottom: 0.6pt + black),
      baseline: 2pt,
      []
    )
  }
}

// 1. Título do Documento
#v(0.2cm)
#align(center)[
  #block(width: 85%)[
    #text(size: 12pt, weight: "bold")[
      #upper(titulo)
    ]
  ]
]

#v(0.7cm)

// 2. Dados das Unidades Participantes
#block(width: 100%, spacing: 0.9em)[
  #text(weight: "bold")[Unidade de Saída:] #h(4pt)
  #if unidade_saida.trim() != "" [
    #text(weight: "regular")[#unidade_saida]
  ]
]

#block(width: 100%, spacing: 0.9em)[
  #text(weight: "bold")[Para (Unidade / Setor de Destino):] #h(4pt)
  #if unidade_destino.trim() != "" [
    #text(weight: "regular")[#unidade_destino]
  ]
]

#v(0.4cm)

// 3. Declaração do Responsável pela Unidade de Saída
#par(justify: true, leading: 1.15em)[
  #h(1.8cm) Eu, #campo_sublinhado(responsavel_nome, 9.5cm),
  portador(a) da *Matrícula nº* #campo_sublinhado(responsavel_matricula, 4.2cm), exercendo a *função/cargo de* #campo_sublinhado(responsavel_cargo, 6.5cm), autorizo o empréstimo do(s) equipamento(s) e/ou material(is) discriminado(s) abaixo:
]

#v(0.6cm)

// 4. Tabela de Especificação dos Equipamentos
#text(size: 10pt, weight: "bold")[ESPECIFICAÇÃO DO(S) EQUIPAMENTO(S)]
#v(0.2cm)

#{
  let linhas_equipamentos = ()
  if equipamentos_raw.trim() != "" {
    for linha in equipamentos_raw.split("\n") {
      if linha.trim() != "" {
        let partes = linha.split("\t")
        let desc = partes.at(0, default: "")
        let qtd = partes.at(1, default: "")
        linhas_equipamentos.push((desc, qtd))
      }
    }
  }

  // Garante pelo menos 4 linhas na tabela como no formulário padrão
  while linhas_equipamentos.len() < 4 {
    linhas_equipamentos.push(("", ""))
  }

  table(
    columns: (1fr, 90pt),
    stroke: 0.7pt + black,
    inset: (x: 10pt, y: 10pt),
    align: (col, row) => if col == 0 { left + horizon } else { center + horizon },
    table.header(
      [*Equipamento / Descrição*],
      [*Qtd.*]
    ),
    ..for (desc, qtd) in linhas_equipamentos {
      (
        if desc.trim() != "" {
          text(size: 10pt)[#desc]
        } else {
          line(length: 100%, stroke: 0.4pt + rgb("#64748b"))
        },
        if qtd.trim() != "" {
          text(size: 10pt, weight: "bold")[#qtd]
        } else {
          line(length: 60%, stroke: 0.4pt + rgb("#64748b"))
        }
      )
    }
  )
}

#v(0.9cm)

// 5. Bloco de Assinaturas (com suporte a imagem Base64)
#let bloco_assinatura(rotulo, tem_imagem, arquivo_imagem) = {
  grid(
    columns: (auto, 8.5cm),
    column-gutter: 6pt,
    align: (left + bottom, center + bottom),
    [#text(size: 9.5pt, weight: "bold")[#rotulo]],
    [
      #if tem_imagem [
        #box(height: 1.35cm, width: 100%)[
          #align(center + bottom)[
            #image(arquivo_imagem, height: 1.3cm, fit: "contain")
          ]
        ]
        #v(-2pt)
      ] else [
        #v(0.9cm)
      ]
      #line(length: 100%, stroke: 0.7pt + black)
    ]
  )
}

#bloco_assinatura(
  "ASSINATURA DO RESPONSÁVEL:",
  tem_assinatura_responsavel,
  assinatura_responsavel_arquivo
)

#v(0.4cm)

#bloco_assinatura(
  "ASSINATURA DO SOLICITANTE:",
  tem_assinatura_solicitante,
  assinatura_solicitante_arquivo
)

#v(0.9cm)

// 6. Datas de Retirada e Devolução
#grid(
  columns: (1fr, 1fr),
  align: (left, left),
  [
    #text(size: 9.5pt, weight: "bold")[DATA DA RETIRADA: ]
    #if data_retirada.trim() != "" and data_retirada.trim() != "___/___/___" [
      #box(stroke: (bottom: 0.6pt + black), inset: (bottom: 1pt, x: 6pt))[#data_retirada]
    ] else [
      #text(size: 9.5pt, weight: "bold")[\_\_\_/\_\_\_/\_\_\_]
    ]
  ],
  [
    #text(size: 9.5pt, weight: "bold")[DATA DA DEVOLUÇÃO: ]
    #if data_devolucao.trim() != "" and data_devolucao.trim() != "___/___/___" [
      #box(stroke: (bottom: 0.6pt + black), inset: (bottom: 1pt, x: 6pt))[#data_devolucao]
    ] else [
      #text(size: 9.5pt, weight: "bold")[\_\_\_/\_\_\_/\_\_\_]
    ]
  ]
)

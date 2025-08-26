import os
import zipfile
from datetime import datetime
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

def generate_accounting_reports(processor, nomes_contas, df, output_dir=None, display_result=False, debug=False):
    """
    Gera relatórios específicos solicitados pelo contador.
    Parâmetros:
      - processor: instância de NeodontoCsvProcessor (usa helpers como format_currency, truncate_lines, etc.)
      - nomes_contas: dicionário com descrições das contas contábeis (NOMES_CONTAS_CONTABEIS)
      - df: DataFrame consolidado
    Retorna dicionário com resultados e paths dos arquivos gerados.
    """
    import tempfile

    # Usar diretório temporário se não for especificado
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    else:
        os.makedirs(output_dir, exist_ok=True)

    reports_config = [
        {"name": "taxas_manutencao", "title": "Relatório de Taxas de Manutenção", "filters": {"CodigoTipoRecebimento": 3}},
        {"name": "taxas_marketing", "title": "Relatório de Taxas de Marketing", "filters": {"CodigoTipoRecebimento": 4}},
        {"name": "multas_juros", "title": "Relatório de Multas e Juros", "filters": {"CodigoTipoRecebimento": 5}},
        {"name": "outras", "title": "Relatório de Outras", "filters": {"CodigoTipoRecebimento": 6}},
        {"name": "pre_pagamento_operadoras", "title": "Relatório de Pré-pagamento - Operadoras", "filters": {"CodigoTipoRecebimento": 1, "TipoSingular": "Operadora"}},
        {"name": "custo_operacional_operadoras", "title": "Relatório de Custo Operacional - Operadoras", "filters": {"CodigoTipoRecebimento": 2, "TipoSingular": "Operadora"}},
        {"name": "pre_pagamento_prestadoras", "title": "Relatório de Pré-pagamento - Prestadoras", "filters": {"CodigoTipoRecebimento": 1, "TipoSingular": "Prestadora"}},
        {"name": "custo_operacional_prestadoras", "title": "Relatório de Custo Operacional  - Prestadoras", "filters": {"CodigoTipoRecebimento": 2, "TipoSingular": "Prestadora"}}
    ]

    results = {}
    pdf_files = []
    csv_files = []

    config = processor.get_pdf_config()
    styles = config['styles']
    cell_style = config['cell_style']

    required_columns = ['CodigoTipoRecebimento', 'TipoSingular', 'Tipo', 'DATA', 'valor', 'complemento', 'Debito', 'Credito', 'Historico']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colunas ausentes no DataFrame: {', '.join(missing_columns)}")

    for report_config in reports_config:
        filtered_df = df.copy()

        if debug:
            processor.debug_report_data(filtered_df, f"Antes do filtro - {report_config['title']}")

        for key, value in report_config["filters"].items():
            if key in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[key] == value]
            else:
                if display_result:
                    # usar st se disponível via processor context
                    try:
                        import streamlit as st
                        st.warning(f"Coluna {key} não encontrada para o relatório {report_config['title']}")
                    except Exception:
                        pass
                continue

        if debug:
            processor.debug_report_data(filtered_df, f"Após filtros - {report_config['title']}")

        if filtered_df.empty:
            if display_result:
                try:
                    import streamlit as st
                    st.warning(f"Nenhum dado encontrado para {report_config['title']}")
                except Exception:
                    pass
            results[report_config["name"]] = {"count": 0, "sum": 0, "file": None}
            continue

        csv_file = os.path.join(output_dir, f"{report_config['name']}.csv")
        pdf_file = os.path.join(output_dir, f"{report_config['name']}.pdf")

        # Exportar para CSV
        processor.export_to_csv(filtered_df, csv_file)
        csv_files.append(csv_file)

        # Manter apenas o código nas colunas de conta/histórico (não inserir descrições longas)
        filtered_df['Debito_Code'] = filtered_df['Debito'].apply(lambda x: str(int(x)) if pd_notnull_and_digits(x) else '')
        filtered_df['Credito_Code'] = filtered_df['Credito'].apply(lambda x: str(int(x)) if pd_notnull_and_digits(x) else '')
        filtered_df['Historico_Code'] = filtered_df['Historico'].apply(lambda x: str(int(x)) if pd_notnull_and_digits(x) else '')

        # Criar PDF usando configurações do processor
        doc = SimpleDocTemplate(pdf_file, pagesize=config['pagesize'],
                                leftMargin=config['margins']['left'], rightMargin=config['margins']['right'],
                                topMargin=config['margins']['top'], bottomMargin=config['margins']['bottom'])
        elements = []

        elements.append(Paragraph(report_config["title"], styles['Title']))
        elements.append(Spacer(1, 0.25 * inch))

        date_str = filtered_df['DATA'].iloc[0] if not filtered_df.empty else ""
        elements.append(Paragraph(f"Data de referência: {date_str}", styles['Normal']))
        elements.append(Spacer(1, 0.15 * inch))

        record_count = len(filtered_df)
        total_value = filtered_df['valor'].sum()

        summary_data = [
            ["Total de registros", str(record_count)],
            ["Valor total", f"R$ {total_value:.2f}".replace('.', ',')]
        ]

        summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT')
        ]))

        elements.append(summary_table)
        elements.append(Spacer(1, 0.25 * inch))

        display_df = filtered_df[['DATA', 'complemento', 'valor', 'Debito_Code', 'Credito_Code', 'Historico_Code']].copy()
        display_df.columns = ['Data', 'Complemento', 'Valor', 'Débito', 'Crédito', 'Histórico']

        data = [display_df.columns.tolist()]
        for _, row in display_df.iterrows():
            row_data = []
            for col, val in row.items():
                if col == 'Valor' and isinstance(val, (int, float)):
                    val_str = f"R$ {val:.2f}".replace('.', ',')
                    val = Paragraph(val_str, cell_style)
                elif col == 'Complemento':
                    val_str = str(val)
                    complemento_formatado = processor.truncate_lines(val_str, max_chars_per_line=55, max_lines=3)
                    val = Paragraph(complemento_formatado, cell_style)
                elif col in ['Débito', 'Crédito', 'Histórico']:
                    # Exibir apenas o código (mais compacto)
                    val = Paragraph(str(val), cell_style)
                elif col == 'Data':
                    val = Paragraph(str(val), cell_style)
                else:
                    val = str(val)
                row_data.append(val)
            data.append(row_data)

        total_row = ['', 'TOTAL', Paragraph(f"R$ {total_value:.2f}".replace('.', ','), cell_style), '', '', '']
        data.append(total_row)

        col_widths = [0.6*inch, 1.8*inch, 0.7*inch, 1.4*inch, 1.4*inch, 0.8*inch]

        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 6),
            ('ALIGN', (2, -1), (2, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
        ])

        table = Table(data, colWidths=col_widths, repeatRows=1, splitByRow=True, rowHeights=None)
        table.setStyle(table_style)
        elements.append(table)

        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))

        doc.build(elements)

        results[report_config["name"]] = {"count": record_count, "sum": total_value, "file": pdf_file}
        pdf_files.append(pdf_file)

        if display_result:
            try:
                import streamlit as st
                st.success(f"✅ Relatório gerado: {report_config['title']} - {record_count} registros, Total: R$ {total_value:.2f}")
            except Exception:
                pass

    # resumo geral
    summary_file = os.path.join(output_dir, "resumo_relatorios.pdf")
    config = processor.get_pdf_config()
    styles = config['styles']

    doc = SimpleDocTemplate(summary_file, pagesize=config['pagesize'],
                            leftMargin=config['margins']['left'], rightMargin=config['margins']['right'],
                            topMargin=config['margins']['top'], bottomMargin=config['margins']['bottom'])
    elements = []

    elements.append(Paragraph("Resumo dos Relatórios Contábeis", styles['Title']))
    elements.append(Spacer(1, 0.5 * inch))

    summary_data = [["Relatório", "Registros", "Valor Total"]]
    total_overall = 0

    for report_config in reports_config:
        report_name = report_config["name"]
        if report_name in results:
            report_result = results[report_name]
            summary_data.append([report_config["title"], str(report_result["count"]), f"R$ {report_result['sum']:.2f}".replace('.', ',')])
            total_overall += report_result["sum"]

    summary_data.append(["TOTAL GERAL", "", f"R$ {total_overall:.2f}".replace('.', ',')])

    summary_table = Table(summary_data, colWidths=[3*inch, 0.8*inch, 1.2*inch])
    summary_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    summary_table.setStyle(summary_style)
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(f"Resumo gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))

    doc.build(elements)
    pdf_files.append(summary_file)

    zip_file = os.path.join(output_dir, "relatorios_contabeis.zip")
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pdf_file in pdf_files:
            zipf.write(pdf_file, os.path.basename(pdf_file))
        for csv_file in csv_files:
            zipf.write(csv_file, os.path.basename(csv_file))

    return {"reports": results, "summary_file": summary_file, "zip_file": zip_file}


def generate_unified_report(processor, df, output_dir=None, display_result=False):
    import tempfile
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    else:
        os.makedirs(output_dir, exist_ok=True)

    required_columns = ['Tipo', 'DATA', 'valor', 'complemento', 'Debito', 'Credito', 'Historico']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colunas ausentes no DataFrame: {', '.join(missing_columns)}")

    irrf_info = processor.calculate_irrf_from_original_data(df)

    valor_bruto_a_pagar = irrf_info['valor_bruto_a_pagar']
    valor_bruto_a_receber = irrf_info['valor_bruto_a_receber']
    valor_liquido_a_pagar = irrf_info['valor_liquido_a_pagar']
    valor_liquido_a_receber = irrf_info['valor_liquido_a_receber']
    saldo_liquido = valor_liquido_a_receber - valor_liquido_a_pagar
    saldo_bruto = valor_bruto_a_receber - valor_bruto_a_pagar

    mask_nao_irrf = ~processor.is_irrf_record(df)
    df_a_pagar_bruto = df[(df['Tipo'] == 'A pagar') & mask_nao_irrf]
    df_a_receber_bruto = df[(df['Tipo'] == 'A receber') & mask_nao_irrf]

    config = processor.get_pdf_config()
    styles = config['styles']
    cell_style = config['cell_style']

    pdf_file = os.path.join(output_dir, "relatorio_camara_compensacao.pdf")
    doc = SimpleDocTemplate(pdf_file, pagesize=config['pagesize'],
                            leftMargin=config['margins']['left'], rightMargin=config['margins']['right'],
                            topMargin=config['margins']['top'], bottomMargin=config['margins']['bottom'])
    elements = []

    def create_csv_table(data_df, section_title):
        section_elements = []
        if data_df.empty:
            section_elements.append(Paragraph(f"{section_title} - Nenhum registro encontrado", styles['Heading2']))
            return section_elements, 0, 0

        section_elements.append(Paragraph(section_title, styles['Heading2']))
        section_elements.append(Spacer(1, 0.1 * inch))

        table_data = [['Data', 'Complemento', 'Valor Bruto', 'IRRF', 'Valor Líquido', 'Débito', 'Crédito', 'Histórico']]
        total_bruto = total_irrf = total_liquido = 0

        for _, row in data_df.iterrows():
            is_irrf_lancamento = processor.is_irrf_record(pd.DataFrame([row]))
            if is_irrf_lancamento.iloc[0]:
                valor_bruto = 0
                irrf = row['valor']
                valor_liquido = 0
            else:
                valor_bruto = row['valor']
                irrf = 0
                if 'IRRF' in row and pd_notnull(row.get('IRRF', 0)):
                    irrf = processor.normalize_value(row['IRRF'])
                valor_liquido = valor_bruto - irrf

            total_bruto += valor_bruto
            total_irrf += irrf
            total_liquido += valor_liquido

            complemento_texto = str(row['complemento'])
            complemento_formatado = processor.truncate_lines(complemento_texto, max_chars_per_line=55, max_lines=3)
            complemento = Paragraph(complemento_formatado, cell_style)

            table_data.append([
                row['DATA'],
                complemento,
                processor.format_currency(valor_bruto),
                processor.format_currency(irrf),
                processor.format_currency(valor_liquido),
                str(row['Debito']),
                str(row['Credito']),
                str(row['Historico'])
            ])

        col_widths = [0.6*inch, 3.2*inch, 0.7*inch, 0.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.6*inch]
        table = Table(table_data, colWidths=col_widths, repeatRows=1, splitByRow=True)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
            ('ALIGN', (5, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ])
        table.setStyle(table_style)
        section_elements.append(table)
        section_elements.append(Spacer(1, 0.2 * inch))
        return section_elements, total_liquido, total_irrf

    elements.append(Paragraph("RELATÓRIO DA CÂMARA DE COMPENSAÇÃO", styles['Title']))
    elements.append(Spacer(1, 0.3 * inch))

    total_a_pagar_liquido = valor_liquido_a_pagar
    total_a_receber_liquido = valor_liquido_a_receber

    date_str = df['DATA'].iloc[0] if not df.empty else ""
    elements.append(Paragraph(f"Data de referência: {date_str}", styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    resumo_data = [
        ['RESUMO EXECUTIVO', '', '', '', ''],
        ['Categoria', 'Registros', 'Valor Bruto', 'IRRF', 'Valor Líquido'],
        ['A Pagar', str(len(df_a_pagar_bruto)), processor.format_currency(valor_bruto_a_pagar), processor.format_currency(irrf_info['irrf_a_pagar']), processor.format_currency(valor_liquido_a_pagar)],
        ['A Receber', str(len(df_a_receber_bruto)), processor.format_currency(valor_bruto_a_receber), processor.format_currency(irrf_info['irrf_a_receber']), processor.format_currency(valor_liquido_a_receber)],
        ['', '', '', '', ''],
        ['SALDO BRUTO', '', processor.format_currency(saldo_bruto), '', ''],
        ['SALDO LÍQUIDO', '', '', '', processor.format_currency(saldo_liquido)]
    ]

    resumo_table = Table(resumo_data, colWidths=[1.5*inch, 0.8*inch, 1*inch, 0.8*inch, 1*inch])
    resumo_style = TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, 1), colors.grey),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.whitesmoke),
        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 6),
        ('BACKGROUND', (0, 2), (-1, 4), colors.white),
        ('ALIGN', (1, 2), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 2), (-1, 4), 6),
        ('BACKGROUND', (0, 5), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, 5), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 5), (-1, -1), 6),
        ('ALIGN', (4, 5), (4, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ])
    resumo_table.setStyle(resumo_style)
    elements.append(resumo_table)

    from reportlab.platypus import PageBreak
    elements.append(PageBreak())
    a_pagar_elements, _, _ = create_csv_table(df[df['Tipo'] == 'A pagar'], "DETALHAMENTO - A PAGAR")
    elements.extend(a_pagar_elements)
    elements.append(PageBreak())
    a_receber_elements, _, _ = create_csv_table(df[df['Tipo'] == 'A receber'], "DETALHAMENTO - A RECEBER")
    elements.extend(a_receber_elements)

    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))

    doc.build(elements)

    if display_result:
        try:
            import streamlit as st
            st.success(f"✅ Relatório unificado gerado com sucesso!")
            st.info(f"📊 A Pagar: {len(df_a_pagar_bruto)} registros - {processor.format_currency(valor_liquido_a_pagar)}")
            st.info(f"📈 A Receber: {len(df_a_receber_bruto)} registros - {processor.format_currency(valor_liquido_a_receber)}")
            st.info(f"🧾 IRRF Total: {processor.format_currency(irrf_info['total_irrf'])} (A Pagar: {processor.format_currency(irrf_info['irrf_a_pagar'])}, A Receber: {processor.format_currency(irrf_info['irrf_a_receber'])})")
            st.info(f"💰 Saldo Bruto: {processor.format_currency(saldo_bruto)}")
            st.info(f"💰 Saldo Líquido: {processor.format_currency(saldo_liquido)}")
        except Exception:
            pass

    return {"pdf_file": pdf_file, "total_a_pagar": valor_liquido_a_pagar, "total_a_receber": valor_liquido_a_receber,
            "count_a_pagar": len(df_a_pagar_bruto), "count_a_receber": len(df_a_receber_bruto), "saldo": saldo_liquido,
            "irrf_info": irrf_info, "valor_bruto_a_pagar": valor_bruto_a_pagar, "valor_bruto_a_receber": valor_bruto_a_receber,
            "saldo_bruto": saldo_bruto}


def generate_irrf_report(processor, df, output_dir=None, display_result=False):
    import tempfile
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    else:
        os.makedirs(output_dir, exist_ok=True)

    irrf_info = processor.calculate_irrf_from_original_data(df)

    if irrf_info['total_irrf'] == 0:
        if display_result:
            try:
                import streamlit as st
                st.warning("Nenhum registro com IRRF encontrado nos dados originais.")
            except Exception:
                pass
        return None

    mask_nao_irrf = ~processor.is_irrf_record(df)
    df_original = df[mask_nao_irrf].copy()

    if 'IRRF' in df_original.columns:
        df_original['IRRF_normalizado'] = df_original['IRRF'].apply(processor.normalize_value)
        df_irrf = df_original[df_original['IRRF_normalizado'] > 0].copy()
    else:
        df_irrf = df_original.iloc[0:0].copy()

    config = processor.get_pdf_config()
    styles = config['styles']
    cell_style = config['cell_style']

    pdf_file = os.path.join(output_dir, "relatorio_irrf.pdf")
    doc = SimpleDocTemplate(pdf_file, pagesize=config['pagesize'],
                            leftMargin=config['margins']['left'], rightMargin=config['margins']['right'],
                            topMargin=config['margins']['top'], bottomMargin=config['margins']['bottom'])
    elements = []

    elements.append(Paragraph("RELATÓRIO DE IRRF - IMPOSTO DE RENDA RETIDO NA FONTE", styles['Title']))
    elements.append(Spacer(1, 0.3 * inch))

    date_str = df_irrf['DATA'].iloc[0] if not df_irrf.empty else ""
    elements.append(Paragraph(f"Data de referência: {date_str}", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    table_data = [['Tipo', 'Entidade', 'Valor IRRF', 'Observação']]
    for _, row in df_irrf.iterrows():
        valor_irrf = row.get('IRRF_normalizado', 0)
        entidade = str(row.get('NomeSingular', 'N/A'))
        if len(entidade) > 30:
            entidade = entidade[:27] + '...'
        table_data.append([row['Tipo'], Paragraph(entidade, cell_style), processor.format_currency(valor_irrf), "IRRF dos dados originais"])

    table_data.append(['', Paragraph('<b>TOTAL</b>', cell_style), f'<b>{processor.format_currency(irrf_info["total_irrf"])}</b>', ''])

    col_widths = [0.8*inch, 1.8*inch, 1*inch, 1.8*inch]
    table = Table(table_data, colWidths=col_widths, repeatRows=1, splitByRow=True)
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 1), (-1, -2), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 6),
        ('ALIGN', (2, -1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("RESUMO ESTATÍSTICO", styles['Heading2']))
    elements.append(Spacer(1, 0.1 * inch))

    resumo_data = [
        ['Categoria', 'Registros', 'Total IRRF'],
        ['A Pagar', str(len(df_irrf[df_irrf['Tipo'] == 'A pagar'])), processor.format_currency(irrf_info['irrf_a_pagar'])],
        ['A Receber', str(len(df_irrf[df_irrf['Tipo'] == 'A receber'])), processor.format_currency(irrf_info['irrf_a_receber'])],
        ['TOTAL GERAL', str(irrf_info['registros_com_irrf']), processor.format_currency(irrf_info['total_irrf'])]
    ]

    resumo_table = Table(resumo_data, colWidths=[1.5*inch, 1.2*inch, 1.3*inch])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(resumo_table)

    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("OBSERVAÇÕES:", styles['Heading3']))
    elements.append(Paragraph("• Registros de IRRF identificados através da palavra 'IRRF' no complemento", styles['Normal']))
    elements.append(Paragraph("• Valores apresentados são os valores dos registros contábeis de IRRF", styles['Normal']))
    elements.append(Paragraph("• IRRF A Pagar: valores deduzidos dos pagamentos", styles['Normal']))
    elements.append(Paragraph("• IRRF A Receber: valores deduzidos dos recebimentos", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))

    doc.build(elements)

    if display_result:
        try:
            import streamlit as st
            st.success(f"✅ Relatório de IRRF gerado com sucesso!")
            st.info(f"📊 Total de registros com IRRF: {irrf_info['registros_com_irrf']}")
            st.info(f"💰 Total IRRF: {processor.format_currency(irrf_info['total_irrf'])}")
            st.info(f"🔸 IRRF A Pagar: {processor.format_currency(irrf_info['irrf_a_pagar'])}")
            st.info(f"🔹 IRRF A Receber: {processor.format_currency(irrf_info['irrf_a_receber'])}")
        except Exception:
            pass

    return {"pdf_file": pdf_file, "total_irrf": irrf_info['total_irrf'], "total_registros": irrf_info['registros_com_irrf'],
            "irrf_a_pagar": irrf_info['irrf_a_pagar'], "irrf_a_receber": irrf_info['irrf_a_receber']}


# Pequena helper para evitar repetição ao verificar valores numéricos
def pd_notnull_and_digits(x):
    try:
        import pandas as pd
        return pd.notnull(x) and str(x).isdigit()
    except Exception:
        return False

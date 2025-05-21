import pandas as pd
import streamlit as st
import io
import base64
from datetime import datetime, timedelta
import os
import numpy as np
import re
import matplotlib.pyplot as plt
import seaborn as sns
import zipfile
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.units import cm

# Configurar o título e o ícone da página
st.set_page_config(
    page_title="Processador de CSV Uniodonto",
    page_icon="📊",
    layout="wide"
)

# Dicionário com descrições das contas contábeis
NOMES_CONTAS_CONTABEIS = {
    85433: "Contraprestação assumida em Pós-pagamento",
    40507: "Despesas com Eventos/ Sinistros",
    90919: "Intercâmbio a Pagar de Corresponsabilidade Cedida - Preço Pós-estabelecido",
    15456: "IRRF - sobre Faturamento",
    40140: "Ato Odontológico",
    51202: "Despesas Diversas",
    52631: "Taxa para Manutenção da Central",
    52532: "Propaganda e Marketing - Matriz",
    19958: "Contraprestação Corresponsabilidade Assumida Pré-pagamento",
    52632: "Taxa para Manutenção da Federação",
    19253: "Crédito com Singulares",
    40413: "(-) Recup.Reemb. Contratante Assumida Pós-pagamento",
    23476: "IRPJ - NF Serviços (cod. 3280)",
    21898: "Contrap. Corresp. Assumida Pós",
    92003: "Rede Contratada/Credenciada PJ - clínicas",
    30203: "Corresponsabilidade Assumida Pré",
    22036: "Federação Paulista",
    1021: "VL. N/NFF. INTERC. RECEB.ODONT",
    2005: "VL. S/NFF. INTERC. A PAGAR",
    2341: "VL. IRRF S/NF INTERC. PAGAR",
    22: "VL. IRRF N/NFF. SERVIÇOS",
    361: "VL. TAXA MANUT. DA CENTRAL S/N",
    365: "VL. FUNDO DE MARKTING S/NFF",
    30: "VL. CONTRATO SERVIÇOS DIVERSOS",
    33: "VL. CONTRAP. A RECEBER ODONT",
    228: "VL. CONTRAP. A RECEBER CLINICA",
    31426: "VL. CONTRATO OUTROS SERVIÇOS",
    30069: "VL. CONTRAP. RECEBIDA",
    30071: "VL. CONTRAP. RECEBIDA - CONSULTORIA",
    30127: "VL. CONTRAP. SERVIÇOS ADMINISTRATIVOS",
    368: "VL. TAXA MANUT. DA FEDERAÇÃO",
    179: "VL. MULTAS/JUROS"
}

class NeodontoCsvProcessor:
    def __init__(self):
        self.today = datetime.today()
        self.first_day_of_current_month = self.today.replace(day=1)
        self.last_day_of_previous_month = self.first_day_of_current_month - timedelta(days=1)
        self.processed_files = []
        self.error_files = []
    
    def calculate_debit(self, row):
        """Calcula o valor de débito baseado nas condições específicas."""
        tipo = row['Tipo']
        tipo_singular = row['TipoSingular']
        codigo_tipo_recebimento = row['CodigoTipoRecebimento']
        nome_singular = str(row['NomeSingular']).upper() if pd.notnull(row['NomeSingular']) else ""
        descricao = str(row['Descricao']).upper() if pd.notnull(row['Descricao']) else ""
        
        # Regras especiais para CodigoTipoRecebimento 5
        if codigo_tipo_recebimento == 5:
            if "LGPD" in descricao:
                return 52129
            elif "ATUARIO" in descricao or "ATUÁRIO" in descricao:
                return 52451

        # A pagar
        if tipo == 'A pagar':
            if tipo_singular == 'Operadora':
                if codigo_tipo_recebimento == 1:
                    return 31731
                elif codigo_tipo_recebimento == 2:
                    return 40507
                elif codigo_tipo_recebimento == 3:
                    if nome_singular == "UNIODONTO DO BRASIL":
                        return 52631
                    else:
                        return 52632
                elif codigo_tipo_recebimento == 4:
                    return 52532
                elif codigo_tipo_recebimento == 5:
                    return 51818
                elif codigo_tipo_recebimento == 6:
                    return 51202
            elif tipo_singular == 'Prestadora':
                if codigo_tipo_recebimento in [1, 2]:
                    return 40140
                elif codigo_tipo_recebimento == 3:
                    if nome_singular == "UNIODONTO DO BRASIL":
                        return 52631
                    else:
                        return 52632
                elif codigo_tipo_recebimento == 4:
                    return 52532
                elif codigo_tipo_recebimento == 5:
                    return 51818
                elif codigo_tipo_recebimento == 6:
                    return 51202
        # A receber
        elif tipo == 'A receber':
            if tipo_singular == 'Operadora':
                if codigo_tipo_recebimento == 1:
                    return 19958
                elif codigo_tipo_recebimento == 2:
                    return 85433
                elif codigo_tipo_recebimento in [3, 4, 5]:
                    return 84679
                elif codigo_tipo_recebimento == 6:
                    return 19253
            elif tipo_singular == 'Prestadora':
                if codigo_tipo_recebimento == 1:
                    return 19253
                elif codigo_tipo_recebimento == 2:
                    return 19253
                elif codigo_tipo_recebimento in [3, 4, 5]:
                    return 84679
                elif codigo_tipo_recebimento == 6:
                    return 19253
        return ''
    
    def calculate_credit(self, row):
        """Calcula o valor de crédito baseado nas condições específicas."""
        tipo = row['Tipo']
        tipo_singular = row['TipoSingular']
        codigo_tipo_recebimento = row['CodigoTipoRecebimento']
        nome_singular = str(row['NomeSingular']).upper() if pd.notnull(row['NomeSingular']) else ""
        descricao = str(row['Descricao']).upper() if pd.notnull(row['Descricao']) else ""
        
        # Regras especiais para CodigoTipoRecebimento 5
        if codigo_tipo_recebimento == 5:
            if "LGPD" in descricao or "ATUARIO" in descricao or "ATUÁRIO" in descricao:
                return 22036

        # A pagar
        if tipo == 'A pagar':
            if tipo_singular == 'Operadora':
                if codigo_tipo_recebimento == 1:
                    return 90918
                elif codigo_tipo_recebimento == 2:
                    return 90919
                elif codigo_tipo_recebimento == 3:
                    if nome_singular == "UNIODONTO DO BRASIL":
                        return 21898
                    else:
                        return 22036
                elif codigo_tipo_recebimento == 4:
                    if nome_singular == "UNIODONTO DO BRASIL":
                        return 21898
                    else:
                        return 22036
                elif codigo_tipo_recebimento == 5:
                    return 51818
                elif codigo_tipo_recebimento == 6:
                    return 90919
            elif tipo_singular == 'Prestadora':
                if codigo_tipo_recebimento in [1, 2]:
                    return 92003
                elif codigo_tipo_recebimento == 3:
                    if nome_singular == "UNIODONTO DO BRASIL":
                        return 21898
                    else:
                        return 22036
                elif codigo_tipo_recebimento == 4:
                    if nome_singular == "UNIODONTO DO BRASIL":
                        return 21898
                    else:
                        return 22036
                elif codigo_tipo_recebimento == 5:
                    return 51818
                elif codigo_tipo_recebimento == 6:
                    return 90919
        # A receber
        elif tipo == 'A receber':
            if tipo_singular == 'Operadora':
                if codigo_tipo_recebimento == 1:
                    return 30203
                elif codigo_tipo_recebimento == 2:
                    return 40413
                elif codigo_tipo_recebimento == 3:
                    return 30069
                elif codigo_tipo_recebimento == 4:
                    return 30071
                elif codigo_tipo_recebimento == 5:
                    return 31426
                elif codigo_tipo_recebimento == 6:
                    return 30127
            elif tipo_singular == 'Prestadora':
                if codigo_tipo_recebimento == 1:
                    return 30203
                elif codigo_tipo_recebimento == 2:
                    return 40413
                elif codigo_tipo_recebimento == 3:
                    return 30069
                elif codigo_tipo_recebimento == 4:
                    return 30071
                elif codigo_tipo_recebimento == 5:
                    return 31426
                elif codigo_tipo_recebimento == 6:
                    return 30127
        return ''
    
    def calculate_history(self, row):
        """Calcula o valor do histórico baseado nas condições específicas."""
        tipo = row['Tipo']
        codigo_tipo_recebimento = row['CodigoTipoRecebimento']
        descricao = str(row['Descricao']).upper() if pd.notnull(row['Descricao']) else ""
        nome_singular = str(row['NomeSingular']).upper() if pd.notnull(row['NomeSingular']) else ""
        
        # Regras especiais para CodigoTipoRecebimento 5
        if codigo_tipo_recebimento == 5:
            if "LGPD" in descricao:
                return 2005
            elif "ATUARIO" in descricao or "ATUÁRIO" in descricao:
                return 2005

        # A pagar
        if tipo == 'A pagar':
            if codigo_tipo_recebimento in [1, 2, 6]:
                return 2005
            elif codigo_tipo_recebimento == 3:
                if nome_singular == "UNIODONTO DO BRASIL":
                    return 361
                else:
                    return 368
            elif codigo_tipo_recebimento == 4:
                return 365
            elif codigo_tipo_recebimento == 5:
                return 179
        # A receber
        elif tipo == 'A receber':
            if codigo_tipo_recebimento in [1, 2, 6]:
                return 1021
            elif codigo_tipo_recebimento == 3:
                return 33
            elif codigo_tipo_recebimento == 4:
                return 228
            elif codigo_tipo_recebimento == 5:
                return 30
        return ''
    
    def normalize_value(self, value):
        """Normaliza um valor para formato numérico."""
        if pd.isna(value) or value == '':
            return 0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        # Remove caracteres não numéricos, exceto ponto e vírgula
        value_str = str(value)
        value_str = re.sub(r'[^\d.,]', '', value_str)
        
        # Substitui vírgula por ponto
        value_str = value_str.replace(',', '.')
        
        try:
            return float(value_str)
        except ValueError:
            return 0
    
    def process_dataframe(self, df):
        """Processa o dataframe conforme as regras estabelecidas."""
        # Verifica se o DataFrame tem as colunas necessárias
        required_columns = [
            'Tipo', 'CodigoSingular', 'NomeSingular', 'TipoSingular', 
            'CodigoTipoRecebimento', 'DescricaoTipoRecebimento', 
            'ValorBruto', 'IRRF', 'Descricao'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Colunas ausentes no arquivo: {', '.join(missing_columns)}")
            return None
        
        # Converte CodigoTipoRecebimento para inteiro
        try:
            df['CodigoTipoRecebimento'] = pd.to_numeric(df['CodigoTipoRecebimento'], errors='coerce').fillna(0).astype(int)
        except Exception as e:
            st.warning(f"Aviso ao converter CodigoTipoRecebimento: {str(e)}. Tentando continuar o processamento.")
        
        # Aplica as funções para criar as colunas necessárias
        df['Debito'] = df.apply(self.calculate_debit, axis=1)
        df['Credito'] = df.apply(self.calculate_credit, axis=1)
        df['Historico'] = df.apply(self.calculate_history, axis=1)
        
        # Adiciona a coluna DATA com o último dia do mês anterior
        df['DATA'] = self.last_day_of_previous_month
        
        # Adiciona a coluna valor com os dados de ValorBruto
        df['valor'] = df['ValorBruto']
        
        # Normaliza e converte a coluna valor para float
        df['valor'] = df['valor'].apply(self.normalize_value)
        
        # Cria a coluna complemento com o formato especificado
        df['complemento'] = (df['NomeSingular'].fillna('') + " | " + 
                           df['DescricaoTipoRecebimento'].fillna('') + " | " + 
                           df['Descricao'].fillna(''))
        
        # Cria o DataFrame para exportação
        df_export = df[['Debito', 'Credito', 'Historico', 'DATA', 'valor', 'complemento']].copy()
        
        # Adiciona registros baseados na condição IRRF
        irrf_rows = []
        for index, row in df.iterrows():
            irrf_value = self.normalize_value(row['IRRF'])
            if irrf_value > 0:
                if row['Tipo'] == 'A pagar':
                    debito_irrf = df_export.iloc[index]['Credito']
                    credito_irrf = 23476
                    historico_irrf = 2341
                elif row['Tipo'] == 'A receber':
                    debito_irrf = 15456
                    credito_irrf = df_export.iloc[index]['Debito']
                    historico_irrf = 22
                
                irrf_rows.append({
                    'Debito': debito_irrf,
                    'Credito': credito_irrf,
                    'Historico': historico_irrf,
                    'DATA': self.last_day_of_previous_month,
                    'valor': irrf_value,
                    'complemento': (str(row['NomeSingular']) if pd.notnull(row['NomeSingular']) else '') + 
                                 " | " + (str(row['DescricaoTipoRecebimento']) if pd.notnull(row['DescricaoTipoRecebimento']) else '') +
                                 " | " + (str(row['Descricao']) if pd.notnull(row['Descricao']) else '') + " | IRRF"
                })
        
        # Adiciona as linhas de IRRF ao DataFrame de exportação
        if irrf_rows:
            df_export = pd.concat([df_export, pd.DataFrame(irrf_rows)], ignore_index=True)
        
        # Formata a coluna DATA para o formato brasileiro (dd/mm/yyyy)
        df_export['DATA'] = pd.to_datetime(df_export['DATA']).dt.strftime('%d/%m/%Y')
        
        # Preservar também as colunas originais de TipoSingular e CodigoTipoRecebimento para filtros
        df_export['TipoSingular'] = df['TipoSingular']
        df_export['CodigoTipoRecebimento'] = df['CodigoTipoRecebimento']
        df_export['Tipo'] = df['Tipo']
        
        return df_export
    
    def create_download_link(self, df, filename):
        """Cria um link para download do DataFrame como CSV."""
        csv_string = self.df_to_csv_string(df)
        b64 = base64.b64encode(csv_string.encode('utf-8')).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="download-button">Baixar {filename}</a>'
        return href
    
    def df_to_csv_string(self, df):
        """Converte DataFrame para string CSV no formato brasileiro."""
        csv_buffer = io.StringIO()
        
        # Cria uma cópia do dataframe para exportação, removendo colunas extras
        export_df = df.copy()
        if 'TipoSingular' in export_df.columns:
            export_df = export_df.drop(['TipoSingular', 'CodigoTipoRecebimento', 'Tipo'], axis=1, errors='ignore')
        
        # Escreve o cabeçalho
        csv_buffer.write(';'.join(export_df.columns) + '\n')
        
        # Escreve as linhas sem aspas
        for _, row in export_df.iterrows():
            line_values = []
            for col, val in row.items():
                # Formata valores numéricos com vírgula decimal
                if col == 'valor' and isinstance(val, (int, float)):
                    line_values.append(f"{val:.2f}".replace('.', ','))
                elif isinstance(val, (int, float)) and col not in ['Debito', 'Credito', 'Historico']:
                    line_values.append(str(val).replace('.', ','))
                else:
                    line_values.append(str(val))
            csv_buffer.write(';'.join(line_values) + '\n')
        
        return csv_buffer.getvalue()
    
    def process_csv_file(self, uploaded_file):
        """Processa um arquivo CSV carregado."""
        try:
            # Tenta ler o arquivo com diferentes encodings e separadores
            try:
                df = pd.read_csv(uploaded_file, sep=";", encoding='utf-8')
            except:
                try:
                    df = pd.read_csv(uploaded_file, sep=",", encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv(uploaded_file, sep=";", encoding='latin1')
                    except:
                        # Último recurso: tenta detectar o separador
                        uploaded_file.seek(0)
                        sample = uploaded_file.read(1024).decode('utf-8', errors='ignore')
                        if ',' in sample and ';' not in sample:
                            sep = ','
                        else:
                            sep = ';'
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, sep=sep, encoding='utf-8', on_bad_lines='skip')
            
            # Processa o DataFrame
            processed_df = self.process_dataframe(df)
            if processed_df is not None:
                self.processed_files.append(uploaded_file.name)
                return processed_df, df  # Retorna também o DataFrame original para uso nos relatórios
            else:
                self.error_files.append(uploaded_file.name)
                return None, None
        except Exception as e:
            self.error_files.append(uploaded_file.name)
            st.error(f"Erro ao processar o arquivo {uploaded_file.name}: {str(e)}")
            return None, None
    
    def generate_accounting_reports(self, df, output_dir=None, display_result=False):
        """
        Gera relatórios específicos solicitados pelo contador.
        
        Relatórios gerados:
        1. Taxas de Manutenção (3) - Para todas (operadoras e prestadoras)
        2. Taxas de Marketing (4) - Para todas
        3. Multas e Juros (5) - Para todas
        4. Outras (6) - Para todas
        5. Pré-pagamento (1) - Somente operadoras
        6. Custo Operacional (2) - Somente operadoras
        7. Pré-pagamento (1) - Somente prestadoras
        8. Custo Operacional (2) - Somente prestadoras
        """
        import tempfile
        
        # Usar diretório temporário se não for especificado
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        else:
            os.makedirs(output_dir, exist_ok=True)
        
        # Definir os relatórios a serem gerados
        reports_config = [
            {"name": "taxas_manutencao", "title": "Relatório de Taxas de Manutenção (3)", 
            "filters": {"CodigoTipoRecebimento": 3}},
            
            {"name": "taxas_marketing", "title": "Relatório de Taxas de Marketing (4)", 
            "filters": {"CodigoTipoRecebimento": 4}},
            
            {"name": "multas_juros", "title": "Relatório de Multas e Juros (5)", 
            "filters": {"CodigoTipoRecebimento": 5}},
            
            {"name": "outras", "title": "Relatório de Outras (6)", 
            "filters": {"CodigoTipoRecebimento": 6}},
            
            {"name": "pre_pagamento_operadoras", "title": "Relatório de Pré-pagamento (1) - Operadoras", 
            "filters": {"CodigoTipoRecebimento": 1, "TipoSingular": "Operadora"}},
            
            {"name": "custo_operacional_operadoras", "title": "Relatório de Custo Operacional (2) - Operadoras", 
            "filters": {"CodigoTipoRecebimento": 2, "TipoSingular": "Operadora"}},
            
            {"name": "pre_pagamento_prestadoras", "title": "Relatório de Pré-pagamento (1) - Prestadoras", 
            "filters": {"CodigoTipoRecebimento": 1, "TipoSingular": "Prestadora"}},
            
            {"name": "custo_operacional_prestadoras", "title": "Relatório de Custo Operacional (2) - Prestadoras", 
            "filters": {"CodigoTipoRecebimento": 2, "TipoSingular": "Prestadora"}}
        ]
        
        # Dicionário para armazenar resultados
        results = {}
        pdf_files = []
        csv_files = []

        # Configurar estilos para o PDF
        styles = getSampleStyleSheet()
        
        # Verificar se temos as colunas necessárias
        if 'CodigoTipoRecebimento' not in df.columns or 'TipoSingular' not in df.columns:
            raise ValueError("Colunas CodigoTipoRecebimento ou TipoSingular não encontradas no DataFrame")
        
        # Iterar sobre cada configuração de relatório
        for report_config in reports_config:
            # Filtrar os dados conforme os critérios
            filtered_df = df.copy()
            
            for key, value in report_config["filters"].items():
                filtered_df = filtered_df[filtered_df[key] == value]
            
            # Se não há dados para este relatório, continuar para o próximo
            if filtered_df.empty:
                if display_result:
                    st.warning(f"Nenhum dado encontrado para {report_config['title']}")
                results[report_config["name"]] = {"count": 0, "sum": 0, "file": None}
                continue
            
            # Nome do arquivo
            csv_file = os.path.join(output_dir, f"{report_config['name']}.csv")
            pdf_file = os.path.join(output_dir, f"{report_config['name']}.pdf")
            
            # Exportar para CSV
            self.export_to_csv(filtered_df, csv_file)
            
            # Adicionar descrições das contas contábeis
            filtered_df['Debito_Desc'] = filtered_df['Debito'].apply(
                lambda x: f"{x} - {NOMES_CONTAS_CONTABEIS.get(int(x), 'Descrição não encontrada')}" if pd.notnull(x) and str(x).isdigit() else "")
            
            filtered_df['Credito_Desc'] = filtered_df['Credito'].apply(
                lambda x: f"{x} - {NOMES_CONTAS_CONTABEIS.get(int(x), 'Descrição não encontrada')}" if pd.notnull(x) and str(x).isdigit() else "")
            
            filtered_df['Historico_Desc'] = filtered_df['Historico'].apply(
                lambda x: f"{x} - {NOMES_CONTAS_CONTABEIS.get(int(x), 'Descrição não encontrada')}" if pd.notnull(x) and str(x).isdigit() else "")
            
            # Gerar PDF com totalizações
            doc = SimpleDocTemplate(pdf_file, pagesize=landscape(letter), leftMargin=1*cm, rightMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
            elements = []
            
            # Título
            elements.append(Paragraph(report_config["title"], styles['Title']))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Dados do relatório
            date_str = filtered_df['DATA'].iloc[0] if not filtered_df.empty else ""
            elements.append(Paragraph(f"Data de referência: {date_str}", styles['Normal']))
            elements.append(Spacer(1, 0.15 * inch))
            
            # Totalizações
            record_count = len(filtered_df)
            total_value = filtered_df['valor'].sum()
            
            # Tabela de resumo
            summary_data = [
                ["Total de registros", str(record_count)],
                ["Valor total", f"R$ {total_value:.2f}".replace('.', ',')]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT')
            ]))
            
            elements.append(summary_table)
            elements.append(Spacer(1, 0.25 * inch))
            
            # Tabela com os registros
            # Selecionar e reordenar colunas para o relatório
            display_df = filtered_df[['DATA', 'complemento', 'valor', 'Debito_Desc', 'Credito_Desc', 'Historico_Desc']].copy()
            display_df.columns = ['Data', 'Complemento', 'Valor', 'Débito', 'Crédito', 'Histórico']
            
            # Converter para lista para o relatório PDF
            data = [display_df.columns.tolist()]
            for _, row in display_df.iterrows():
                row_data = []
                for i, (col, val) in enumerate(row.items()):
                    if col == 'Valor' and isinstance(val, (int, float)):
                        val = f"R$ {val:.2f}".replace('.', ',')
                    elif col == 'Complemento':
                        # Limitar o tamanho do complemento para caber na página
                        val = (str(val)[:40] + '...') if len(str(val)) > 40 else str(val)
                    elif col in ['Débito', 'Crédito']:
                        # Limitar descrições de contas para tamanho adequado
                        val = (str(val)[:40] + '...') if len(str(val)) > 40 else str(val)
                    row_data.append(str(val))
                data.append(row_data)
            
            # Adicionar linha de total no final
            total_row = ['', 'TOTAL', f"R$ {total_value:.2f}".replace('.', ','), '', '', '']
            data.append(total_row)
            
            # Criar tabela com larguras de coluna ajustadas
            col_widths = [0.8*inch, 2.0*inch, 0.8*inch, 2.2*inch, 2.2*inch, 1.0*inch]
            
            # Estilo da tabela - definir aqui antes de aplicar as classes
            table_style = TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Dados
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Data centralizada
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),   # Valor à direita
                
                # Linha de total
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (2, -1), (2, -1), 'RIGHT'),  # Total à direita
                
                # Borda
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                
                # Reduzir tamanho da fonte para dados
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                # Forçar word wrap e alinhamento vertical nas células
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ])

            # Criar tabela uma única vez
            table = Table(data, colWidths=col_widths, repeatRows=1)

            # Aplicar o estilo à tabela
            table.setStyle(table_style)
            elements.append(table)
            
            # Adicionar informações adicionais
            elements.append(Spacer(1, 0.5 * inch))
            elements.append(Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
            
            # Gerar o PDF
            doc.build(elements)
            
            # Armazenar os resultados
            results[report_config["name"]] = {
                "count": record_count,
                "sum": total_value,
                "file": pdf_file
            }
            
            pdf_files.append(pdf_file)
            csv_files.append(csv_file)
            
            if display_result:
                st.success(f"✅ Relatório gerado: {report_config['title']} - {record_count} registros, Total: R$ {total_value:.2f}")
        
        # Criar um relatório de resumo geral
        summary_file = os.path.join(output_dir, "resumo_relatorios.pdf")
        doc = SimpleDocTemplate(summary_file, pagesize=letter)
        elements = []
        
        # Título
        elements.append(Paragraph("Resumo dos Relatórios Contábeis", styles['Title']))
        elements.append(Spacer(1, 0.5 * inch))
        
        # Tabela de resumo
        summary_data = [["Relatório", "Registros", "Valor Total"]]
        total_overall = 0
        
        for report_config in reports_config:
            report_name = report_config["name"]
            if report_name in results:
                report_result = results[report_name]
                summary_data.append([
                    report_config["title"],
                    str(report_result["count"]),
                    f"R$ {report_result['sum']:.2f}".replace('.', ',')
                ])
                total_overall += report_result["sum"]
        
        # Adicionar linha de total geral
        summary_data.append(["TOTAL GERAL", "", f"R$ {total_overall:.2f}".replace('.', ',')])
        
        # Criar tabela
        summary_table = Table(summary_data, colWidths=[4*inch, 1*inch, 1.5*inch])
        
        # Estilo da tabela
        summary_style = TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Dados
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
            
            # Total geral
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            
            # Borda
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        summary_table.setStyle(summary_style)
        elements.append(summary_table)
        
        # Adicionar informações adicionais
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(f"Resumo gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        
        # Gerar o PDF de resumo
        doc.build(elements)
        pdf_files.append(summary_file)
        
        if display_result:
            st.success(f"✅ Resumo geral gerado: {summary_file}")
        
        # Criar arquivo ZIP com todos os relatórios
        zip_file = os.path.join(output_dir, "relatorios_contabeis.zip")
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Adicionar todos os PDFs
            for pdf_file in pdf_files:
                zipf.write(pdf_file, os.path.basename(pdf_file))
            
            # Adicionar todos os CSVs
            for csv_file in csv_files:
                zipf.write(csv_file, os.path.basename(csv_file))
        
        # Retornar informações sobre os relatórios e o arquivo ZIP
        return {
            "reports": results,
            "summary_file": summary_file,
            "zip_file": zip_file
        }

    def export_to_csv(self, df, filename):
        """Exporta o DataFrame para um arquivo CSV."""
        csv_content = self.df_to_csv_string(df)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        return filename

def main():
    st.title("Processador de Arquivos CSV da Câmara de Compensação")
    
    # Adiciona CSS personalizado
    st.markdown("""
        <style>
            /* Configurações existentes */
            .download-button {
                display: inline-block;
                padding: 0.5em 1em;
                background-color: #4CAF50;
                color: white;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                border-radius: 4px;
                transition: background-color 0.3s;
                margin: 10px 0;
            }
            .download-button:hover {
                background-color: #45a049;
            }
            .file-header {
                margin-top: 20px;
                padding: 10px;
                background-color: #f0f2f6;
                border-radius: 5px;
            }
            .stAlert {
                margin-top: 10px;
            }
            .report-box {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 10px;
            }
            .report-header {
                font-weight: bold;
                margin-bottom: 10px;
                color: #2C3E50;
            }
            .report-metrics {
                display: flex;
                gap: 20px;
            }
            .metric {
                background-color: #e8f4f8;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
            }
            .metric-value {
                font-size: 1.2em;
                font-weight: bold;
            }
            
            /* Formatação da tabela de relatórios - AJUSTADO */
            table {
                width: 100%;
                table-layout: fixed;
                border-collapse: collapse;
                font-size: 10pt;
            }
            td, th {
                font-family: Arial, sans-serif;
                padding: 3px;
                border: 1px solid #ddd;
                overflow: hidden;
            }
            td {
                word-wrap: break-word;
                white-space: normal;
                text-overflow: ellipsis;
                vertical-align: middle;
                max-width: 0; /* Força texto a quebrar */
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
                text-align: center;
            }
            
            /* Classes específicas para colunas - AJUSTADO */
            .col-data { width: 8%; }
            .col-complemento { width: 20%; } /* Reduzido para dar mais espaço a outras colunas */
            .col-valor { width: 8%; }
            .col-debito { width: 28%; } /* Aumentado para acomodar textos longos */
            .col-credito { width: 28%; } /* Aumentado para acomodar textos longos */
            .col-historico { width: 8%; }
        </style>
        """, unsafe_allow_html=True)
    
    st.write("""
    Este aplicativo processa arquivos CSV da câmara de compensação de singulares do Neodonto.
    Arraste e solte os arquivos CSV para processá-los conforme as regras estabelecidas.
    """)
    
    processor = NeodontoCsvProcessor()
    
    # Criando abas principais
    tab1, tab2 = st.tabs(["Processamento de Arquivos", "Relatórios Contábeis"])
    
    with tab1:
        # Opção para configurar manualmente a data
        custom_date = st.checkbox("Definir data manualmente")
        if custom_date:
            selected_date = st.date_input(
                "Selecione a data a ser usada (último dia do mês de referência)",
                value=processor.last_day_of_previous_month
            )
            processor.last_day_of_previous_month = selected_date
        
        # Opções avançadas em um expansor
        with st.expander("Opções avançadas"):
            st.write("Configurações de processamento:")
            
            # Opção para mostrar mais linhas na prévia
            preview_rows = st.slider("Número de linhas na prévia", min_value=3, max_value=20, value=5)
            
            # Opção para processar todos os arquivos em lote
            batch_process = st.checkbox("Processar todos os arquivos em lote", value=False)
            
            # Opção para baixar todos os arquivos processados em um ZIP
            download_zip = st.checkbox("Baixar todos os arquivos em um único ZIP", value=False)
        
        # Upload de arquivos CSV
        uploaded_files = st.file_uploader(
            "Arraste e solte os arquivos CSV aqui", 
            type=["csv"], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            # Barra de progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Processamento dos arquivos
            processed_dfs = {}
            original_dfs = {}
            total_files = len(uploaded_files)
            
            # Se processar em lote, mostrar apenas barra de progresso
            if batch_process:
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processando arquivo {i+1} de {total_files}: {uploaded_file.name}")
                    progress_bar.progress((i) / total_files)
                    
                    # Processamento do arquivo
                    processed_df, original_df = processor.process_csv_file(uploaded_file)
                    if processed_df is not None:
                        processed_dfs[uploaded_file.name] = processed_df
                        original_dfs[uploaded_file.name] = original_df
                    
                    progress_bar.progress((i+1) / total_files)
                
                # Resumo do processamento em lote
                st.write("## Resumo do processamento")
                st.write(f"Total de arquivos: {total_files}")
                st.write(f"Arquivos processados com sucesso: {len(processed_dfs)}")
                st.write(f"Arquivos com erro: {total_files - len(processed_dfs)}")
                
                # Download individual
                st.write("## Download dos arquivos processados")
                for filename, df in processed_dfs.items():
                    output_filename = f"contabil_{filename}"
                    download_link = processor.create_download_link(df, output_filename)
                    st.markdown(download_link, unsafe_allow_html=True)
                
                # Se opção de ZIP selecionada, gerar download ZIP
                if download_zip and processed_dfs:
                    try:
                        import zipfile
                        from io import BytesIO
                        
                        # Criar arquivo ZIP em memória
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for filename, df in processed_dfs.items():
                                # Converter DataFrame para CSV em string
                                csv_content = processor.df_to_csv_string(df)
                                # Adicionar ao ZIP
                                zip_file.writestr(f"contabil_{filename}", csv_content.encode('utf-8'))
                        
                        # Criar link de download para o ZIP
                        zip_buffer.seek(0)
                        b64 = base64.b64encode(zip_buffer.read()).decode()
                        href = f'<a href="data:application/zip;base64,{b64}" download="contabil_todos_arquivos.zip" class="download-button">Baixar todos os arquivos em ZIP</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Erro ao criar arquivo ZIP: {str(e)}")
            
            # Se não for processamento em lote, mostrar detalhes de cada arquivo
            else:
                st.write("## Arquivos processados")
                
                for i, uploaded_file in enumerate(uploaded_files):
                    progress_bar.progress((i) / total_files)
                    status_text.text(f"Processando arquivo {i+1} de {total_files}")
                    
                    st.markdown(f"<div class='file-header'><h3>Arquivo: {uploaded_file.name}</h3></div>", unsafe_allow_html=True)
                    
                    # Processamento do arquivo
                    processed_df, original_df = processor.process_csv_file(uploaded_file)
                    
                    if processed_df is not None:
                        # Salvar também o DataFrame original
                        processed_dfs[uploaded_file.name] = processed_df
                        original_dfs[uploaded_file.name] = original_df
                        
                        # Exibe uma prévia dos dados processados
                        st.write("Prévia dos dados processados:")
                        st.dataframe(processed_df.head(preview_rows))
                        
                        # Estatísticas básicas
                        st.write("Resumo do processamento:")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total de registros", len(processed_df))
                        with col2:
                            # Conta registros de IRRF (adicionais)
                            original_rows = len(processed_df) - sum(1 for _, row in processed_df.iterrows() 
                                                                 if row['Historico'] in [22, 2341])
                            st.metric("Registros originais", original_rows)
                        with col3:
                            irrf_rows = sum(1 for _, row in processed_df.iterrows() 
                                          if row['Historico'] in [22, 2341])
                            st.metric("Registros IRRF adicionados", irrf_rows)
                        
                        # Cria nome do arquivo de saída
                        output_filename = f"contabil_{uploaded_file.name}"
                        
                        # Cria link de download
                        download_link = processor.create_download_link(processed_df, output_filename)
                        st.markdown(download_link, unsafe_allow_html=True)
                    else:
                        st.error(f"Não foi possível processar o arquivo {uploaded_file.name}")
                    
                    # Adiciona separador visual
                    st.markdown("---")
                    
                    # Atualiza a barra de progresso
                    progress_bar.progress((i+1) / total_files)
                
                # Se opção de ZIP selecionada, gerar download ZIP
                if download_zip and processed_dfs:
                    try:
                        import zipfile
                        from io import BytesIO
                        
                        # Criar arquivo ZIP em memória
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for filename, df in processed_dfs.items():
                                # Converter DataFrame para CSV em string
                                csv_content = processor.df_to_csv_string(df)
                                # Adicionar ao ZIP
                                zip_file.writestr(f"contabil_{filename}", csv_content.encode('utf-8'))
                        
                        # Criar link de download para o ZIP
                        zip_buffer.seek(0)
                        b64 = base64.b64encode(zip_buffer.read()).decode()
                        st.markdown("<h3>Download em lote</h3>", unsafe_allow_html=True)
                        href = f'<a href="data:application/zip;base64,{b64}" download="contabil_todos_arquivos.zip" class="download-button">Baixar todos os arquivos em ZIP</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Erro ao criar arquivo ZIP: {str(e)}")
                
                # Finaliza a barra de progresso
                progress_bar.progress(1.0)
                status_text.text("Processamento concluído!")
            
            # Armazenar os DataFrames processados na sessão para uso na aba de relatórios
            st.session_state.processed_dfs = processed_dfs
            st.session_state.original_dfs = original_dfs
    
    with tab2:
        st.header("Relatórios Contábeis")
        
        if 'processed_dfs' not in st.session_state or not st.session_state.processed_dfs:
            st.info("Processe arquivos na aba 'Processamento de Arquivos' para gerar relatórios contábeis.")
        else:
            st.write("Selecione os arquivos para gerar relatórios contábeis:")
            
            # Mostrar lista de arquivos processados para seleção
            processed_files = list(st.session_state.processed_dfs.keys())
            selected_files = st.multiselect("Arquivos disponíveis", processed_files, default=processed_files)
            
            if selected_files:
                # Opção para processar todos os relatórios ou apenas alguns específicos
                report_options = st.radio(
                    "Escolha os relatórios a serem gerados:",
                    ["Todos os relatórios solicitados pelo contador", "Relatórios específicos"]
                )
                
                if report_options == "Relatórios específicos":
                    # Lista de relatórios disponíveis
                    report_types = [
                        {"name": "taxas_manutencao", "title": "Taxas de Manutenção (3) - Para todas"},
                        {"name": "taxas_marketing", "title": "Taxas de Marketing (4) - Para todas"},
                        {"name": "multas_juros", "title": "Multas e Juros (5) - Para todas"},
                        {"name": "outras", "title": "Outras (6) - Para todas"},
                        {"name": "pre_pagamento_operadoras", "title": "Pré-pagamento (1) - Operadoras"},
                        {"name": "custo_operacional_operadoras", "title": "Custo Operacional (2) - Operadoras"},
                        {"name": "pre_pagamento_prestadoras", "title": "Pré-pagamento (1) - Prestadoras"},
                        {"name": "custo_operacional_prestadoras", "title": "Custo Operacional (2) - Prestadoras"}
                    ]
                    
                    selected_reports = st.multiselect(
                        "Selecione os relatórios específicos a serem gerados:",
                        options=[report["title"] for report in report_types],
                        default=[report["title"] for report in report_types]
                    )
                    
                    # Mapear títulos selecionados para nomes de relatórios
                    report_name_to_title = {report["name"]: report["title"] for report in report_types}
                    title_to_report_name = {report["title"]: report["name"] for report in report_types}
                    
                    # Filtrar reports_config com base nos relatórios selecionados
                    selected_report_names = [title_to_report_name[title] for title in selected_reports]
                else:
                    # Todos os relatórios selecionados
                    selected_report_names = None
                
                if st.button("Gerar Relatórios Contábeis"):
                    # Criar diretório temporário para os relatórios
                    import tempfile
                    output_dir = tempfile.mkdtemp()
                    
                    # Consolidar DataFrames selecionados
                    dfs_to_process = [st.session_state.processed_dfs[filename] for filename in selected_files]
                    consolidated_df = pd.concat(dfs_to_process, ignore_index=True)
                    
                    st.write(f"Gerando relatórios contábeis a partir de {len(consolidated_df)} registros...")
                    
                    # Mostrar barra de progresso
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    status_text.text("Processando relatórios contábeis...")
                    
                    try:
                        # Gerar relatórios contábeis
                        report_results = processor.generate_accounting_reports(consolidated_df, output_dir, display_result=False)
                        
                        # Criar link de download para o ZIP com todos os relatórios
                        if "zip_file" in report_results and os.path.exists(report_results["zip_file"]):
                            with open(report_results["zip_file"], "rb") as f:
                                zip_data = f.read()
                                b64 = base64.b64encode(zip_data).decode()
                                href = f'<a href="data:application/zip;base64,{b64}" download="relatorios_contabeis.zip" class="download-button">Baixar todos os relatórios (ZIP)</a>'
                                st.markdown(href, unsafe_allow_html=True)
                        
                        # Exibir resultados dos relatórios
                        st.write("## Resumo dos Relatórios Gerados")
                        
                        # Calcular total geral
                        total_overall = sum(result["sum"] for _, result in report_results["reports"].items() if result["file"] is not None)
                        st.metric("Total Geral", f"R$ {total_overall:.2f}")
                        
                        # Exibir detalhes de cada relatório
                        for report_name, result in report_results["reports"].items():
                            if result["file"] is not None and result["count"] > 0:
                                st.markdown(f"<div class='report-box'>", unsafe_allow_html=True)
                                st.markdown(f"<div class='report-header'>{report_name.replace('_', ' ').title()}</div>", unsafe_allow_html=True)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"<div class='metric'><div>Registros</div><div class='metric-value'>{result['count']}</div></div>", unsafe_allow_html=True)
                                with col2:
                                    st.markdown(f"<div class='metric'><div>Valor Total</div><div class='metric-value'>R$ {result['sum']:.2f}</div></div>", unsafe_allow_html=True)
                                
                                # Link para download do relatório específico
                                if os.path.exists(result["file"]):
                                    with open(result["file"], "rb") as f:
                                        pdf_data = f.read()
                                        b64 = base64.b64encode(pdf_data).decode()
                                        href = f'<a href="data:application/pdf;base64,{b64}" download="{os.path.basename(result["file"])}" target="_blank">Visualizar PDF</a>'
                                        st.markdown(href, unsafe_allow_html=True)
                                
                                st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Concluir barra de progresso
                        progress_bar.progress(1.0)
                        status_text.text("Processamento concluído!")
                        st.success("✅ Relatórios contábeis gerados com sucesso!")
                    
                    except Exception as e:
                        st.error(f"Erro ao gerar relatórios contábeis: {str(e)}")
    
    # Adiciona informações de rodapé
    st.markdown("---")
    with st.expander("Informações sobre o processamento"):
        st.write("""
        ### Regras de processamento
        
        O processamento segue estas etapas:
        
        1. **Criação de colunas**:
           - Debito: Código contábil para débito
           - Credito: Código contábil para crédito
           - Historico: Código do histórico padrão
           - DATA: Último dia do mês anterior (ou data selecionada manualmente)
           - valor: Valor bruto da operação
           - complemento: Concatenação de NomeSingular, DescricaoTipoRecebimento e Descricao
        
        2. **Processamento de IRRF**:
           - Para cada linha com IRRF > 0, cria uma nova linha com as contas contábeis apropriadas
           - Para "A pagar", o débito é o crédito original e o crédito é 23476
           - Para "A receber", o débito é 15456 e o crédito é o débito original
        
        3. **Formatação**:
           - Valores numéricos com vírgula como separador decimal
           - Data no formato dd/mm/yyyy
        """)
        
        st.write("""
        ### Relatórios Contábeis Disponíveis
        
        1. **Taxas de Manutenção (3)** - Para todas (operadoras e prestadoras)
        2. **Taxas de Marketing (4)** - Para todas (operadoras e prestadoras)
        3. **Multas e Juros (5)** - Para todas (operadoras e prestadoras)
        4. **Outras (6)** - Para todas (operadoras e prestadoras)
        5. **Pré-pagamento (1)** - Somente operadoras
        6. **Custo Operacional (2)** - Somente operadoras
        7. **Pré-pagamento (1)** - Somente prestadoras
        8. **Custo Operacional (2)** - Somente prestadoras
        
        Cada relatório inclui o total de registros, o valor total e uma listagem detalhada com as descrições das contas contábeis.
        """)

if __name__ == "__main__":
    main()
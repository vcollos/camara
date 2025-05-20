import pandas as pd
import streamlit as st
import io
import base64
from datetime import datetime, timedelta
import os
import numpy as np
import re

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
        nome_singular = str(row['NomeSingular']).upper() if pd.notnull(row['NomeSingular']) else ""
        
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
                                 " | " + (str(row['Descricao']) if pd.notnull(row['Descricao']) else '')
                })
        
        # Adiciona as linhas de IRRF ao DataFrame de exportação
        if irrf_rows:
            df_export = pd.concat([df_export, pd.DataFrame(irrf_rows)], ignore_index=True)
        
        # Formata a coluna DATA para o formato brasileiro (dd/mm/yyyy)
        df_export['DATA'] = pd.to_datetime(df_export['DATA']).dt.strftime('%d/%m/%Y')
        
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
        
        # Escreve o cabeçalho
        csv_buffer.write(';'.join(df.columns) + '\n')
        
        # Escreve as linhas sem aspas
        for _, row in df.iterrows():
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
                        df = pd.read_csv(uploaded_file, sep=sep, encoding='utf-8', error_bad_lines=False)
            
            # Processa o DataFrame
            processed_df = self.process_dataframe(df)
            if processed_df is not None:
                self.processed_files.append(uploaded_file.name)
                return processed_df
            else:
                self.error_files.append(uploaded_file.name)
                return None
        except Exception as e:
            self.error_files.append(uploaded_file.name)
            st.error(f"Erro ao processar o arquivo {uploaded_file.name}: {str(e)}")
            return None

def main():
    st.set_page_config(
        page_title="Processador de CSV Neodonto",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("Processador de Arquivos CSV da Câmara de Compensação")
    
    # Adiciona CSS personalizado
    st.markdown("""
    <style>
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
    </style>
    """, unsafe_allow_html=True)
    
    st.write("""
    Este aplicativo processa arquivos CSV da câmara de compensação de singulares do Neodonto.
    Arraste e solte os arquivos CSV para processá-los conforme as regras estabelecidas.
    """)
    
    processor = NeodontoCsvProcessor()
    
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
        total_files = len(uploaded_files)
        
        # Se processar em lote, mostrar apenas barra de progresso
        if batch_process:
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processando arquivo {i+1} de {total_files}: {uploaded_file.name}")
                progress_bar.progress((i) / total_files)
                
                # Processamento do arquivo
                processed_df = processor.process_csv_file(uploaded_file)
                if processed_df is not None:
                    processed_dfs[uploaded_file.name] = processed_df
                
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
                processed_df = processor.process_csv_file(uploaded_file)
                
                if processed_df is not None:
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
                    
                    # Salva o DataFrame processado para o ZIP (se necessário)
                    processed_dfs[uploaded_file.name] = processed_df
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
        ### Mapeamento de códigos contábeis
        
        #### Para registros "A pagar":
        - **Operadoras**:
          - Repasse em Pré-pagamento (1): Débito 31731, Crédito 90918
          - Repasse em Custo Operacional (2): Débito 40507, Crédito 90919
          - Taxa de Manutenção (3): 
            - UNIODONTO DO BRASIL: Débito 52631, Crédito 21898
            - Outras: Débito 52632, Crédito 22036
          - Fundo de Marketing (4): 
            - UNIODONTO DO BRASIL: Débito 52532, Crédito 21898
            - Outras: Débito 52532, Crédito 22036
          - Fundo de Reserva (5): Débito 51818, Crédito 51818
          - Outros (6): Débito 51202, Crédito 90919
        
        - **Prestadoras**:
          - Repasse em Pré-pagamento/Custo Operacional (1,2): Débito 40140, Crédito 92003
          - Taxa de Manutenção (3): 
            - UNIODONTO DO BRASIL: Débito 52631, Crédito 21898
            - Outras: Débito 52632, Crédito 22036
          - Fundo de Marketing (4): 
            - UNIODONTO DO BRASIL: Débito 52532, Crédito 21898
            - Outras: Débito 52532, Crédito 22036
          - Fundo de Reserva (5): Débito 51818, Crédito 51818
          - Outros (6): Débito 51202, Crédito 90919
        
        #### Para registros "A receber":
        - **Operadoras**:
          - Repasse em Pré-pagamento (1): Débito 19958, Crédito 30203
          - Repasse em Custo Operacional (2): Débito 85433, Crédito 40413
          - Taxa de Manutenção (3): Débito 84679, Crédito 30069
          - Fundo de Marketing (4): Débito 84679, Crédito 30071
          - Fundo de Reserva (5): Débito 84679, Crédito 31426
          - Outros (6): Débito 19253, Crédito 30127
        
        - **Prestadoras**:
          - Repasse em Pré-pagamento (1): Débito 19253, Crédito 30203
          - Repasse em Custo Operacional (2): Débito 19253, Crédito 40413
          - Taxa de Manutenção (3): Débito 84679, Crédito 30069
          - Fundo de Marketing (4): Débito 84679, Crédito 30071
          - Fundo de Reserva (5): Débito 84679, Crédito 31426
          - Outros (6): Débito 19253, Crédito 30127
        
        #### Códigos de Histórico:
        - A pagar, tipos 1, 2, 6: 2005
        - A pagar, tipo 3: 
          - UNIODONTO DO BRASIL: 361
          - Outras: 368
        - A pagar, tipo 4: 365
        - A pagar, tipo 5: 179
        - A receber, tipos 1, 2, 6: 1021
        - A receber, tipo 3: 33
        - A receber, tipo 4: 228
        - A receber, tipo 5: 30

        #### Para registros IRRF:
        - A pagar: Débito = Crédito da linha original, Crédito = 23476, Histórico = 2341
        - A receber: Débito = 15456, Crédito = Débito da linha original, Histórico = 22
        """)
        
        st.write("""
        ### Contexto do projeto
        
        Este aplicativo processa os dados da Câmara de Compensação do Sistema Uniodonto para facilitar a troca de valores financeiros entre as Cooperativas Uniodonto.
        
        A Câmara de Compensação funciona como uma conta corrente onde as Uniodontos registram os serviços prestados umas às outras para fins de pagamento. Os valores são processados e aceitos pela cooperativa devedora (dona do relatório), que também registra seus próprios valores.
        
        Ao final, são calculados os saldos de quem deve para quem e os pagamentos são processados. Paralelamente, o sistema gera os lançamentos contábeis de todas as movimentações e pagamentos que a Uniodonto dona do relatório realizou.
        """)

if __name__ == "__main__":
    main()                
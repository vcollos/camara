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
from reportlab.lib.pagesizes import letter
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
        
        # Mapeamento oficial CodigoTipoRecebimento <-> DescricaoTipoRecebimento
        self.codigo_descricao_map = {
            1: "Repasse em Pré-pagamento",
            2: "Repasse em Custo Operacional", 
            3: "Taxa de Manutenção",
            4: "Fundo de Marketing",
            5: "Juros",
            6: "Outros"
        }
        
        # Mapeamento reverso para sincronização
        self.descricao_codigo_map = {v: k for k, v in self.codigo_descricao_map.items()}
    
    def sync_codigo_descricao(self, df):
        """
        Sincroniza CodigoTipoRecebimento e DescricaoTipoRecebimento para garantir consistência.
        Prioriza o CodigoTipoRecebimento como fonte da verdade.
        """
        inconsistencias = []
        
        for idx, row in df.iterrows():
            codigo = row.get('CodigoTipoRecebimento')
            descricao = row.get('DescricaoTipoRecebimento', '').strip()
            
            # Verificar se o código é válido
            if codigo in self.codigo_descricao_map:
                descricao_esperada = self.codigo_descricao_map[codigo]
                
                # Se a descrição não bate com o código, corrigir
                if descricao != descricao_esperada:
                    inconsistencias.append({
                        'index': idx,
                        'NomeSingular': row.get('NomeSingular', 'N/A'),
                        'codigo': codigo,
                        'descricao_atual': descricao,
                        'descricao_correta': descricao_esperada
                    })
                    
                    # Corrigir a descrição baseada no código
                    df.at[idx, 'DescricaoTipoRecebimento'] = descricao_esperada
            else:
                # Código inválido - tentar corrigir baseado na descrição
                if descricao in self.descricao_codigo_map:
                    codigo_correto = self.descricao_codigo_map[descricao]
                    inconsistencias.append({
                        'index': idx,
                        'NomeSingular': row.get('NomeSingular', 'N/A'),
                        'codigo': codigo,
                        'codigo_correto': codigo_correto,
                        'descricao_atual': descricao
                    })
                    
                    # Corrigir o código baseado na descrição
                    df.at[idx, 'CodigoTipoRecebimento'] = codigo_correto
                else:
                    # Nem código nem descrição são válidos - usar padrão
                    inconsistencias.append({
                        'index': idx,
                        'NomeSingular': row.get('NomeSingular', 'N/A'),
                        'codigo': codigo,
                        'descricao_atual': descricao,
                        'acao': 'Definido como "Outros" (código 6)'
                    })
                    
                    df.at[idx, 'CodigoTipoRecebimento'] = 6
                    df.at[idx, 'DescricaoTipoRecebimento'] = "Outros"
        
        # Reportar inconsistências corrigidas
        if inconsistencias:
            st.warning(f"🔄 **SINCRONIZAÇÃO**: {len(inconsistencias)} inconsistências entre Código e Descrição foram corrigidas automaticamente")
            
            with st.expander("Ver detalhes das correções"):
                for inc in inconsistencias:
                    if 'descricao_correta' in inc:
                        st.write(f"• **{inc['NomeSingular']}**: Código {inc['codigo']} → Descrição corrigida para '{inc['descricao_correta']}'")
                    elif 'codigo_correto' in inc:
                        st.write(f"• **{inc['NomeSingular']}**: Descrição '{inc['descricao_atual']}' → Código corrigido para {inc['codigo_correto']}")
                    else:
                        st.write(f"• **{inc['NomeSingular']}**: {inc['acao']}")
        
        return df
    
    def calculate_debit(self, row):
        """Calcula o valor de débito baseado nas condições específicas."""
        tipo = row['Tipo']
        tipo_singular = row['TipoSingular']
        codigo_tipo_recebimento = row['CodigoTipoRecebimento']
        nome_singular = str(row['NomeSingular']).upper() if pd.notnull(row['NomeSingular']) else ""
        descricao = str(row['Descricao']).upper() if pd.notnull(row['Descricao']) else ""
        
        # Novas regras para convenção
        if "CONVENCAO" in descricao or "CONVENÇÃO" in descricao:
            if tipo == 'A pagar':
                return 53742
            elif tipo == 'A receber':
                return 84679

        # Regras especiais para CodigoTipoRecebimento 5
        if codigo_tipo_recebimento == 5:
            if tipo == 'A receber':
                if "LGPD" in descricao or "ATUARIO" in descricao or "ATUÁRIO" in descricao:
                    return 84679
            else:  # A pagar
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
        
        # Novas regras para convenção
        if "CONVENCAO" in descricao or "CONVENÇÃO" in descricao:
            if tipo == 'A pagar':
                if "PAULISTA" in descricao:
                    return 22036
                else:
                    return 21898
            elif tipo == 'A receber':
                if "PAULISTA" in descricao:
                    return 19265
                else:
                    return 11021

        # Regras especiais para CodigoTipoRecebimento 5
        if codigo_tipo_recebimento == 5:
            if tipo == 'A receber':
                if "LGPD" in descricao:
                    return 30173
                elif "ATUARIO" in descricao or "ATUÁRIO" in descricao:
                    return 30088
            else:  # A pagar
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
        """Calcula o histórico baseado nas condições específicas."""
        tipo = row['Tipo']
        tipo_singular = row['TipoSingular']
        codigo_tipo_recebimento = row['CodigoTipoRecebimento']
        nome_singular = str(row['NomeSingular']).upper() if pd.notnull(row['NomeSingular']) else ""
        descricao = str(row['Descricao']).upper() if pd.notnull(row['Descricao']) else ""
        
        # Novas regras para convenção
        if "CONVENCAO" in descricao or "CONVENÇÃO" in descricao:
            if tipo == 'A pagar':
                return 2005
            elif tipo == 'A receber':
                return 1021

        # Regras especiais para CodigoTipoRecebimento 5
        if codigo_tipo_recebimento == 5:
            if tipo == 'A receber':
                if "LGPD" in descricao or "ATUARIO" in descricao or "ATUÁRIO" in descricao:
                    return 1021
            else:  # A pagar
                if "LGPD" in descricao or "ATUARIO" in descricao or "ATUÁRIO" in descricao:
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
        """Normaliza um valor para formato numérico, tratando adequadamente valores monetários."""
        if pd.isna(value) or value == '':
            return 0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        # Converter para string para processamento
        value_str = str(value).strip()
        
        # Se o valor está vazio após strip
        if not value_str:
            return 0
            
        # Detectar formato monetário brasileiro (com vírgula como decimal)
        # Ex: "1.234,56" ou "234,56" ou "1234,56"
        if ',' in value_str and value_str.count(',') == 1:
            # Verificar se é formato brasileiro (vírgula decimal)
            partes = value_str.split(',')
            if len(partes) == 2 and len(partes[1]) <= 2 and partes[1].isdigit():
                # É formato brasileiro (vírgula decimal)
                parte_inteira = re.sub(r'[^\d]', '', partes[0])  # Remove pontos de milhares
                parte_decimal = partes[1]
                if parte_inteira == '':
                    parte_inteira = '0'
                try:
                    return float(f"{parte_inteira}.{parte_decimal}")
                except ValueError:
                    pass
        
        # Para outros casos, remover caracteres não numéricos exceto ponto e vírgula
        value_str = re.sub(r'[^\d.,]', '', value_str)
        
        # Se não há dígitos, retornar 0
        if not re.search(r'\d', value_str):
            return 0
        
        # Detectar se é valor em formato americano (ponto como decimal)
        if '.' in value_str and ',' in value_str:
            # Formato com separadores de milhares e decimal
            # Ex: "1,234.56" (americano) ou "1.234,56" (brasileiro)
            if value_str.rfind('.') > value_str.rfind(','):
                # Ponto vem depois da vírgula = formato americano
                value_str = value_str.replace(',', '')  # Remove separador de milhares
            else:
                # Vírgula vem depois do ponto = formato brasileiro
                value_str = value_str.replace('.', '')  # Remove separador de milhares
                value_str = value_str.replace(',', '.')  # Converte decimal
        elif ',' in value_str:
            # Apenas vírgula - assumir como decimal brasileiro
        
            value_str = value_str.replace(",", ".")
        try:
            result = float(value_str)
            # Verificação de sanidade: se o valor for muito grande (mais de 1 milhão), 
            # pode ter havido conversão incorreta
            if result > 1000000:
                # Verificar se o valor original tinha formato monetário
                original_str = str(value).strip()
                if ',' in original_str and len(original_str.split(',')[-1]) <= 2:
                    # Pode ter sido convertido incorretamente
                    # Tentar dividir por 100
                    potential_correct = result / 100
                    if potential_correct < 10000:  # Valor mais razoável
                        return potential_correct
            
            return result
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

        # PROTEÇÃO: Criar backup dos valores originais do CodigoTipoRecebimento
        df_original_backup = df.copy()
        original_codigo_tipo = df['CodigoTipoRecebimento'].copy()
        
        st.info("🔒 **PROTEÇÃO ATIVADA**: Valores originais de CodigoTipoRecebimento foram preservados")

        # Converte CodigoTipoRecebimento para inteiro
        try:
            df['CodigoTipoRecebimento'] = pd.to_numeric(df['CodigoTipoRecebimento'], errors='coerce').fillna(6).astype(int)
            
            # VERIFICAÇÃO: Comparar se houve alterações não autorizadas
            try:
                original_codigo_int = pd.to_numeric(original_codigo_tipo, errors='coerce').fillna(6).astype(int)
                if not df['CodigoTipoRecebimento'].equals(original_codigo_int):
                    alteracoes = df[df['CodigoTipoRecebimento'] != original_codigo_int]
                    if len(alteracoes) > 0:
                        st.warning(f"⚠️ **ATENÇÃO**: {len(alteracoes)} registros tiveram CodigoTipoRecebimento alterado durante a conversão numérica!")
                        st.write("Registros afetados:")
                        st.dataframe(alteracoes[['NomeSingular', 'Descricao', 'CodigoTipoRecebimento']])
            except Exception as e:
                st.info(f"Aviso na verificação de alterações: {str(e)}")
                    
        except Exception as e:
            st.warning(f"Aviso ao converter CodigoTipoRecebimento: {str(e)}. Tentando continuar o processamento.")

        # SINCRONIZAÇÃO: Garantir consistência entre Código e Descrição
        df = self.sync_codigo_descricao(df)

        # Aplica as funções para criar as colunas necessárias
        df['Debito'] = df.apply(self.calculate_debit, axis=1)
        df['Credito'] = df.apply(self.calculate_credit, axis=1)
        df['Historico'] = df.apply(self.calculate_history, axis=1)
        
        # Adiciona a coluna DATA com o último dia do mês anterior
        df['DATA'] = self.last_day_of_previous_month
        
        # Adiciona a coluna valor com os dados de ValorBruto
        df['valor'] = df['ValorBruto']
        
        # PROTEÇÃO EXTRA: Preservar valores originais de ValorBruto para evitar conversões incorretas
        original_valor_bruto = df['ValorBruto'].copy()
        
        # Normaliza e converte a coluna valor para float
        df['valor'] = df['valor'].apply(self.normalize_value)
        
        # VERIFICAÇÃO: Detectar valores convertidos incorretamente (muito grandes)
        problematic_values = df[df['valor'] > 100000]  # Valores maiores que 100k são suspeitos
        if len(problematic_values) > 0:
            st.warning(f"⚠️ **ATENÇÃO**: {len(problematic_values)} valores parecem ter sido convertidos incorretamente (muito grandes)")
            
            # Tentar corrigir valores problemáticos
            for idx in problematic_values.index:
                original_val = original_valor_bruto.iloc[idx]
                converted_val = df.loc[idx, 'valor']
                
                # Se o valor original era uma string com vírgula como decimal
                if isinstance(original_val, str) and ',' in str(original_val):
                    # Tentar reconverter usando lógica mais cuidadosa
                    corrected_val = self.normalize_value(original_val)
                    
                    # Se ainda está muito grande, tentar dividir por 100
                    if corrected_val > 10000:
                        corrected_val = corrected_val / 100
                    
                    df.loc[idx, 'valor'] = corrected_val
                    st.info(f"🔧 Valor corrigido: {original_val} → {corrected_val} (era {converted_val})")
                elif converted_val > 10000:
                    # Para valores numéricos muito grandes, tentar dividir por 100
                    corrected_val = converted_val / 100
                    df.loc[idx, 'valor'] = corrected_val
                    st.info(f"🔧 Valor corrigido: {converted_val} → {corrected_val}")
        
        # Cria a coluna complemento com o formato especificado + tipo
        df['complemento'] = (df['NomeSingular'].fillna('') + " | " + 
                           df['DescricaoTipoRecebimento'].fillna('') + " | " + 
                           df['Descricao'].fillna('') + " | " + 
                           df['Tipo'].fillna(''))
        
        # AJUSTE PROVISÓRIO: Verificação de inconsistências na conciliação da câmara
        # Quando CodigoTipoRecebimento = 2, DescricaoTipoRecebimento = "Repasse em Custo Operacional"
        # e Descrição contém "Mensalidade" ou "Mensalidades"
        # IMPORTANTE: Esta regra NÃO altera o CodigoTipoRecebimento, apenas marca como inconsistente
        def verificar_inconsistencia(row):
            if (row['CodigoTipoRecebimento'] == 2 and 
                str(row['DescricaoTipoRecebimento']).strip() == 'Repasse em Custo Operacional' and
                ('mensalidade' in str(row['Descricao']).lower() or 'mensalidades' in str(row['Descricao']).lower())):
                return "*** Lançamento Inconsistente, verifique | " + str(row['complemento'])
            else:
                return row['complemento']
        
        # Aplicar a verificação de inconsistência
        df['complemento'] = df.apply(verificar_inconsistencia, axis=1)
        
        # VERIFICAÇÃO FINAL: Garantir que CodigoTipoRecebimento não foi alterado
        try:
            final_codigo_tipo = df['CodigoTipoRecebimento'].copy()
            original_codigo_int = pd.to_numeric(original_codigo_tipo, errors='coerce').fillna(6).astype(int)
            
            if not final_codigo_tipo.equals(original_codigo_int):
                alteracoes_finais = df[df['CodigoTipoRecebimento'] != original_codigo_int]
                if len(alteracoes_finais) > 0:
                    st.error(f"🚨 **ERRO CRÍTICO**: {len(alteracoes_finais)} registros tiveram CodigoTipoRecebimento alterado sem autorização!")
                    st.write("**Registros com alterações não autorizadas:**")
                    for idx, row in alteracoes_finais.iterrows():
                        original_val = original_codigo_int.iloc[idx]
                        new_val = row['CodigoTipoRecebimento']
                        st.write(f"- {row['NomeSingular']}: {original_val} → {new_val} (Descrição: {row['Descricao']})")
                    
                    # Restaurar valores originais
                    df['CodigoTipoRecebimento'] = original_codigo_int
                    st.success("✅ **VALORES RESTAURADOS**: CodigoTipoRecebimento foi restaurado aos valores originais")
        except Exception as e:
            st.info(f"Aviso na verificação final: {str(e)}")
        
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
                                 " | " + (str(row['Descricao']) if pd.notnull(row['Descricao']) else '') + 
                                 " | " + (str(row['Tipo']) if pd.notnull(row['Tipo']) else '') + " | IRRF"
                })
        
        # Adiciona as linhas de IRRF ao DataFrame de exportação
        if irrf_rows:
            df_export = pd.concat([df_export, pd.DataFrame(irrf_rows)], ignore_index=True)
        
        # Formata a coluna DATA para o formato brasileiro (dd/mm/yyyy)
        df_export['DATA'] = pd.to_datetime(df_export['DATA']).dt.strftime('%d/%m/%Y')
        
        # Preservar também as colunas originais para filtros
        if 'TipoSingular' in df.columns:
            df_export['TipoSingular'] = df['TipoSingular']
        if 'CodigoTipoRecebimento' in df.columns:
            df_export['CodigoTipoRecebimento'] = df['CodigoTipoRecebimento']
        if 'Tipo' in df.columns:
            df_export['Tipo'] = df['Tipo']
        if 'NomeSingular' in df.columns:
            df_export['NomeSingular'] = df['NomeSingular']
        if 'DescricaoTipoRecebimento' in df.columns:
            df_export['DescricaoTipoRecebimento'] = df['DescricaoTipoRecebimento']
        if 'Descricao' in df.columns:
            df_export['Descricao'] = df['Descricao']
        if 'ValorBruto' in df.columns:
            df_export['ValorBruto'] = df['ValorBruto']
        if 'IRRF' in df.columns:
            df_export['IRRF'] = df['IRRF']
        
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
        
        # Cria uma cópia do dataframe para exportação
        export_df = df.copy()
        
        # Para arquivos contábeis, filtrar apenas as 6 colunas específicas
        if all(col in export_df.columns for col in ['Debito', 'Credito', 'Historico', 'DATA', 'valor', 'complemento']):
            # Arquivo contábil: apenas as 6 colunas específicas
            export_df = export_df[['Debito', 'Credito', 'Historico', 'DATA', 'valor', 'complemento']].copy()
            
            # Renomear DATA para data
            export_df = export_df.rename(columns={'DATA': 'data'})
            
            # Recriar o campo complemento com dados atualizados
            if all(col in df.columns for col in ['NomeSingular', 'DescricaoTipoRecebimento', 'Descricao']):
                # Verificar se existe flag de IRRF no complemento
                irrf_mask = export_df['complemento'].str.contains('IRRF', na=False)
                
                # Para registros normais, recriar o complemento
                normal_mask = ~irrf_mask
                if normal_mask.any():
                    # Mapear os índices corretos
                    for idx in export_df[normal_mask].index:
                        if idx < len(df):
                            original_row = df.iloc[idx]
                            nome = str(original_row['NomeSingular']) if pd.notnull(original_row['NomeSingular']) else ''
                            desc_tipo = str(original_row['DescricaoTipoRecebimento']) if pd.notnull(original_row['DescricaoTipoRecebimento']) else ''
                            desc = str(original_row['Descricao']) if pd.notnull(original_row['Descricao']) else ''
                            
                            # Verificar inconsistências
                            if (original_row.get('CodigoTipoRecebimento') == 2 and 
                                str(original_row.get('DescricaoTipoRecebimento', '')).strip() == 'Repasse em Custo Operacional' and
                                ('mensalidade' in str(original_row.get('Descricao', '')).lower() or 'mensalidades' in str(original_row.get('Descricao', '')).lower())):
                                tipo = str(original_row.get('Tipo', '')) if pd.notnull(original_row.get('Tipo')) else ''
                                export_df.at[idx, 'complemento'] = f"*** Lançamento Inconsistente, verifique | {nome} | {desc_tipo} | {desc} | {tipo}"
                            else:
                                tipo = str(original_row.get('Tipo', '')) if pd.notnull(original_row.get('Tipo')) else ''
                                export_df.at[idx, 'complemento'] = f"{nome} | {desc_tipo} | {desc} | {tipo}"
        else:
            # Arquivo original: remover apenas colunas extras de controle
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
    
    def create_default_columns(self, df):
        """Cria colunas padrão quando estão ausentes."""
        # Colunas obrigatórias com valores padrão
        default_values = {
            'Tipo': 'A receber',  # Valor padrão
            'CodigoSingular': 0,
            'NomeSingular': 'Não informado',
            'TipoSingular': 'Operadora',  # Valor padrão mais comum
            'CodigoTipoRecebimento': 6,  # Outras
            'DescricaoTipoRecebimento': 'Outras',
            'ValorBruto': 0.0,
            'IRRF': 0.0,
            'Descricao': 'Importado automaticamente'
        }
        
        # Adicionar colunas ausentes com valores padrão
        for col, default_val in default_values.items():
            if col not in df.columns:
                df[col] = default_val
                st.warning(f"⚠️ Coluna '{col}' não encontrada. Usando valor padrão: {default_val}")
        
        return df
    
    def detect_simplified_format(self, df):
        """Detecta formato simplificado de relatório financeiro."""
        available_columns = df.columns.tolist()
        
        # Verificar se é o formato simplificado (com colunas como Vencimento, Código, Nome, etc.)
        simplified_indicators = [
            'Vencimento' in available_columns,
            'Código' in available_columns,
            'Nome' in available_columns,
            'Tipo' in available_columns,
            any('Valor a Receber' in col or 'Valor a Pagar' in col for col in available_columns)
        ]
        
        if sum(simplified_indicators) >= 4:
            st.info("📋 **Formato Simplificado Detectado**")
            st.info("Este arquivo parece ser um relatório financeiro simplificado. Convertendo para o formato da Câmara de Compensação...")
            
            # Criar DataFrame mapeado para o formato da Câmara
            df_mapped = df.copy()
            
            # Mapeamentos básicos
            column_mapping = {}
            if 'Nome' in available_columns:
                column_mapping['Nome'] = 'NomeSingular'
            if 'Código' in available_columns:
                column_mapping['Código'] = 'CodigoSingular'
            if 'Tipo' in available_columns:
                column_mapping['Tipo'] = 'Tipo'
            
            # Aplicar mapeamentos
            df_mapped = df_mapped.rename(columns=column_mapping)
            
            # Determinar o valor bruto baseado no tipo
            if 'Valor a Receber' in available_columns and 'Valor a Pagar' in available_columns:
                def calculate_valor_bruto(row):
                    valor_receber = self.normalize_value(row.get('Valor a Receber', 0))
                    valor_pagar = self.normalize_value(row.get('Valor a Pagar', 0))
                    return valor_receber if valor_receber > 0 else valor_pagar
                
                df_mapped['ValorBruto'] = df.apply(calculate_valor_bruto, axis=1)
            
            # Criar colunas padrão necessárias
            default_values = {
                'TipoSingular': 'Operadora',
                'CodigoTipoRecebimento': 6,  # Outras
                'DescricaoTipoRecebimento': 'Outras',
                'IRRF': 0.0,
                'Descricao': 'Importado de relatório simplificado'
            }
            
            for col, default_val in default_values.items():
                if col not in df_mapped.columns:
                    df_mapped[col] = default_val
            
            # Ajustar tipo baseado nos valores
            if 'Valor a Receber' in available_columns and 'Valor a Pagar' in available_columns:
                def determine_tipo(row):
                    valor_receber = self.normalize_value(row.get('Valor a Receber', 0))
                    valor_pagar = self.normalize_value(row.get('Valor a Pagar', 0))
                    return 'A receber' if valor_receber > 0 else 'A pagar'
                
                df_mapped['Tipo'] = df.apply(determine_tipo, axis=1)
            
            return df_mapped, "✅ Formato simplificado convertido para Câmara de Compensação"
        
        return None, "Não é formato simplificado"
    
    def detect_csv_format(self, df):
        """Detecta o formato do CSV e tenta mapear as colunas."""
        # Colunas esperadas pelo sistema
        expected_columns = [
            'Tipo', 'CodigoSingular', 'NomeSingular', 'TipoSingular', 
            'CodigoTipoRecebimento', 'DescricaoTipoRecebimento', 
            'ValorBruto', 'IRRF', 'Descricao'
        ]
        
        # Verificar se já está no formato correto
        if all(col in df.columns for col in expected_columns):
            return df, "Formato padrão da Câmara de Compensação detectado"
        
        # Colunas disponíveis no arquivo
        available_columns = df.columns.tolist()
        
        # Primeiro, tentar detectar formato simplificado
        simplified_result, simplified_message = self.detect_simplified_format(df)
        if simplified_result is not None:
            return simplified_result, simplified_message
        
        # Verificar se é um arquivo da Câmara de Compensação válido
        # Deve ter pelo menos algumas colunas essenciais
        essential_indicators = [
            any('tipo' in col.lower() for col in available_columns),
            any('singular' in col.lower() for col in available_columns),
            any('valor' in col.lower() for col in available_columns),
            any('recebimento' in col.lower() for col in available_columns)
        ]
        
        # Se não tem pelo menos 2 indicadores essenciais, não é arquivo da Câmara
        if sum(essential_indicators) < 2:
            return None, f"""
            ❌ ARQUIVO NÃO COMPATÍVEL COM CÂMARA DE COMPENSAÇÃO
            
            Este arquivo não parece ser um CSV da Câmara de Compensação Uniodonto.
            
            📋 Formato esperado deve conter colunas como:
            • Tipo (A pagar/A receber)
            • NomeSingular (Nome da cooperativa)
            • CodigoTipoRecebimento (1-6)
            • ValorBruto (Valor da transação)
            • IRRF (Imposto retido)
            
            📁 Colunas encontradas no seu arquivo:
            {', '.join(available_columns)}
            
            💡 Verifique se está usando o arquivo correto da Câmara de Compensação.
            """
        
        # Tentar mapear colunas similares
        column_mapping = {}
        
        # Mapeamentos possíveis para arquivos da Câmara
        possible_mappings = {
            'Tipo': ['tipo', 'Type', 'TIPO'],
            'CodigoSingular': ['codigo_singular', 'codigo singular', 'CodSingular', 'CODIGO_SINGULAR'],
            'NomeSingular': ['nome_singular', 'nome singular', 'NomeSing', 'NOME_SINGULAR', 'Nome'],
            'TipoSingular': ['tipo_singular', 'tipo singular', 'TipoSing', 'TIPO_SINGULAR'],
            'CodigoTipoRecebimento': ['codigo_tipo_recebimento', 'cod_tipo_receb', 'CodTipoReceb', 'CODIGO_TIPO_RECEBIMENTO'],
            'DescricaoTipoRecebimento': ['descricao_tipo_recebimento', 'desc_tipo_receb', 'DescTipoReceb', 'DESCRICAO_TIPO_RECEBIMENTO'],
            'ValorBruto': ['valor_bruto', 'valor bruto', 'Valor', 'VALOR_BRUTO', 'ValorTotal'],
            'IRRF': ['irrf', 'ir', 'IR', 'ImpostoRenda'],
            'Descricao': ['descricao', 'desc', 'Desc', 'DESCRICAO', 'Observacao']
        }
        
        # Tentar encontrar correspondências
        for expected_col, possible_names in possible_mappings.items():
            for possible_name in possible_names:
                if possible_name in available_columns:
                    column_mapping[possible_name] = expected_col
                    break
        
        # Se encontrou mapeamentos suficientes, aplicar
        if len(column_mapping) >= 5:  # Pelo menos 5 colunas mapeadas
            df_mapped = df.rename(columns=column_mapping)
            
            # Verificar se ainda faltam colunas após o mapeamento
            missing_after_mapping = [col for col in expected_columns if col not in df_mapped.columns]
            
            if missing_after_mapping:
                # Só criar colunas padrão se for um número pequeno de colunas ausentes
                if len(missing_after_mapping) <= 3:
                    df_mapped = self.create_default_columns(df_mapped)
                    return df_mapped, f"✅ Mapeamento aplicado: {column_mapping}. Colunas padrão criadas para: {', '.join(missing_after_mapping)}"
                else:
                    return None, f"❌ Muitas colunas ausentes após mapeamento: {', '.join(missing_after_mapping)}"
            
            return df_mapped, f"✅ Mapeamento aplicado com sucesso: {column_mapping}"
        
        # Se não conseguiu mapear suficientemente, retornar erro detalhado
        return None, f"""
        ❌ FORMATO NÃO RECONHECIDO
        
        Não foi possível mapear as colunas automaticamente.
        
        📁 Colunas disponíveis no arquivo:
        {', '.join(available_columns)}
        
        📋 Colunas esperadas pela Câmara de Compensação:
        {', '.join(expected_columns)}
        
        💡 Verifique se o arquivo está no formato correto ou renomeie as colunas conforme necessário.
        """
    
    def show_file_preview(self, df, filename):
        """Mostra uma prévia do arquivo para o usuário confirmar."""
        st.write(f"### Prévia do arquivo: {filename}")
        
        # Informações básicas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de linhas", len(df))
        with col2:
            st.metric("Total de colunas", len(df.columns))
        with col3:
            # Verificar se tem valores numéricos
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            st.metric("Colunas numéricas", len(numeric_cols))
        
        # Mostrar colunas disponíveis
        st.write("**Colunas disponíveis:**")
        st.write(", ".join(df.columns.tolist()))
        
        # Mostrar primeiras linhas
        st.write("**Primeiras 5 linhas:**")
        st.dataframe(df.head())
        
        # Verificar se tem dados que parecem valores monetários
        potential_value_columns = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['valor', 'value', 'preco', 'price', 'montante', 'amount']):
                potential_value_columns.append(col)
        
        if potential_value_columns:
            st.write(f"**Colunas que podem conter valores:** {', '.join(potential_value_columns)}")
        
        return True
    
    def process_csv_file(self, uploaded_file):
        """Processa um arquivo CSV carregado."""
        try:
            # Lista de encodings para tentar
            encodings = ['utf-8', 'latin1', 'iso-8859-1', 'windows-1252', 'cp1252']
            separators = [';', ',']
            
            # Tenta diferentes combinações de encoding e separador
            for encoding in encodings:
                for sep in separators:
                    try:
                        uploaded_file.seek(0)  # Volta ao início do arquivo
                        df = pd.read_csv(uploaded_file, sep=sep, encoding=encoding)
                        # Se chegou aqui, conseguiu ler o arquivo
                        break
                    except:
                        continue
                else:
                    continue
                break
            else:
                # Se nenhuma combinação funcionou, tenta detectar o separador
                uploaded_file.seek(0)
                sample = uploaded_file.read(1024).decode('utf-8', errors='ignore')
                sep = ',' if ',' in sample and ';' not in sample else ';'
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=sep, encoding='utf-8', on_bad_lines='skip')
            
            # Processa o DataFrame
            mapped_df, mapping_info = self.detect_csv_format(df)
            if mapped_df is not None:
                # Exibir informação sobre o mapeamento
                if "Mapeamento aplicado" in mapping_info:
                    st.info(f"✅ {mapping_info}")
                elif "Formato padrão" in mapping_info:
                    st.success(f"✅ {mapping_info}")
                
                # Processar o DataFrame mapeado
                processed_df = self.process_dataframe(mapped_df)
                if processed_df is not None:
                    self.processed_files.append(uploaded_file.name)
                    return processed_df, mapped_df  # Retorna também o DataFrame original mapeado
                else:
                    self.error_files.append(uploaded_file.name)
                    return None, None
            else:
                # Erro no mapeamento
                self.error_files.append(uploaded_file.name)
                st.error(f"❌ {mapping_info}")
                return None, None
        except Exception as e:
            self.error_files.append(uploaded_file.name)
            st.error(f"Erro ao processar o arquivo {uploaded_file.name}: {str(e)}")
            return None, None
    
    def debug_report_data(self, df, report_name):
        """Função de debug para verificar dados dos relatórios."""
        st.write(f"### Debug - {report_name}")
        
        # Verificar colunas disponíveis
        st.write("**Colunas disponíveis:**", list(df.columns))
        
        # Verificar valores únicos em colunas importantes
        if 'CodigoTipoRecebimento' in df.columns:
            st.write("**Códigos de tipo de recebimento:**", sorted(df['CodigoTipoRecebimento'].unique()))
        
        if 'TipoSingular' in df.columns:
            st.write("**Tipos de singular:**", sorted(df['TipoSingular'].unique()))
        
        if 'Tipo' in df.columns:
            st.write("**Tipos:**", sorted(df['Tipo'].unique()))
        
        # Mostrar primeiras linhas
        st.write("**Primeiras 3 linhas:**")
        st.dataframe(df.head(3))
        
        st.write("---")

    def generate_accounting_reports(self, df, output_dir=None, display_result=False, debug=False):
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
        
        # Definir os relatórios a serem gerados - CORRIGIDO
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
        
        # Criar estilo personalizado para células da tabela
        cell_style = styles['Normal'].clone('CellStyle')
        cell_style.fontSize = 7
        cell_style.leading = 9
        cell_style.alignment = 0  # Alinhamento à esquerda
        cell_style.wordWrap = 'CJK'
        
        # Verificar se temos as colunas necessárias
        required_columns = ['CodigoTipoRecebimento', 'TipoSingular', 'Tipo', 'DATA', 'valor', 'complemento', 'Debito', 'Credito', 'Historico']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colunas ausentes no DataFrame: {', '.join(missing_columns)}")
        
        # Iterar sobre cada configuração de relatório
        for report_config in reports_config:
            # Filtrar os dados conforme os critérios
            filtered_df = df.copy()
            
            # Debug se solicitado
            if debug:
                self.debug_report_data(filtered_df, f"Antes do filtro - {report_config['title']}")
            
            for key, value in report_config["filters"].items():
                if key in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df[key] == value]
                else:
                    if display_result:
                        st.warning(f"Coluna {key} não encontrada para o relatório {report_config['title']}")
                    continue
            
            # Debug após filtros se solicitado
            if debug:
                self.debug_report_data(filtered_df, f"Após filtros - {report_config['title']}")
            
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
            doc = SimpleDocTemplate(pdf_file, pagesize=letter, leftMargin=1.2*cm, rightMargin=1.2*cm, topMargin=1.2*cm, bottomMargin=1.2*cm)
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
            
            summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch])
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
                        # Usar função auxiliar para quebra inteligente de linhas
                        val_str = str(val)
                        complemento_formatado = self.truncate_lines(val_str, max_chars_per_line=40, max_lines=3)
                        val = Paragraph(complemento_formatado, cell_style)
                    elif col in ['Débito', 'Crédito']:
                        # Quebrar descrições de contas em linhas
                        val_str = str(val)
                        if len(val_str) > 50:
                            # Quebrar na primeira quebra natural (hífen ou espaço)
                            if ' - ' in val_str:
                                parts = val_str.split(' - ', 1)
                                if len(parts) == 2:
                                    text_content = f"{parts[0]}<br/>{parts[1][:30]}{'...' if len(parts[1]) > 30 else ''}"
                                else:
                                    text_content = val_str[:50] + '...'
                            else:
                                # Quebrar por palavras
                                words = val_str.split()
                                line1 = ""
                                line2 = ""
                                for word in words:
                                    if len(line1 + " " + word) <= 25:
                                        line1 += " " + word if line1 else word
                                    elif len(line2 + " " + word) <= 25:
                                        line2 += " " + word if line2 else word
                                    else:
                                        break
                                text_content = f"{line1}<br/>{line2}{'...' if len(' '.join(words)) > len(line1 + line2) else ''}"
                            val = Paragraph(text_content, cell_style)
                        else:
                            val = Paragraph(val_str, cell_style)
                    elif col == 'Histórico':
                        # Histórico pode ser mais compacto
                        val_str = str(val)
                        if len(val_str) > 25:
                            val = Paragraph(val_str[:22] + '...', cell_style)
                        else:
                            val = Paragraph(val_str, cell_style)
                    else:
                        val = str(val)
                    
                    row_data.append(val)
                data.append(row_data)
            
            # Adicionar linha de total no final
            total_row = ['', 'TOTAL', f"R$ {total_value:.2f}".replace('.', ','), '', '', '']
            data.append(total_row)
            
            # Criar tabela com larguras de coluna otimizadas para retrato A4
            col_widths = [0.6*inch, 1.8*inch, 0.7*inch, 1.4*inch, 1.4*inch, 0.8*inch]
            
            # Estilo da tabela melhorado
            table_style = TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                
                # Dados
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Data centralizada
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),   # Valor à direita
                
                # Linha de total
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 8),
                ('ALIGN', (2, -1), (2, -1), 'RIGHT'),  # Total à direita
                
                # Borda
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                
                # Alinhamento vertical
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                
                # Padding interno das células
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                
                # Altura mínima das linhas para acomodar texto quebrado
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
            ])

            # Criar tabela com configurações melhoradas
            table = Table(data, colWidths=col_widths, repeatRows=1, splitByRow=True, rowHeights=None)

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
        
        # Criar tabela (ajustada para formato retrato A4)
        summary_table = Table(summary_data, colWidths=[3*inch, 0.8*inch, 1.2*inch])
        
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

    def truncate_lines(self, text, max_chars_per_line=55, max_lines=3):
        """
        Divide o texto em linhas com quebra inteligente por palavras.
        
        Args:
            text: Texto a ser formatado
            max_chars_per_line: Máximo de caracteres por linha
            max_lines: Máximo de linhas permitidas
            
        Returns:
            String formatada com <br/> para uso em Paragraph
        """
        if not text or pd.isna(text):
            return ""
        
        text_str = str(text).strip()
        if not text_str:
            return ""
        
        # Se o texto é curto, retornar como está
        if len(text_str) <= max_chars_per_line:
            return text_str
        
        # Dividir por palavras
        words = text_str.split()
        lines = []
        current_line = ""
        
        for word in words:
            # Verificar se adicionando a palavra ultrapassaria o limite
            test_line = current_line + " " + word if current_line else word
            
            if len(test_line) <= max_chars_per_line:
                current_line = test_line
            else:
                # Se a linha atual não está vazia, adicionar às linhas
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # Palavra muito longa, forçar quebra
                    lines.append(word)
                    current_line = ""
        
        # Adicionar última linha se não estiver vazia
        if current_line:
            lines.append(current_line)
        
        # Limitar ao número máximo de linhas
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            # Adicionar "..." na última linha se necessário
            if lines:
                last_line = lines[-1]
                if len(last_line) + 3 <= max_chars_per_line:
                    lines[-1] = last_line + "..."
                else:
                    # Truncar a última linha para dar espaço ao "..."
                    lines[-1] = last_line[:max_chars_per_line-3] + "..."
        
        # Juntar com <br/> para ReportLab
        return "<br/>".join(lines)

    def format_currency(self, value):
        """Formata valor monetário com separador de milhares."""
        if pd.isna(value) or value == 0:
            return "0,00"
        
        # Converter para float se necessário
        if isinstance(value, str):
            value = self.normalize_value(value)
        
        # Formatar com separador de milhares
        formatted = f"{value:,.2f}"
        # Trocar ponto por vírgula e vírgula por ponto (padrão brasileiro)
        formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        return formatted

    def generate_unified_report(self, df, output_dir=None, display_result=False):
        """
        Gera um relatório simples: CSV convertido em PDF + página de resumo.
        """
        import tempfile
        
        # Usar diretório temporário se não for especificado
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        else:
            os.makedirs(output_dir, exist_ok=True)
        
        # Verificar se temos as colunas necessárias
        required_columns = ['Tipo', 'DATA', 'valor', 'complemento', 'Debito', 'Credito', 'Historico']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colunas ausentes no DataFrame: {', '.join(missing_columns)}")
        
        # Calcular IRRF usando a nova função que pega dos dados originais
        irrf_info = self.calculate_irrf_from_original_data(df)
        
        # Usar valores calculados da função
        valor_bruto_a_pagar = irrf_info['valor_bruto_a_pagar']
        valor_bruto_a_receber = irrf_info['valor_bruto_a_receber']
        valor_liquido_a_pagar = irrf_info['valor_liquido_a_pagar']
        valor_liquido_a_receber = irrf_info['valor_liquido_a_receber']
        saldo_liquido = valor_liquido_a_receber - valor_liquido_a_pagar
        saldo_bruto = valor_bruto_a_receber - valor_bruto_a_pagar
        
        # Contar registros (filtrar apenas registros originais, não lançamentos de IRRF)
        mask_nao_irrf = ~self.is_irrf_record(df)
        df_a_pagar_bruto = df[(df['Tipo'] == 'A pagar') & mask_nao_irrf]
        df_a_receber_bruto = df[(df['Tipo'] == 'A receber') & mask_nao_irrf]
        
        # Configurar estilos para o PDF
        styles = getSampleStyleSheet()
        
        # Criar estilo personalizado para células da tabela
        cell_style = styles['Normal'].clone('CellStyle')
        cell_style.fontSize = 7
        cell_style.leading = 9
        cell_style.alignment = 0
        cell_style.wordWrap = 'CJK'
        
        # Nome do arquivo
        pdf_file = os.path.join(output_dir, "relatorio_camara_compensacao.pdf")
        
        # Gerar PDF
        doc = SimpleDocTemplate(pdf_file, pagesize=letter, 
                              leftMargin=1.2*cm, rightMargin=1.2*cm, 
                              topMargin=1.2*cm, bottomMargin=1.2*cm)
        elements = []
        
        # Função para criar tabela simples do CSV
        def create_csv_table(data_df, section_title):
            section_elements = []
            
            if data_df.empty:
                section_elements.append(Paragraph(f"{section_title} - Nenhum registro encontrado", styles['Heading2']))
                return section_elements, 0, 0
            
            # Título da seção
            section_elements.append(Paragraph(section_title, styles['Heading2']))
            section_elements.append(Spacer(1, 0.1 * inch))
            
            # Preparar dados para a tabela (formato CSV simples)
            table_data = [['Data', 'Complemento', 'Valor Bruto', 'IRRF', 'Valor Líquido', 'Débito', 'Crédito', 'Histórico']]
            
            total_bruto = 0
            total_irrf = 0
            total_liquido = 0
            
            for _, row in data_df.iterrows():
                # Verificar se é registro de IRRF (lançamento adicional)
                is_irrf_lancamento = self.is_irrf_record(pd.DataFrame([row]))
                
                if is_irrf_lancamento.iloc[0]:
                    # Para lançamentos de IRRF, o valor é o próprio IRRF
                    valor_bruto = 0
                    irrf = row['valor']
                    valor_liquido = 0
                else:
                    # Para registros originais
                    valor_bruto = row['valor']
                    # IRRF vem da coluna IRRF original (se disponível)
                    irrf = 0
                    if 'IRRF' in row and pd.notnull(row.get('IRRF', 0)):
                        irrf = self.normalize_value(row['IRRF'])
                    valor_liquido = valor_bruto - irrf
                
                # Acumular totais
                total_bruto += valor_bruto
                total_irrf += irrf
                total_liquido += valor_liquido
                
                # Formatar complemento com quebra de linha otimizada
                complemento_texto = str(row['complemento'])
                # Usar função auxiliar para quebra inteligente de linhas
                complemento_formatado = self.truncate_lines(complemento_texto, max_chars_per_line=55, max_lines=3)
                complemento = Paragraph(complemento_formatado, cell_style)
                
                # Adicionar linha à tabela
                table_data.append([
                    row['DATA'],
                    complemento,
                    self.format_currency(valor_bruto),
                    self.format_currency(irrf),
                    self.format_currency(valor_liquido),
                    str(row['Debito']),
                    str(row['Credito']),
                    str(row['Historico'])
                ])
            
            # Totais removidos - já estão no resumo da primeira página
            
            # Configurar larguras das colunas (ajustadas para formato retrato A4)
            col_widths = [0.6*inch, 3.2*inch, 0.7*inch, 0.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.6*inch]
            
            # Criar tabela com suporte a quebra de linha
            table = Table(table_data, colWidths=col_widths, repeatRows=1, splitByRow=True)
            
            # Estilo da tabela com suporte a quebra de linha
            table_style = TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                
                # Dados
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Data centralizada
                ('ALIGN', (2, 1), (4, -1), 'RIGHT'),   # Valores à direita
                ('ALIGN', (5, 1), (-1, -1), 'CENTER'), # Códigos centralizados
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),   # Alinhamento vertical superior
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                
                # Bordas simples
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                
                # Padding ajustado para texto com quebra
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                
                # Alternância de cores nas linhas para melhor legibilidade
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ])
            
            table.setStyle(table_style)
            section_elements.append(table)
            section_elements.append(Spacer(1, 0.2 * inch))
            
            return section_elements, total_liquido, total_irrf

    # Removido método truncate_lines conforme solicitado
        
        # PÁGINA 1: RESUMO EXECUTIVO
        elements.append(Paragraph("RELATÓRIO DA CÂMARA DE COMPENSAÇÃO", styles['Title']))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Calcular totais para o resumo
        total_a_pagar_liquido = valor_liquido_a_pagar
        total_a_receber_liquido = valor_liquido_a_receber
        total_irrf_a_pagar = irrf_info['irrf_a_pagar']
        total_irrf_a_receber = irrf_info['irrf_a_receber']
        
        # Separar dados por tipo para exibição
        df_a_pagar = df[df['Tipo'] == 'A pagar'].copy()
        df_a_receber = df[df['Tipo'] == 'A receber'].copy()
        
        # Data de referência
        date_str = df['DATA'].iloc[0] if not df.empty else ""
        elements.append(Paragraph(f"Data de referência: {date_str}", styles['Normal']))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Tabela de resumo executivo atualizada
        resumo_data = [
            ['RESUMO EXECUTIVO', '', '', '', ''],
            ['Categoria', 'Registros', 'Valor Bruto', 'IRRF', 'Valor Líquido'],
            ['A Pagar', str(len(df_a_pagar_bruto)), 
             self.format_currency(valor_bruto_a_pagar), 
             self.format_currency(irrf_info['irrf_a_pagar']),
             self.format_currency(valor_liquido_a_pagar)],
            ['A Receber', str(len(df_a_receber_bruto)), 
             self.format_currency(valor_bruto_a_receber), 
             self.format_currency(irrf_info['irrf_a_receber']),
             self.format_currency(valor_liquido_a_receber)],
            ['', '', '', '', ''],
            ['SALDO BRUTO', '', self.format_currency(saldo_bruto), '', ''],
            ['SALDO LÍQUIDO', '', '', '', self.format_currency(saldo_liquido)]
        ]
        
        resumo_table = Table(resumo_data, colWidths=[1.5*inch, 0.8*inch, 1*inch, 0.8*inch, 1*inch])
        
        resumo_style = TableStyle([
            # Título
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            
            # Cabeçalho
            ('BACKGROUND', (0, 1), (-1, 1), colors.grey),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.whitesmoke),
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 9),
            
            # Dados
            ('BACKGROUND', (0, 2), (-1, 4), colors.white),
            ('ALIGN', (1, 2), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 2), (-1, 4), 9),
            
            # Saldo
            ('BACKGROUND', (0, 5), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, 5), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 5), (-1, -1), 10),
            ('ALIGN', (4, 5), (4, -1), 'RIGHT'),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        
        resumo_table.setStyle(resumo_style)
        elements.append(resumo_table)
        
        # PÁGINA 2: DETALHAMENTO A PAGAR
        from reportlab.platypus import PageBreak
        elements.append(PageBreak())
        
        a_pagar_elements, _, _ = create_csv_table(df[df['Tipo'] == 'A pagar'], "DETALHAMENTO - A PAGAR")
        elements.extend(a_pagar_elements)
        
        # PÁGINA 3: DETALHAMENTO A RECEBER
        elements.append(PageBreak())
        
        a_receber_elements, _, _ = create_csv_table(df[df['Tipo'] == 'A receber'], "DETALHAMENTO - A RECEBER")
        elements.extend(a_receber_elements)
        
        # Informações finais
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        
        # Gerar o PDF
        doc.build(elements)
        
        if display_result:
            st.success(f"✅ Relatório unificado gerado com sucesso!")
            st.info(f"📊 A Pagar: {len(df_a_pagar_bruto)} registros - {self.format_currency(valor_liquido_a_pagar)}")
            st.info(f"📈 A Receber: {len(df_a_receber_bruto)} registros - {self.format_currency(valor_liquido_a_receber)}")
            st.info(f"🧾 IRRF Total: {self.format_currency(irrf_info['total_irrf'])} (A Pagar: {self.format_currency(irrf_info['irrf_a_pagar'])}, A Receber: {self.format_currency(irrf_info['irrf_a_receber'])})")
            st.info(f"💰 Saldo Bruto: {self.format_currency(saldo_bruto)}")
            st.info(f"💰 Saldo Líquido: {self.format_currency(saldo_liquido)}")
        
        return {
            "pdf_file": pdf_file,
            "total_a_pagar": valor_liquido_a_pagar,
            "total_a_receber": valor_liquido_a_receber,
            "count_a_pagar": len(df_a_pagar_bruto),
            "count_a_receber": len(df_a_receber_bruto),
            "saldo": saldo_liquido,
            "irrf_info": irrf_info,
            "valor_bruto_a_pagar": valor_bruto_a_pagar,
            "valor_bruto_a_receber": valor_bruto_a_receber,
            "saldo_bruto": saldo_bruto
        }

    def generate_irrf_report(self, df, output_dir=None, display_result=False):
        """
        Gera relatório específico de IRRF (Imposto de Renda Retido na Fonte).
        """
        import tempfile
        
        # Usar diretório temporário se não for especificado
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        else:
            os.makedirs(output_dir, exist_ok=True)
        
        # Calcular IRRF usando a nova função de dados originais
        irrf_info = self.calculate_irrf_from_original_data(df)
        
        if irrf_info['total_irrf'] == 0:
            if display_result:
                st.warning("Nenhum registro com IRRF encontrado nos dados originais.")
            return None
        
        # Filtrar apenas registros que têm IRRF > 0 nos dados originais
        mask_nao_irrf = ~self.is_irrf_record(df)
        df_original = df[mask_nao_irrf].copy()
        
        if 'IRRF' in df_original.columns:
            df_original['IRRF_normalizado'] = df_original['IRRF'].apply(self.normalize_value)
            df_irrf = df_original[df_original['IRRF_normalizado'] > 0].copy()
        else:
            df_irrf = pd.DataFrame()
        
        # Configurar estilos para o PDF
        styles = getSampleStyleSheet()
        
        # Criar estilo personalizado para células da tabela
        cell_style = styles['Normal'].clone('CellStyle')
        cell_style.fontSize = 8
        cell_style.leading = 10
        cell_style.alignment = 0
        cell_style.wordWrap = 'CJK'
        
        # Nome do arquivo
        pdf_file = os.path.join(output_dir, "relatorio_irrf.pdf")
        
        # Gerar PDF
        doc = SimpleDocTemplate(pdf_file, pagesize=letter, 
                              leftMargin=1.2*cm, rightMargin=1.2*cm, 
                              topMargin=1.2*cm, bottomMargin=1.2*cm)
        elements = []
        
        # Título principal
        elements.append(Paragraph("RELATÓRIO DE IRRF - IMPOSTO DE RENDA RETIDO NA FONTE", styles['Title']))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Data de referência
        date_str = df_irrf['DATA'].iloc[0] if not df_irrf.empty else ""
        elements.append(Paragraph(f"Data de referência: {date_str}", styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Preparar dados para a tabela
        table_data = [['Tipo', 'Entidade', 'Valor IRRF', 'Observação']]
        
        for _, row in df_irrf.iterrows():
            # Valor do IRRF vem da coluna IRRF_normalizado
            valor_irrf = row.get('IRRF_normalizado', 0)
            
            # Formatar entidade (nome mais curto)
            entidade = str(row.get('NomeSingular', 'N/A'))
            if len(entidade) > 30:
                entidade = entidade[:27] + '...'
            
            table_data.append([
                row['Tipo'],
                Paragraph(entidade, cell_style),
                self.format_currency(valor_irrf),
                "IRRF dos dados originais"
            ])
        
        # Adicionar linha de total
        table_data.append([
            '',
            Paragraph('<b>TOTAL</b>', cell_style),
            f'<b>{self.format_currency(irrf_info["total_irrf"])}</b>',
            ''
        ])
        
        # Configurar larguras das colunas (ajustadas para formato retrato A4)
        col_widths = [0.8*inch, 1.8*inch, 1*inch, 1.8*inch]
        
        # Criar tabela
        table = Table(table_data, colWidths=col_widths, repeatRows=1, splitByRow=True)
        
        # Estilo da tabela
        table_style = TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            
            # Dados
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),   # Valores à direita
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 1), (-1, -2), 7),
            
            # Linha de total
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 8),
            ('ALIGN', (2, -1), (-1, -1), 'RIGHT'),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            
            # Alternância de cores nas linhas
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        
        # Resumo estatístico
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph("RESUMO ESTATÍSTICO", styles['Heading2']))
        elements.append(Spacer(1, 0.1 * inch))
        
        resumo_data = [
            ['Categoria', 'Registros', 'Total IRRF'],
            ['A Pagar', str(len(df_irrf[df_irrf['Tipo'] == 'A pagar'])), self.format_currency(irrf_info['irrf_a_pagar'])],
            ['A Receber', str(len(df_irrf[df_irrf['Tipo'] == 'A receber'])), self.format_currency(irrf_info['irrf_a_receber'])],
            ['TOTAL GERAL', str(irrf_info['registros_com_irrf']), self.format_currency(irrf_info['total_irrf'])]
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
        
        # Informações finais
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph("OBSERVAÇÕES:", styles['Heading3']))
        elements.append(Paragraph("• Registros de IRRF identificados através da palavra 'IRRF' no complemento", styles['Normal']))
        elements.append(Paragraph("• Valores apresentados são os valores dos registros contábeis de IRRF", styles['Normal']))
        elements.append(Paragraph("• IRRF A Pagar: valores deduzidos dos pagamentos", styles['Normal']))
        elements.append(Paragraph("• IRRF A Receber: valores deduzidos dos recebimentos", styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        
        # Gerar o PDF
        doc.build(elements)
        
        if display_result:
            st.success(f"✅ Relatório de IRRF gerado com sucesso!")
            st.info(f"📊 Total de registros com IRRF: {irrf_info['registros_com_irrf']}")
            st.info(f"💰 Total IRRF: {self.format_currency(irrf_info['total_irrf'])}")
            st.info(f"🔸 IRRF A Pagar: {self.format_currency(irrf_info['irrf_a_pagar'])}")
            st.info(f"🔹 IRRF A Receber: {self.format_currency(irrf_info['irrf_a_receber'])}")
        
        return {
            "pdf_file": pdf_file,
            "total_irrf": irrf_info['total_irrf'],
            "total_registros": irrf_info['registros_com_irrf'],
            "irrf_a_pagar": irrf_info['irrf_a_pagar'],
            "irrf_a_receber": irrf_info['irrf_a_receber']
        }

    def export_to_csv(self, df, filename):
        """Exporta o DataFrame para um arquivo CSV."""
        csv_content = self.df_to_csv_string(df)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        return filename

    def safe_numeric_sum(self, series):
        """Converte série para numérica e retorna soma, tratando valores não-numéricos."""
        if series.empty:
            return 0.0
        
        # Converter para numérico, forçando erros para NaN
        numeric_series = pd.to_numeric(series, errors='coerce')
        
        # Substituir NaN por 0 e retornar soma
        return numeric_series.fillna(0).sum()
    
    def calculate_irrf_by_complemento(self, df):
        """Calcula IRRF baseado nos registros que contêm 'IRRF' no complemento."""
        # Filtrar registros que têm IRRF no complemento usando a função helper
        mask_irrf = self.is_irrf_record(df)
        df_irrf = df[mask_irrf].copy()
        
        if df_irrf.empty:
            return {
                'total_irrf': 0.0,
                'irrf_a_pagar': 0.0,
                'irrf_a_receber': 0.0,
                'registros_irrf': 0,
                'df_irrf': pd.DataFrame()
            }
        
        # Separar por tipo
        irrf_a_pagar = self.safe_numeric_sum(df_irrf[df_irrf['Tipo'] == 'A pagar']['valor'])
        irrf_a_receber = self.safe_numeric_sum(df_irrf[df_irrf['Tipo'] == 'A receber']['valor'])
        
        return {
            'total_irrf': irrf_a_pagar + irrf_a_receber,
            'irrf_a_pagar': irrf_a_pagar,
            'irrf_a_receber': irrf_a_receber,
            'registros_irrf': len(df_irrf),
            'df_irrf': df_irrf
        }
    
    def calculate_irrf_from_original_data(self, df):
        """
        Calcula IRRF baseado nos dados originais (coluna IRRF dos dados originais).
        Esta função deve ser usada quando temos acesso aos dados originais com a coluna IRRF.
        """
        # Filtrar apenas registros que NÃO são lançamentos de IRRF (registros originais)
        mask_nao_irrf = ~self.is_irrf_record(df)
        df_original = df[mask_nao_irrf].copy()
        
        if df_original.empty:
            return {
                'total_irrf': 0.0,
                'irrf_a_pagar': 0.0,
                'irrf_a_receber': 0.0,
                'registros_com_irrf': 0,
                'valor_bruto_a_pagar': 0.0,
                'valor_bruto_a_receber': 0.0,
                'valor_liquido_a_pagar': 0.0,
                'valor_liquido_a_receber': 0.0
            }
        
        # Calcular valores brutos (dos registros originais)
        df_a_pagar = df_original[df_original['Tipo'] == 'A pagar']
        df_a_receber = df_original[df_original['Tipo'] == 'A receber']
        
        valor_bruto_a_pagar = self.safe_numeric_sum(df_a_pagar['valor'])
        valor_bruto_a_receber = self.safe_numeric_sum(df_a_receber['valor'])
        
        # Calcular IRRF baseado na coluna IRRF original (se disponível)
        irrf_a_pagar = 0.0
        irrf_a_receber = 0.0
        registros_com_irrf = 0
        
        if 'IRRF' in df_original.columns:
            # Normalizar valores da coluna IRRF
            df_original['IRRF_normalizado'] = df_original['IRRF'].apply(self.normalize_value)
            
            # Filtrar registros com IRRF > 0
            df_com_irrf = df_original[df_original['IRRF_normalizado'] > 0]
            registros_com_irrf = len(df_com_irrf)
            
            # Somar IRRF por tipo
            df_a_pagar_irrf = df_com_irrf[df_com_irrf['Tipo'] == 'A pagar']
            df_a_receber_irrf = df_com_irrf[df_com_irrf['Tipo'] == 'A receber']
            
            irrf_a_pagar = self.safe_numeric_sum(df_a_pagar_irrf['IRRF_normalizado'])
            irrf_a_receber = self.safe_numeric_sum(df_a_receber_irrf['IRRF_normalizado'])
        
        # Calcular valores líquidos
        valor_liquido_a_pagar = valor_bruto_a_pagar - irrf_a_pagar
        valor_liquido_a_receber = valor_bruto_a_receber - irrf_a_receber
        
        return {
            'total_irrf': irrf_a_pagar + irrf_a_receber,
            'irrf_a_pagar': irrf_a_pagar,
            'irrf_a_receber': irrf_a_receber,
            'registros_com_irrf': registros_com_irrf,
            'valor_bruto_a_pagar': valor_bruto_a_pagar,
            'valor_bruto_a_receber': valor_bruto_a_receber,
            'valor_liquido_a_pagar': valor_liquido_a_pagar,
            'valor_liquido_a_receber': valor_liquido_a_receber
        }

    def is_irrf_record(self, df):
        """Identifica registros de IRRF baseado no complemento."""
        return (
            df['complemento'].str.contains(r'\|\s*IRRF\s*$', case=False, na=False, regex=True) |
            df['complemento'].str.endswith('IRRF', na=False) |
            df['complemento'].str.contains(r'IRRF\s*$', case=False, na=False, regex=True)
        )

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
    tab1, tab2, tab3 = st.tabs(["Processamento de Arquivos", "Relatórios Contábeis", "Edição de Dados"])
    
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
            
            # Nova opção para mostrar prévia dos arquivos
            show_preview = st.checkbox("Mostrar prévia dos arquivos antes do processamento", value=False)
        
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
                    
                    # Mostrar prévia se solicitado
                    if show_preview:
                        try:
                            # Ler arquivo para prévia
                            uploaded_file.seek(0)
                            df_preview = pd.read_csv(uploaded_file, sep=';', encoding='utf-8', nrows=10)
                            self.show_file_preview(df_preview, uploaded_file.name)
                            
                            # Perguntar se deve continuar
                            if not st.button(f"Processar {uploaded_file.name}", key=f"process_{i}"):
                                st.info("Clique no botão acima para processar este arquivo.")
                                continue
                        except Exception as e:
                            st.warning(f"Não foi possível mostrar prévia: {str(e)}")
                    
                    # Processamento do arquivo
                    processed_df, original_df = processor.process_csv_file(uploaded_file)
                    
                    if processed_df is not None:
                        # Salvar também o DataFrame original
                        processed_dfs[uploaded_file.name] = processed_df
                        original_dfs[uploaded_file.name] = original_df
                        
                        # Exibe uma prévia dos dados processados
                        st.write("Prévia dos dados processados:")
                        
                        # Opção para escolher quantas linhas mostrar
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(f"**Total de {len(processed_df)} registros processados**")
                        with col2:
                            show_all = st.checkbox("Mostrar todos os registros", key=f"show_all_{i}")
                        
                        if show_all:
                            # Mostrar todos os registros
                            st.dataframe(processed_df, use_container_width=True, height=400)
                        else:
                            # Mostrar apenas as primeiras linhas com opção de escolher quantas
                            num_rows = st.slider(
                                "Número de linhas para mostrar:", 
                                min_value=5, 
                                max_value=min(50, len(processed_df)), 
                                value=min(preview_rows, len(processed_df)),
                                key=f"num_rows_{i}"
                            )
                            st.dataframe(processed_df.head(num_rows), use_container_width=True)
                        
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
                    ["Relatório Unificado da Câmara de Compensação", "Relatório de IRRF", "Todos os relatórios solicitados pelo contador", "Relatórios específicos"]
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
                    
                    # Opção de debug (movida para cá para evitar problemas de estado)
                    debug_mode = st.checkbox("Modo debug (mostrar informações detalhadas)", value=False, key="debug_mode_reports")
                    
                    # VERIFICAR SE HÁ DADOS EDITADOS
                    dados_editados = False
                    arquivos_editados = []
                    
                    # Verificar se há versões editadas dos arquivos selecionados
                    for filename in selected_files:
                        edited_key = f"{filename}_edited"
                        if edited_key in st.session_state:
                            arquivos_editados.append(filename)
                            dados_editados = True
                    
                    # Decidir quais dados usar para o relatório
                    if dados_editados:
                        st.info(f"✏️ **Usando dados editados** para {len(arquivos_editados)} arquivo(s): {', '.join(arquivos_editados)}")
                        
                        # Consolidar DataFrames - usar versão editada quando disponível
                        dfs_to_process = []
                        for filename in selected_files:
                            edited_key = f"{filename}_edited"
                            if edited_key in st.session_state:
                                # Usar versão editada reprocessada
                                reprocessed_key = f"{filename}_reprocessed"
                                if reprocessed_key in st.session_state:
                                    dfs_to_process.append(st.session_state[reprocessed_key])
                                else:
                                    # Fallback para versão editada
                                    dfs_to_process.append(st.session_state[edited_key])
                            else:
                                # Usar versão original
                                dfs_to_process.append(st.session_state.processed_dfs[filename])
                        
                        consolidated_df = pd.concat(dfs_to_process, ignore_index=True)
                    else:
                        st.info("📄 **Usando dados originais** (nenhuma edição detectada)")
                        # Consolidar DataFrames originais
                        dfs_to_process = [st.session_state.processed_dfs[filename] for filename in selected_files]
                        consolidated_df = pd.concat(dfs_to_process, ignore_index=True)
                    
                    st.write(f"Gerando relatórios contábeis a partir de {len(consolidated_df)} registros...")
                    
                    # Mostrar barra de progresso
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    status_text.text("Processando relatórios contábeis...")
                    
                    # CRIAR RESUMO EXECUTIVO COM VALORES BRUTOS E LÍQUIDOS
                    st.subheader("💰 Resumo Executivo")
                    
                    # Calcular valores usando a nova função
                    irrf_info = processor.calculate_irrf_from_original_data(consolidated_df)
                    
                    # Usar valores calculados da função
                    valor_bruto_a_pagar = irrf_info['valor_bruto_a_pagar']
                    valor_bruto_a_receber = irrf_info['valor_bruto_a_receber']
                    valor_liquido_a_pagar = irrf_info['valor_liquido_a_pagar']
                    valor_liquido_a_receber = irrf_info['valor_liquido_a_receber']
                    saldo_liquido = valor_liquido_a_receber - valor_liquido_a_pagar
                    saldo_bruto = valor_bruto_a_receber - valor_bruto_a_pagar
                    
                    # Contar registros (filtrar apenas registros originais, não lançamentos de IRRF)
                    mask_nao_irrf = ~processor.is_irrf_record(consolidated_df)
                    df_a_pagar_bruto = consolidated_df[(consolidated_df['Tipo'] == 'A pagar') & mask_nao_irrf]
                    df_a_receber_bruto = consolidated_df[(consolidated_df['Tipo'] == 'A receber') & mask_nao_irrf]
                    
                    # Exibir resumo em colunas (sem IRRF - tem seção dedicada)
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("💸 Valor A Pagar (Bruto)", processor.format_currency(valor_bruto_a_pagar))
                        st.metric("💸 Valor A Pagar (Líquido)", processor.format_currency(valor_liquido_a_pagar))
                        st.metric("📊 Registros A Pagar", len(df_a_pagar_bruto))
                    
                    with col2:
                        st.metric("💰 Valor A Receber (Bruto)", processor.format_currency(valor_bruto_a_receber))
                        st.metric("💰 Valor A Receber (Líquido)", processor.format_currency(valor_liquido_a_receber))
                        st.metric("📊 Registros A Receber", len(df_a_receber_bruto))
                    
                    with col3:
                        saldo_color = "normal" if saldo_bruto >= 0 else "inverse"
                        st.metric("🏦 Saldo Final (Bruto)", processor.format_currency(saldo_bruto), delta_color=saldo_color)
                        saldo_liquido_color = "normal" if saldo_liquido >= 0 else "inverse"
                        st.metric("🏦 Saldo Final (Líquido)", processor.format_currency(saldo_liquido), delta_color=saldo_liquido_color)
                        st.metric("📊 Total de Registros", len(df_a_pagar_bruto) + len(df_a_receber_bruto))
                    
                    # Alerta se há diferença significativa entre bruto e líquido
                    if abs(saldo_bruto - saldo_liquido) > 0.01:
                        st.warning(f"⚠️ **Atenção**: Diferença de {processor.format_currency(abs(saldo_bruto - saldo_liquido))} entre saldo bruto e líquido devido ao IRRF")
                    
                    # SEÇÃO DE DETALHAMENTO DO IRRF
                    if irrf_info['total_irrf'] > 0:
                        st.subheader("🧾 Detalhamento do IRRF")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**📊 Registros com IRRF nos dados originais:**")
                            st.write(f"• **Registros com IRRF**: {irrf_info['registros_com_irrf']}")
                            st.write(f"• **IRRF A Pagar**: {processor.format_currency(irrf_info['irrf_a_pagar'])}")
                            st.write(f"• **IRRF A Receber**: {processor.format_currency(irrf_info['irrf_a_receber'])}")
                            st.write(f"• **Total IRRF**: {processor.format_currency(irrf_info['total_irrf'])}")
                        
                        with col2:
                            st.write("**💡 Cálculo do Valor Líquido:**")
                            st.write("*Valores líquidos = Valores brutos - IRRF correspondente*")
                            st.write("")
                            st.write(f"**A Pagar**: {processor.format_currency(valor_bruto_a_pagar)} - {processor.format_currency(irrf_info['irrf_a_pagar'])} = {processor.format_currency(valor_liquido_a_pagar)}")
                            st.write(f"**A Receber**: {processor.format_currency(valor_bruto_a_receber)} - {processor.format_currency(irrf_info['irrf_a_receber'])} = {processor.format_currency(valor_liquido_a_receber)}")
                            st.write("")
                            st.write(f"**Saldo Líquido**: {processor.format_currency(saldo_liquido)}")
                    else:
                        st.info("ℹ️ Nenhum registro com IRRF encontrado nos dados originais.")
                    
                    # Verificação de segurança para output_dir
                    if 'output_dir' not in locals() or output_dir is None:
                        import tempfile
                        output_dir = tempfile.mkdtemp()
                        st.info("🔧 Diretório temporário criado para relatórios")
                    
                    try:
                        if report_options == "Relatório Unificado da Câmara de Compensação":
                            # Gerar relatório unificado
                            unified_results = processor.generate_unified_report(consolidated_df, output_dir, display_result=True)
                            
                            # Criar link de download para o relatório unificado
                            if "pdf_file" in unified_results and os.path.exists(unified_results["pdf_file"]):
                                with open(unified_results["pdf_file"], "rb") as f:
                                    pdf_data = f.read()
                                    b64 = base64.b64encode(pdf_data).decode()
                                    href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio_camara_compensacao.pdf" class="download-button">Baixar Relatório Unificado (PDF)</a>'
                                    st.markdown(href, unsafe_allow_html=True)
                        
                        elif report_options == "Relatório de IRRF":
                            # Gerar relatório de IRRF
                            irrf_results = processor.generate_irrf_report(consolidated_df, output_dir, display_result=True)
                            
                            # Criar link de download para o relatório de IRRF
                            if "pdf_file" in irrf_results and os.path.exists(irrf_results["pdf_file"]):
                                with open(irrf_results["pdf_file"], "rb") as f:
                                    pdf_data = f.read()
                                    b64 = base64.b64encode(pdf_data).decode()
                                    href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio_irrf.pdf" class="download-button">Baixar Relatório de IRRF (PDF)</a>'
                                    st.markdown(href, unsafe_allow_html=True)
                            
                            # Exibir resumo do relatório de IRRF
                            st.write("## Resumo do Relatório de IRRF")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total IRRF", processor.format_currency(irrf_results['total_irrf']))
                            with col2:
                                st.metric("Registros com IRRF", irrf_results['total_registros'])
                            with col3:
                                st.metric("IRRF A Pagar", processor.format_currency(irrf_results['irrf_a_pagar']))
                                st.metric("IRRF A Receber", processor.format_currency(irrf_results['irrf_a_receber']))
                        
                        else:
                            # Gerar relatórios tradicionais
                            report_results = processor.generate_accounting_reports(consolidated_df, output_dir, display_result=False, debug=debug_mode)
                            
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
        st.markdown("""
        # 📋 Documentação Completa do Sistema
        
        ## 🎯 Visão Geral
        Sistema desenvolvido em Python com Streamlit para processar arquivos CSV da Câmara de Compensação do Sistema Uniodonto, gerando lançamentos contábeis e relatórios financeiros.
        
        ## ⚙️ Regras de Processamento
        
        ### Estrutura do Arquivo CSV
        O arquivo CSV deve conter as seguintes colunas obrigatórias:
        
        | Coluna | Descrição | Tipo |
        |--------|-----------|------|
        | Tipo | Tipo de transação (A pagar/A receber) | Texto |
        | CodigoSingular | Código único da entidade | Número |
        | NomeSingular | Nome da entidade | Texto |
        | TipoSingular | Classificação (Operadora/Prestadora) | Texto |
        | CodigoTipoRecebimento | Código do tipo de recebimento | Número |
        | Descricao | Descrição da transação | Texto |
        | ValorBruto | Valor bruto | Moeda |
        | TaxaAdministrativa | Taxa administrativa | Moeda |
        | Subtotal | Valor subtotal | Moeda |
        | IRRF | Imposto de Renda Retido na Fonte | Moeda |
        | OutrosTributos | Outros tributos | Moeda |
        | ValorLiquido | Valor líquido | Moeda |
        
        ### Regras de Lançamentos Contábeis
        
        #### Regras de Débito
        
        ##### A pagar - Operadora
        | CodigoTipoRecebimento | Conta |
        |----------------------|--------|
        | 1 | 31731 |
        | 2 | 40507 |
        | 3 | 52631 (UNIODONTO DO BRASIL) / 52632 (outros) |
        | 4 | 52532 |
        | 5 | 51818 |
        | 6 | 51202 |
        
        ##### A pagar - Prestadora
        | CodigoTipoRecebimento | Conta |
        |----------------------|--------|
        | 1,2 | 40140 |
        | 3 | 52631 (UNIODONTO DO BRASIL) / 52632 (outros) |
        | 4 | 52532 |
        | 5 | 51818 |
        | 6 | 51202 |
        
        ##### A receber - Operadora
        | CodigoTipoRecebimento | Conta |
        |----------------------|--------|
        | 1 | 19958 |
        | 2 | 85433 |
        | 3,4,5 | 84679 |
        | 6 | 19253 |
        
        ##### A receber - Prestadora
        | CodigoTipoRecebimento | Conta |
        |----------------------|--------|
        | 1,2 | 19253 |
        | 3,4,5 | 84679 |
        | 6 | 19253 |
        
        #### Regras de Crédito
        
        ##### A pagar - Operadora
        | CodigoTipoRecebimento | Conta |
        |----------------------|--------|
        | 1 | 90918 |
        | 2 | 90919 |
        | 3 | 21898 (UNIODONTO DO BRASIL) / 22036 (outros) |
        | 4 | 21898 (UNIODONTO DO BRASIL) / 22036 (outros) |
        | 5 | 51818 |
        | 6 | 90919 |
        
        ##### A pagar - Prestadora
        | CodigoTipoRecebimento | Conta |
        |----------------------|--------|
        | 1,2 | 92003 |
        | 3 | 21898 (UNIODONTO DO BRASIL) / 22036 (outros) |
        | 4 | 21898 (UNIODONTO DO BRASIL) / 22036 (outros) |
        | 5 | 51818 |
        | 6 | 90919 |
        
        ##### A receber - Operadora/Prestadora
        | CodigoTipoRecebimento | Conta |
        |----------------------|--------|
        | 1 | 30203 |
        | 2 | 40413 |
        | 3 | 30069 |
        | 4 | 30071 |
        | 5 | 31426 |
        | 6 | 30127 |
        
        #### Regras de Histórico
        
        ##### A pagar
        | CodigoTipoRecebimento | Histórico |
        |----------------------|-----------|
        | 1,2,6 | 2005 |
        | 3 | 361 (UNIODONTO DO BRASIL) / 368 (outros) |
        | 4 | 365 |
        | 5 | 179 |
        
        ##### A receber
        | CodigoTipoRecebimento | Histórico |
        |----------------------|-----------|
        | 1,2,6 | 1021 |
        | 3 | 361 (UNIODONTO DO BRASIL) / 368 (outros) |
        | 4 | 365 |
        | 5 | 179 |
        
        ### Regras Especiais
        
        #### LGPD e Atuário
        Quando CodigoTipoRecebimento = 5 e descrição contém:
        - **"LGPD"**:
          - Débito: 52129
          - Crédito: 22036
          - Histórico: 2005
        - **"ATUARIO"/"ATUÁRIO"**:
          - Débito: 52451
          - Crédito: 22036
          - Histórico: 2005
        
        ## 🚀 Funcionalidades Principais
        
        ### 1. Processamento de Arquivos
        - Leitura de arquivos CSV
        - Validação de dados
        - Processamento em lote
        - Detecção automática de formato
        
        ### 2. Lançamentos Contábeis
        - Cálculo automático de débito
        - Cálculo automático de crédito
        - Geração de histórico
        - Processamento de IRRF
        
        ### 3. Relatórios
        - Exportação em CSV
        - Exportação em PDF
        - Visualização na interface web
        - Download individual ou em lote
        
        ### 4. Interface Web
        - Upload de múltiplos arquivos
        - Visualização prévia
        - Configuração de data personalizada
        - Opções avançadas de processamento
        
        ## 💻 Códigos das Contas Contábeis
        
        ### Principais Contas de Débito
        - **85433**: Contraprestação assumida em Pós-pagamento
        - **40507**: Despesas com Eventos/ Sinistros
        - **19958**: Contraprestação Corresponsabilidade Assumida Pré-pagamento
        - **52631**: Taxa para Manutenção da Central
        - **52532**: Propaganda e Marketing - Matriz
        - **84679**: Outras Contas a Receber
        
        ### Principais Contas de Crédito
        - **90919**: Intercâmbio a Pagar de Corresponsabilidade Cedida
        - **21898**: Contrap. Corresp. Assumida Pós
        - **22036**: Federação Paulista
        - **30203**: Corresponsabilidade Assumida Pré
        - **40413**: (-) Recup.Reemb. Contratante Assumida Pós-pagamento
        
        ### Códigos de Histórico
        - **1021**: VL. N/NFF. INTERC. RECEB.ODONT
        - **2005**: VL. S/NFF. INTERC. A PAGAR
        - **361**: VL. TAXA MANUT. DA CENTRAL S/N
        - **365**: VL. FUNDO DE MARKTING S/NFF
        - **179**: VL. MULTAS/JUROS
        
        ## ⚠️ Observações Importantes
        
        ### Formato dos Arquivos
        1. Arquivos CSV devem seguir o formato especificado
        2. Valores monetários no formato brasileiro (vírgula como separador decimal)
        3. Datas no formato DD/MM/YYYY
        4. Separador de colunas: ponto e vírgula (;)
        
        ### Processamento
        1. Sistema processa múltiplos arquivos simultaneamente
        2. Relatórios são gerados automaticamente
        3. Validações são realizadas durante o processamento
        4. Suporte a formatos simplificados com conversão automática
        
        ### Segurança
        1. Não armazena dados sensíveis
        2. Processamento local dos arquivos
        3. Exportação segura dos relatórios
        4. Dados temporários são limpos automaticamente
        
        ---
        
        **Para mais informações ou suporte, consulte o código fonte ou entre em contato com a equipe de desenvolvimento.**
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
    
    with tab3:
        st.header("Edição de Dados")
        
        # Seção de seleção e upload de arquivos
        st.subheader("📁 Seleção de Arquivos")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Upload de múltiplos arquivos CSV
            uploaded_edit_files = st.file_uploader(
                "Faça upload de novos arquivos CSV para edição", 
                type=["csv"], 
                accept_multiple_files=True,
                key="upload_edit_files"
            )
            
            # Processar arquivos carregados
            if uploaded_edit_files:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_edit_files):
                    status_text.text(f"Processando {uploaded_file.name}...")
                    progress_bar.progress((i) / len(uploaded_edit_files))
                    
                    try:
                        processed_df, original_df = processor.process_csv_file(uploaded_file)
                        
                        if processed_df is not None:
                            # Inicializar session_state se necessário
                            if 'processed_dfs' not in st.session_state:
                                st.session_state.processed_dfs = {}
                            if 'original_dfs' not in st.session_state:
                                st.session_state.original_dfs = {}
                            
                            # Adicionar à sessão
                            st.session_state.processed_dfs[uploaded_file.name] = processed_df
                            st.session_state.original_dfs[uploaded_file.name] = original_df
                            
                        progress_bar.progress((i+1) / len(uploaded_edit_files))
                    
                    except Exception as e:
                        st.error(f"Erro ao processar {uploaded_file.name}: {str(e)}")
                
                progress_bar.progress(1.0)
                status_text.text("Upload concluído!")
                st.success(f"✅ {len(uploaded_edit_files)} arquivo(s) carregado(s) com sucesso!")
        
        with col2:
            st.write("**Arquivos disponíveis:**")
            if 'processed_dfs' in st.session_state and st.session_state.processed_dfs:
                st.write(f"📄 {len(st.session_state.processed_dfs)} arquivo(s)")
                for filename in st.session_state.processed_dfs.keys():
                    st.write(f"• {filename}")
            else:
                st.write("📄 Nenhum arquivo carregado")
        
        if 'processed_dfs' not in st.session_state or not st.session_state.processed_dfs:
            st.info("📤 Faça upload de arquivos CSV ou processe arquivos na aba 'Processamento de Arquivos' para editar dados.")
        else:
            st.markdown("---")
            
            # Seleção do arquivo para edição
            st.subheader("🎯 Arquivo para Edição")
            processed_files = list(st.session_state.processed_dfs.keys())
            selected_file = st.selectbox("Selecione o arquivo que deseja editar:", processed_files)
            
            if selected_file:
                # Obter DataFrame ORIGINAL do arquivo selecionado
                if 'original_dfs' in st.session_state and selected_file in st.session_state.original_dfs:
                    df_edit = st.session_state.original_dfs[selected_file].copy()
                else:
                    # Fallback para dados processados se não houver originais
                    df_edit = st.session_state.processed_dfs[selected_file].copy()
                
                # Verificar se há arquivo editado salvo na sessão
                edited_key = f'edited_{selected_file}'
                if edited_key in st.session_state:
                    df_edit = st.session_state[edited_key].copy()
                    st.info("📝 Exibindo arquivo com alterações salvas")
                
                # Adicionar ID único para cada linha se não existir
                if 'row_id' not in df_edit.columns:
                    df_edit['row_id'] = range(len(df_edit))
                
                # Estatísticas do arquivo
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 Arquivo Selecionado", selected_file)
                with col2:
                    st.metric("📊 Total de Registros", len(df_edit))
                with col3:
                    # Verificar se há alterações pendentes
                    if edited_key in st.session_state:
                        st.metric("✏️ Status", "Editado", delta="Alterações salvas")
                    else:
                        st.metric("✏️ Status", "Original")
                
                st.markdown("---")
                
                # Seção de filtro simplificado
                st.subheader("🔍 Filtro")
                filtro_texto = st.text_input(
                    "Digite qualquer texto para buscar em todas as colunas:",
                    help="Busca em: Nome Singular, Descrição, Tipo, Código, etc."
                )
                
                # Aplicar filtro por texto em todas as colunas
                df_filtrado = df_edit.copy()
                
                if filtro_texto:
                    mask = pd.Series([False] * len(df_filtrado))
                    
                    # Buscar em todas as colunas de texto
                    for col in df_filtrado.columns:
                        if col != 'row_id':  # Excluir apenas a coluna de ID
                            try:
                                mask |= df_filtrado[col].astype(str).str.contains(
                                    filtro_texto, case=False, na=False, regex=False
                                )
                            except:
                                continue  # Ignorar colunas que não podem ser convertidas para string
                    
                    df_filtrado = df_filtrado[mask]
                
                # Informações sobre o filtro
                if filtro_texto:
                    st.write(f"**🔍 Filtrados:** {len(df_filtrado)} de {len(df_edit)} registros")
                else:
                    st.write(f"**📋 Exibindo:** {len(df_filtrado)} registros")
                
                if len(df_filtrado) > 0:
                    # Seção de seleção
                    st.subheader("✅ Seleção de Registros")
                    
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        selecionar_todos = st.checkbox("Selecionar todos os registros filtrados")
                    
                    with col2:
                        if st.button("🗑️ Limpar seleção"):
                            st.session_state.selected_rows = []
                    
                    # Inicializar seleção se não existir
                    if 'selected_rows' not in st.session_state:
                        st.session_state.selected_rows = []
                    
                    # Se "selecionar todos" foi marcado, adicionar todos os IDs filtrados
                    if selecionar_todos:
                        st.session_state.selected_rows = df_filtrado['row_id'].tolist()
                    
                    # Tabela para edição
                    st.subheader("📋 Dados para Edição")
                    
                    # Preparar dados para exibição - APENAS colunas originais
                    colunas_exibicao = ['row_id']
                    colunas_originais = ['Tipo', 'CodigoSingular', 'NomeSingular', 'TipoSingular', 'RegistroANS',
                                       'CodigoTipoRecebimento', 'DescricaoTipoRecebimento', 'NumeroDocumento', 
                                       'Descricao', 'ValorBruto', 'TaxaAdministrativa', 'Subtotal', 
                                       'IRRF', 'OutrosTributos', 'ValorLiquido']
                    
                    for col in colunas_originais:
                        if col in df_filtrado.columns:
                            colunas_exibicao.append(col)
                    
                    df_display = df_filtrado[colunas_exibicao].copy()
                    
                    # Adicionar coluna de seleção
                    df_display['Selecionar'] = df_display['row_id'].isin(st.session_state.selected_rows)
                    
                    # Reordenar colunas
                    cols = ['Selecionar'] + [col for col in df_display.columns if col != 'Selecionar']
                    df_display = df_display[cols]
                    
                    # Exibir tabela editável
                    edited_df = st.data_editor(
                        df_display,
                        use_container_width=True,
                        height=400,
                        column_config={
                            "Selecionar": st.column_config.CheckboxColumn(
                                "Selecionar",
                                help="Selecione os registros para edição",
                                default=False,
                            ),
                            "row_id": st.column_config.NumberColumn(
                                "ID",
                                help="ID único do registro",
                                disabled=True,
                            ),
                            "CodigoTipoRecebimento": st.column_config.NumberColumn(
                                "Código",
                                help="Código do tipo de recebimento",
                                width="small",
                            ),
                            "DescricaoTipoRecebimento": st.column_config.TextColumn(
                                "Descrição",
                                help="Descrição do tipo de recebimento",
                                width="medium",
                            ),
                            "ValorBruto": st.column_config.NumberColumn(
                                "Valor Bruto",
                                help="Valor bruto da transação",
                                format="R$ %.2f",
                            ),
                        },
                        disabled=[col for col in colunas_exibicao if col not in ["Selecionar"]],
                        key="data_editor_edit"
                    )
                    
                    # Atualizar seleção baseada na tabela editada
                    selected_rows = edited_df[edited_df['Selecionar']]['row_id'].tolist()
                    st.session_state.selected_rows = selected_rows
                    
                    # Mostrar registros selecionados
                    if selected_rows:
                        st.success(f"✅ {len(selected_rows)} registro(s) selecionado(s)")
                        
                        # Seção de edição
                        st.subheader("✏️ Edição")
                        
                        # Seleção do novo CodigoTipoRecebimento
                        opcoes_codigo = {
                            1: "1 - Repasse em Pré-pagamento",
                            2: "2 - Repasse em Custo Operacional", 
                            3: "3 - Taxa de Manutenção",
                            4: "4 - Fundo de Marketing",
                            5: "5 - Juros",
                            6: "6 - Outros"
                        }
                            
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            novo_codigo = st.selectbox(
                                "Novo Código e Descrição:",
                                options=list(opcoes_codigo.keys()),
                                format_func=lambda x: opcoes_codigo[x],
                                key="novo_codigo_edit"
                            )
                            
                            # Mapeamento das descrições
                            mapeamento_descricao = {
                                1: "Repasse em Pré-pagamento",
                                2: "Repasse em Custo Operacional",
                                3: "Taxa de Manutenção",
                                4: "Fundo de Marketing", 
                                5: "Juros",
                                6: "Outros"
                            }
                            
                            st.info(f"📝 **Código:** {novo_codigo} | **Descrição:** {mapeamento_descricao[novo_codigo]}")
                        
                        with col2:
                            st.write("")  # Espaçamento
                            st.write("")  # Espaçamento
                            
                            # Botão para aplicar alteração
                            if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                                # Aplicar alterações
                                for row_id in selected_rows:
                                    # Encontrar o índice no DataFrame
                                    idx = df_edit[df_edit['row_id'] == row_id].index[0]
                                    
                                    # Atualizar CodigoTipoRecebimento e DescricaoTipoRecebimento
                                    df_edit.loc[idx, 'CodigoTipoRecebimento'] = novo_codigo
                                    df_edit.loc[idx, 'DescricaoTipoRecebimento'] = mapeamento_descricao[novo_codigo]
                                
                                # Salvar arquivo editado na sessão
                                st.session_state[edited_key] = df_edit
                                
                                # Gerar arquivo reprocessado automaticamente
                                colunas_originais = ['Tipo', 'CodigoSingular', 'NomeSingular', 'TipoSingular', 'RegistroANS',
                                                   'CodigoTipoRecebimento', 'DescricaoTipoRecebimento', 'NumeroDocumento', 
                                                   'Descricao', 'ValorBruto', 'TaxaAdministrativa', 'Subtotal', 
                                                   'IRRF', 'OutrosTributos', 'ValorLiquido']
                                
                                colunas_disponveis = [col for col in colunas_originais if col in df_edit.columns]
                                df_reprocessar = df_edit[colunas_disponveis].copy()
                                
                                # Remover row_id para reprocessamento
                                if 'row_id' in df_reprocessar.columns:
                                    df_reprocessar = df_reprocessar.drop('row_id', axis=1)
                                
                                # Reprocessar com lógica contábil
                                df_reprocessado = processor.process_dataframe(df_reprocessar)
                                
                                # Salvar arquivo reprocessado na sessão
                                reprocessed_key = f'reprocessed_{selected_file}'
                                st.session_state[reprocessed_key] = df_reprocessado
                                
                                # Atualizar dados processados para usar nos relatórios
                                st.session_state.processed_dfs[selected_file] = df_reprocessado
                                
                                st.success(f"✅ {len(selected_rows)} registro(s) alterado(s) e arquivo reprocessado!")
                                st.info("🔄 Arquivo reprocessado automaticamente e disponível para relatórios")
                                
                                # Limpar seleção
                                st.session_state.selected_rows = []
                                
                                # Recarregar para mostrar mudanças
                                st.rerun()
                        
                    # Seção de download - sempre visível se há arquivo editado
                    if edited_key in st.session_state:
                        st.markdown("---")
                        st.subheader("📥 Download")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Download do arquivo editado (formato original)
                            if st.button("📄 Baixar Arquivo Editado (Original)", type="secondary"):
                                # Filtrar apenas colunas originais
                                colunas_originais = ['Tipo', 'CodigoSingular', 'NomeSingular', 'TipoSingular', 'RegistroANS',
                                                   'CodigoTipoRecebimento', 'DescricaoTipoRecebimento', 'NumeroDocumento', 
                                                   'Descricao', 'ValorBruto', 'TaxaAdministrativa', 'Subtotal', 
                                                   'IRRF', 'OutrosTributos', 'ValorLiquido']
                                
                                df_download = st.session_state[edited_key].copy()
                                colunas_disponveis = [col for col in colunas_originais if col in df_download.columns]
                                df_download = df_download[colunas_disponveis]
                                
                                # Remover row_id se existir
                                if 'row_id' in df_download.columns:
                                    df_download = df_download.drop('row_id', axis=1)
                                
                                output_filename = f"editado_{selected_file}"
                                download_link = processor.create_download_link(df_download, output_filename)
                                st.markdown(download_link, unsafe_allow_html=True)
                                st.success("✅ Arquivo editado pronto para download!")
                        
                        with col2:
                            # Download do arquivo reprocessado (com colunas contábeis)
                            if st.button("📊 Baixar Arquivo Reprocessado (Contábil)", type="primary"):
                                # REPROCESSAR ARQUIVO COM NOVAS REGRAS DE DÉBITO/CRÉDITO
                                st.info("🔄 Reprocessando arquivo com as novas regras contábeis...")
                                
                                # Pegar o arquivo editado atual
                                df_para_reprocessar = st.session_state[edited_key].copy()
                                
                                # Filtrar apenas colunas originais e remover row_id
                                colunas_originais = ['Tipo', 'CodigoSingular', 'NomeSingular', 'TipoSingular', 'RegistroANS',
                                                   'CodigoTipoRecebimento', 'DescricaoTipoRecebimento', 'NumeroDocumento', 
                                                   'Descricao', 'ValorBruto', 'TaxaAdministrativa', 'Subtotal', 
                                                   'IRRF', 'OutrosTributos', 'ValorLiquido']
                                
                                colunas_disponveis = [col for col in colunas_originais if col in df_para_reprocessar.columns]
                                df_clean = df_para_reprocessar[colunas_disponveis].copy()
                            
                                # Remover row_id se existir
                                if 'row_id' in df_clean.columns:
                                    df_clean = df_clean.drop('row_id', axis=1)
                                
                                # REAPLICAR REGRAS CONTÁBEIS com os novos códigos usando process_dataframe
                                st.info("📋 Recalculando contas de Débito, Crédito e Histórico...")
                                
                                # Usar process_dataframe que já faz tudo: aplica regras contábeis E adiciona IRRF
                                df_export = processor.process_dataframe(df_clean)
                                
                                # Salvar arquivo reprocessado atualizado na sessão
                                reprocessed_key = f'reprocessed_{selected_file}'
                                st.session_state[reprocessed_key] = df_export
                                
                                # Atualizar também nos dados processados para relatórios
                                st.session_state.processed_dfs[selected_file] = df_export
                                
                                # Gerar download
                                output_filename = f"contabil_{selected_file}"
                                download_link = processor.create_download_link(df_export, output_filename)
                                st.markdown(download_link, unsafe_allow_html=True)
                                st.success("✅ Arquivo reprocessado com novas regras contábeis pronto para download!")
                                st.info("🎯 **Contas de Débito, Crédito e Histórico recalculadas** baseadas nos novos códigos selecionados")
                        
                        # Informações sobre os arquivos
                        st.info("""
                        📋 **Informações sobre os Downloads:**
                        - **Arquivo Editado**: Mantém formato original do CSV, ideal para reimportar no sistema
                        - **Arquivo Reprocessado**: Inclui colunas contábeis (Débito, Crédito, Histórico), pronto para contabilidade
                        - **Relatórios**: Agora usarão automaticamente o arquivo reprocessado com suas alterações
                        """)
                
                else:
                    st.warning("🔍 Nenhum registro encontrado com o filtro aplicado.")
                    st.write("💡 **Dica:** Tente usar termos diferentes ou remova o filtro para ver todos os registros.")

if __name__ == "__main__":
    main()

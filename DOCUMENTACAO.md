# Documentação Atualizada - Sistema de Processamento CSV Câmara de Compensação Uniodonto

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Estrutura do Projeto](#estrutura-do-projeto)
3. [Funcionalidades Implementadas](#funcionalidades-implementadas)
4. [Regras de Processamento](#regras-de-processamento)
5. [Interface do Sistema](#interface-do-sistema)
6. [Requisitos e Instalação](#requisitos-e-instalação)
7. [Guia de Uso](#guia-de-uso)
8. [Observações Importantes](#observações-importantes)

## 🎯 Visão Geral

Sistema desenvolvido em Python com Streamlit para processar arquivos CSV da Câmara de Compensação do Sistema Uniodonto, gerando lançamentos contábeis automatizados, relatórios financeiros e permitindo edição de dados.

### **Status do Sistema**: ✅ **TOTALMENTE FUNCIONAL**

O sistema está em produção e operando corretamente com todas as funcionalidades implementadas.

## 📁 Estrutura do Projeto

```
/
├── app.py                 # Aplicação principal (2853 linhas)
├── camaras/              # Diretório para arquivos CSV de entrada
│   ├── *.csv            # Arquivos CSV da câmara de compensação
│   └── exported_data.csv # Dados exportados
├── notebook/            # Jupyter notebooks para desenvolvimento
│   ├── camara.ipynb     # Notebook principal
│   └── backup*.py       # Backups do código
├── dicionario.csv       # Dicionário de dados das colunas
├── requirements.txt     # Dependências do projeto
├── run.sh              # Script de execução
├── log.txt             # Logs de execução
└── DOCUMENTACAO.md     # Esta documentação
```

## 🚀 Funcionalidades Implementadas

### **1. Processamento de Arquivos CSV** ✅
- **Upload múltiplo**: Suporte a múltiplos arquivos CSV simultâneos
- **Validação automática**: Verificação de colunas obrigatórias e integridade dos dados
- **Detecção de formato**: Identificação automática de diferentes formatos de CSV
- **Sincronização**: Correção automática de inconsistências entre código e descrição
- **Processamento contábil**: Geração automática de colunas Débito, Crédito e Histórico
- **Tratamento de IRRF**: Criação automática de lançamentos adicionais para IRRF
- **Exportação**: Download individual ou em lote (ZIP)

### **2. Geração de Relatórios Contábeis** ✅
- **Relatório Unificado**: Consolidação completa da câmara de compensação
- **Relatório de IRRF**: Análise específica de impostos retidos
- **Relatórios específicos**: 8 tipos de relatórios contábeis detalhados
- **Exportação PDF**: Relatórios formatados profissionalmente
- **Exportação CSV**: Dados estruturados para análise
- **Visualização web**: Interface interativa para visualização dos dados

### **3. Edição de Dados** ✅
- **Filtragem avançada**: Por tipo, singular, código e texto livre
- **Seleção flexível**: Individual ou em lote com checkboxes
- **Edição interativa**: Alteração de CodigoTipoRecebimento e DescricaoTipoRecebimento
- **Visualização imediata**: Mudanças visíveis instantaneamente na tabela
- **Preservação original**: Dados originais mantidos para referência
- **Download editado**: Arquivo CSV com alterações aplicadas

### **4. Interface Web Completa** ✅
- **Design responsivo**: Layout adaptável com 3 abas principais
- **Configuração personalizada**: Data de referência configurável
- **Opções avançadas**: Controle detalhado do processamento
- **Feedback visual**: Barras de progresso e indicadores de status
- **Documentação integrada**: Informações completas sobre regras e funcionamento

## ⚙️ Regras de Processamento

### **Estrutura do Arquivo CSV**
Colunas obrigatórias identificadas pelo sistema:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| Tipo | Texto | "A pagar" ou "A receber" |
| CodigoSingular | Número | Código único da entidade |
| NomeSingular | Texto | Nome da entidade |
| TipoSingular | Texto | "Operadora" ou "Prestadora" |
| RegistroANS | Texto/Número | Registro da ANS (opcional) |
| CodigoTipoRecebimento | Número | Código do tipo (1-6) |
| DescricaoTipoRecebimento | Texto | Descrição do tipo |
| NumeroDocumento | Texto | Número do documento |
| Descricao | Texto | Descrição da transação |
| ValorBruto | Decimal | Valor bruto da transação |
| TaxaAdministrativa | Decimal | Taxa administrativa |
| Subtotal | Decimal | Valor subtotal |
| IRRF | Decimal | Imposto retido |
| OutrosTributos | Decimal | Outros tributos |
| ValorLiquido | Decimal | Valor líquido final |

### **Mapeamento de Códigos**
Sistema utiliza mapeamento oficial:

| Código | Descrição |
|--------|-----------|
| 1 | Repasse em Pré-pagamento |
| 2 | Repasse em Custo Operacional |
| 3 | Taxa de Manutenção |
| 4 | Fundo de Marketing |
| 5 | Juros |
| 6 | Outros |

### **Regras de Lançamentos Contábeis**

#### **Débito - A Pagar**
- **Operadora**: 31731, 40507, 52631/52632, 52532, 51818, 51202
- **Prestadora**: 40140, 40140, 52631/52632, 52532, 51818, 51202

#### **Débito - A Receber**  
- **Operadora**: 19958, 85433, 84679, 84679, 84679, 19253
- **Prestadora**: 19253, 19253, 84679, 84679, 84679, 19253

#### **Crédito - A Pagar**
- **Operadora**: 90918, 90919, 21898/22036, 21898/22036, 51818, 90919
- **Prestadora**: 92003, 92003, 21898/22036, 21898/22036, 51818, 90919

#### **Crédito - A Receber**
- **Ambos**: 30203, 40413, 30069, 30071, 31426, 30127

#### **Histórico**
- **A Pagar**: 2005, 2005, 361/368, 365, 179, 2005
- **A Receber**: 1021, 1021, 361/368, 365, 179, 1021

### **Regras Especiais**

#### **LGPD e Atuário** (Código 5)
- **LGPD**: Débito 52129, Crédito 22036, Histórico 2005
- **ATUÁRIO**: Débito 52451, Crédito 22036, Histórico 2005

#### **Convenção/Convenção**
- **A Pagar**: Débito 53742
- **A Receber**: Débito 84679

## 🖥️ Interface do Sistema

### **Aba 1: Processamento de Arquivos**
- Upload de múltiplos arquivos CSV
- Configuração de data personalizada
- Opções avançadas de processamento
- Visualização prévia dos dados
- Processamento individual ou em lote
- Download de arquivos processados

### **Aba 2: Relatórios Contábeis**
- Seleção de arquivos processados
- Escolha do tipo de relatório
- Geração de relatórios específicos
- Visualização de estatísticas
- Download em PDF e CSV

### **Aba 3: Edição de Dados**
- Seleção do arquivo para edição
- Filtros por tipo, singular e código
- Busca por texto livre
- Seleção individual ou em lote
- Edição interativa de códigos
- Download do arquivo editado

## 💻 Requisitos e Instalação

### **Dependências**
```
streamlit
pandas
numpy
matplotlib
seaborn
reportlab
openpyxl
python-dateutil
pytz
pillow
```

### **Instalação**
```bash
# 1. Ativar ambiente virtual
source .venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar aplicação
streamlit run app.py --server.port 8502 --server.address 0.0.0.0
```

### **Execução via Script**
```bash
chmod +x run.sh
./run.sh
```

## 📖 Guia de Uso

### **1. Processamento de Arquivos**
1. Acesse a aba "Processamento de Arquivos"
2. Configure data se necessário
3. Faça upload dos arquivos CSV
4. Acompanhe o processamento
5. Baixe os arquivos processados

### **2. Geração de Relatórios**
1. Acesse a aba "Relatórios Contábeis"
2. Selecione arquivos processados
3. Escolha o tipo de relatório
4. Clique em "Gerar Relatórios"
5. Baixe os relatórios gerados

### **3. Edição de Dados**
1. Acesse a aba "Edição de Dados"
2. Selecione o arquivo para edição
3. Aplique filtros desejados
4. Selecione registros para editar
5. Altere códigos e descrições
6. Clique em "Processar Alterações"
7. Baixe o arquivo editado

## ⚠️ Observações Importantes

### **Formato dos Arquivos**
- **Separador**: Ponto e vírgula (;)
- **Codificação**: UTF-8
- **Decimais**: Vírgula como separador decimal
- **Datas**: Formato DD/MM/YYYY

### **Processamento**
- Sistema processa múltiplos arquivos simultaneamente
- Validações automáticas durante o processamento
- Correção automática de inconsistências
- Geração automática de lançamentos de IRRF

### **Edição de Dados**
- Alterações são aplicadas sobre dados originais
- Arquivo original é preservado para referência
- Mudanças são visíveis imediatamente na interface
- Download gera arquivo com mesma estrutura original

### **Segurança**
- Processamento local dos arquivos
- Não há armazenamento permanente de dados
- Dados temporários são limpos automaticamente
- Exportação segura dos relatórios

### **Relatórios Disponíveis**
1. **Taxas de Manutenção (3)** - Operadoras e Prestadoras
2. **Fundo de Marketing (4)** - Operadoras e Prestadoras  
3. **Multas e Juros (5)** - Operadoras e Prestadoras
4. **Outras (6)** - Operadoras e Prestadoras
5. **Pré-pagamento (1)** - Operadoras
6. **Custo Operacional (2)** - Operadoras
7. **Pré-pagamento (1)** - Prestadoras
8. **Custo Operacional (2)** - Prestadoras

## 🔧 Códigos das Contas Contábeis

### **Principais Contas de Débito**
- **85433**: Contraprestação assumida em Pós-pagamento
- **40507**: Despesas com Eventos/Sinistros
- **19958**: Contraprestação Corresponsabilidade Assumida Pré-pagamento
- **52631**: Taxa para Manutenção da Central
- **52532**: Propaganda e Marketing - Matriz
- **84679**: Outras Contas a Receber

### **Principais Contas de Crédito**
- **90919**: Intercâmbio a Pagar de Corresponsabilidade Cedida
- **21898**: Contrap. Corresp. Assumida Pós
- **22036**: Federação Paulista
- **30203**: Corresponsabilidade Assumida Pré
- **40413**: (-) Recup.Reemb. Contratante Assumida Pós-pagamento

### **Códigos de Histórico**
- **1021**: VL. N/NFF. INTERC. RECEB.ODONT
- **2005**: VL. S/NFF. INTERC. A PAGAR
- **361**: VL. TAXA MANUT. DA CENTRAL S/N
- **365**: VL. FUNDO DE MARKETING S/NFF
- **179**: VL. MULTAS/JUROS

---

## 📞 Suporte

Para dúvidas, problemas ou sugestões de melhorias:
- Consulte o código fonte em `app.py`
- Verifique logs em `log.txt`
- Entre em contato com a equipe de desenvolvimento

**Sistema em produção desde 2024 - Totalmente funcional e testado** 
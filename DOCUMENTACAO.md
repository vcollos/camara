# Documentação do Processador de Arquivos CSV da Câmara de Compensação - Uniodonto

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Estrutura do Projeto](#estrutura-do-projeto)
3. [Regras de Processamento](#regras-de-processamento)
4. [Funcionalidades](#funcionalidades)
5. [Requisitos Técnicos](#requisitos-técnicos)
6. [Instalação e Execução](#instalação-e-execução)
7. [Observações Importantes](#observações-importantes)

## 🎯 Visão Geral
Sistema desenvolvido em Python com Streamlit para processar arquivos CSV da Câmara de Compensação do Sistema Uniodonto, gerando lançamentos contábeis e relatórios financeiros.

## 📁 Estrutura do Projeto
```
/
├── app.py              # Aplicação principal
├── camaras/           # Diretório para arquivos CSV de entrada
├── dicionario.csv     # Dicionário de dados
├── requirements.txt   # Dependências do projeto
└── README.md         # Documentação principal
```

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
- "LGPD":
  - Débito: 52129
  - Crédito: 22036
  - Histórico: 2005
- "ATUARIO"/"ATUÁRIO":
  - Débito: 52451
  - Crédito: 22036
  - Histórico: 2005

## 🚀 Funcionalidades

### Principais Funcionalidades
1. **Processamento de Arquivos**
   - Leitura de arquivos CSV
   - Validação de dados
   - Processamento em lote

2. **Lançamentos Contábeis**
   - Cálculo automático de débito
   - Cálculo automático de crédito
   - Geração de histórico

3. **Relatórios**
   - Exportação em CSV
   - Exportação em PDF
   - Visualização na interface web

4. **Interface Web**
   - Upload de múltiplos arquivos
   - Visualização prévia
   - Download de relatórios

## 💻 Requisitos Técnicos

### Dependências
- Python 3.x
- Streamlit
- Pandas
- Matplotlib
- Seaborn
- ReportLab

## 📥 Instalação e Execução

### Passos para Instalação
1. Criar ambiente virtual Python:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # ou
   .venv\Scripts\activate  # Windows
   ```

2. Instalar dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Executar aplicação:
   ```bash
   streamlit run app.py
   ```

## ⚠️ Observações Importantes

### Formato dos Arquivos
1. Arquivos CSV devem seguir o formato especificado
2. Valores monetários no formato brasileiro
3. Datas no formato DD/MM/YYYY

### Processamento
1. Sistema processa múltiplos arquivos simultaneamente
2. Relatórios são gerados automaticamente
3. Validações são realizadas durante o processamento

### Segurança
1. Não armazena dados sensíveis
2. Processamento local dos arquivos
3. Exportação segura dos relatórios

---

Para mais informações ou suporte, consulte o código fonte ou entre em contato com a equipe de desenvolvimento. 
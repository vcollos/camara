# Processador de Arquivos CSV da Câmara de Compensação - Uniodonto

Este projeto é um aplicativo web desenvolvido em Python com Streamlit para processar arquivos CSV da Câmara de Compensação do Sistema Uniodonto, gerando lançamentos contábeis e relatórios financeiros.

## Funcionalidades

- **Processamento de arquivos CSV:**
  - Leitura de arquivos CSV com diferentes codificações e separadores.
  - Validação das colunas necessárias.
  - Cálculo das colunas contábeis `Debito`, `Credito` e `Historico` com base em regras específicas.
  - Tratamento de valores de IRRF, adicionando lançamentos contábeis específicos.
  - Formatação de datas e valores para o padrão brasileiro.

- **Geração de relatórios contábeis:**
  - Relatórios específicos para taxas de manutenção, marketing, multas, outras, pré-pagamento e custo operacional.
  - Exportação dos relatórios em CSV e PDF.
  - Visualização dos relatórios na interface web.
  - Download individual ou em lote (ZIP) dos relatórios.

- **Interface web com Streamlit:**
  - Upload de múltiplos arquivos CSV.
  - Visualização prévia dos dados processados.
  - Estatísticas básicas dos dados.
  - Configuração manual da data de referência.
  - Opções avançadas para controle do processamento.

## Estrutura do Projeto

```
/Users/vitorcollos/Documents/Dev/camara/
|-- app.py
|-- camaras/
|   |-- arquivos CSV de entrada
|-- exported_data.csv
|-- README.md
```

## Requisitos

- Python 3.x
- Streamlit
- Pandas
- Matplotlib
- Seaborn
- ReportLab

## Como Usar

1. Ative seu ambiente virtual.
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Execute o aplicativo Streamlit:

```bash
streamlit run app.py
```

4. Acesse a interface web no navegador.
5. Faça upload dos arquivos CSV da Câmara de Compensação.
6. Visualize, processe e baixe os relatórios contábeis.

## Contato

Para dúvidas ou melhorias, entre em contato com o desenvolvedor.

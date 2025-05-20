# Projeto de Análise e Exportação de Dados Financeiros

Este projeto consiste em um notebook Python (`camara.ipynb`) para análise e processamento de dados financeiros extraídos de arquivos CSV, com foco em dados de compensação financeira e IRRF.

## Descrição do Notebook

O notebook realiza as seguintes operações:

1. **Leitura dos Dados:**
   - Importa dados de um arquivo CSV localizado na pasta `camaras/`.
   - Utiliza o pandas para manipulação dos dados.

2. **Criação de Colunas Derivadas:**
   - Calcula colunas `Debito`, `Credito` e `Historico` com base em regras específicas relacionadas aos tipos de transações e códigos de recebimento.
   - Adiciona a coluna `DATA` com o último dia do mês anterior à data atual.
   - Converte a coluna `ValorBruto` para float e cria a coluna `valor`.
   - Cria a coluna `complemento` concatenando informações de outras colunas para facilitar a identificação.

3. **Tratamento de IRRF:**
   - Para registros com IRRF maior que zero, adiciona linhas específicas ao DataFrame de exportação com valores de débito, crédito e histórico ajustados.

4. **Formatação para Exportação:**
   - Converte a coluna `DATA` para o formato brasileiro `dd/mm/yyyy`.
   - Formata a coluna `valor` para usar vírgula como separador decimal, sem separadores de milhares.

5. **Exportação:**
   - Exporta os dados para um arquivo CSV `exported_data.csv` com separador ponto e vírgula (`;`).
   - O arquivo é escrito manualmente para evitar aspas nos campos, garantindo compatibilidade com sistemas que exigem esse formato.

## Estrutura do Projeto

```
/Users/vitorcollos/Documents/Dev/camara/
|-- camara.ipynb
|-- camaras/
|   |-- camara compensacao macae - 04.2025 - vcto 20.05.2025.csv
|   |-- exported_data.csv
|-- exported_data.csv
|-- README.md
```

## Requisitos

- Python 3.x
- Pandas

## Como Usar

1. Certifique-se de que o arquivo CSV de entrada está na pasta `camaras/`.
2. Abra o notebook `camara.ipynb` no Jupyter ou VS Code.
3. Execute as células para processar os dados e gerar o arquivo `exported_data.csv`.
4. O arquivo exportado estará no formato correto para importação em sistemas que exigem CSV com ponto e vírgula e vírgula decimal.

## Observações

- A exportação é feita manualmente para evitar aspas nos campos, especialmente no campo `valor`.
- A data é formatada para o padrão brasileiro.
- O notebook inclui tratamento específico para registros com IRRF.

## Contexto do Projeto

Este projeto trata da geração de lançamentos contábeis para o sistema de Contabilidade da Uniodonto, baseado nos dados da Câmara de Compensação.

### Sobre as colunas `Debito`, `Credito` e `Historico`

- Essas colunas representam as **contas contábeis** onde os registros financeiros serão lançados no sistema contábil.
- Cada registro indica um lançamento contábil, com a conta de débito, conta de crédito e o código do histórico para identificação do tipo de transação.

### Câmara de Compensação Uniodonto

- A Câmara de Compensação é um sistema criado dentro do Sistema Uniodonto para facilitar a troca de valores financeiros entre as Cooperativas Uniodonto.
- Funciona como uma conta corrente onde as Uniodontos registram os serviços prestados umas às outras para fins de pagamento.
- Os valores são processados e aceitos pela cooperativa devedora (dona do relatório), que também registra seus próprios valores.
- Ao final, são calculados os saldos de quem deve para quem e os pagamentos são processados.
- Paralelamente, este sistema gera os lançamentos contábeis de todas as movimentações e pagamentos que a Uniodonto dona do relatório realizou para as outras Uniodontos, incluindo pré-pagamentos, pós-pagamentos, taxas, serviços, e impostos como IRRF.

## Contato

Para dúvidas ou melhorias, entre em contato com o desenvolvedor.

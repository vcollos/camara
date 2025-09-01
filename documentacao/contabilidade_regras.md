# Regras Contábeis — Aplicativo Camara

Resumo
-------
Documento focado para contadores que precisam entender exatamente:
- quais contas são geradas para cada linha de um CSV da Câmara de Compensação;
- quais lançamentos adicionais (ex.: IRRF) são criados;
- regras especiais (CONVENÇÃO, LGPD, ATUÁRIO, mensalidade);
- como interpretar e validar os arquivos de saída gerados pelo sistema;
- exemplos práticos de entrada (CSV) → saída (CSV contábil) e PDF.

Arquivos relevantes
-------------------
- Índice geral: [[00_INDEX.md]]
- Mapa dos arquivos do projeto: [[mapa_de_arquivos.md]]
- Implementação das regras (código): `app.py` — funções chave:
  - `UniodontoCsvProcessor.calculate_debit`
  - `UniodontoCsvProcessor.calculate_credit`
  - `UniodontoCsvProcessor.calculate_history`
  - `UniodontoCsvProcessor.process_dataframe`
  - `UniodontoCsvProcessor.calculate_irrf_from_original_data`
  - `UniodontoCsvProcessor.is_irrf_record`
  - `UniodontoCsvProcessor.df_to_csv_string`
- Dicionário de códigos: variável `NOMES_CONTAS_CONTABEIS` em `app.py` (mapa código → descrição).
- Exemplos de saída (para validação): pasta `test_output/` (ex.: `taxas_manutencao.csv`, `relatorio_irrf.pdf`, `relatorios_contabeis.zip`).
- Arquivo de referência de campos (se existir): `dicionario.csv`.

Formato de entrada esperado
--------------------------
O sistema aceita CSVs variados e tenta mapear colunas automaticamente. O formato ideal (colunas obrigatórias após mapeamento) é:

- Tipo — "A pagar" ou "A receber"
- CodigoSingular — número identificador da entidade
- NomeSingular — nome da entidade (ex.: Uniodonto XYZ)
- TipoSingular — "Operadora" ou "Prestadora"
- CodigoTipoRecebimento — inteiro 1..6 (consulte mapeamento abaixo)
- DescricaoTipoRecebimento — texto (sincronizado com o código)
- ValorBruto — valor bruto do lançamento (monetário)
- IRRF — valor do IRRF (quando aplicável)
- Descricao — texto livre, usado para regras especiais e complemento

Observações sobre leitura:
- O sistema detecta formatos simplificados e tenta mapear colunas automaticamente.
- Valores monetários podem vir com vírgula (ex: "1.234,56") ou ponto (ex: "1234.56"); a função `normalize_value` normaliza e valida.
- Caso faltem colunas, `create_default_columns` insere padrões e avisa.

Mapeamento CódigoTipoRecebimento ↔ Descrição
--------------------------------------------
O mapeamento usado como fonte de verdade (em `UniodontoCsvProcessor.__init__`):

- 1: "Repasse em Pré-pagamento"
- 2: "Repasse em Custo Operacional"
- 3: "Taxa de Manutenção"
- 4: "Fundo de Marketing"
- 5: "Juros"
- 6: "Outros"

Se houver divergência entre código e descrição, o sistema prioriza o código e corrige a descrição. Se o código for inválido e a descrição for reconhecida, o sistema corrige o código. Em falhas, define como "Outros" (6).

Contas contábeis principais (resumo)
-----------------------------------
Abaixo estão as tabelas extraídas das funções de cálculo (`calculate_debit`, `calculate_credit`, `calculate_history`). Use estas tabelas para mapear lançamentos criados pelo sistema.

1) Regras de Débito (coluna Debito do CSV de saída)
- A pagar — Operadora:
  - 1 → 31731
  - 2 → 40507
  - 3 → 52631 (se NomeSingular == "UNIODONTO DO BRASIL") ou 52632 (outros)
  - 4 → 52532
  - 5 → 51818
  - 6 → 51202
- A pagar — Prestadora:
  - 1,2 → 40140
  - 3 → 52631 (UNIODONTO DO BRASIL) / 52632 (outros)
  - 4 → 52532
  - 5 → 51818
  - 6 → 51202
- A receber — Operadora:
  - 1 → 19958
  - 2 → 85433
  - 3,4,5 → 84679
  - 6 → 19253
- A receber — Prestadora:
  - 1,2 → 19253
  - 3,4,5 → 84679
  - 6 → 19253

2) Regras de Crédito (coluna Credito do CSV de saída)
- A pagar — Operadora:
  - 1 → 90918
  - 2 → 90919
  - 3 → 21898 (UNIODONTO DO BRASIL) / 22036 (outros)
  - 4 → 21898 (UNIODONTO DO BRASIL) / 22036 (outros)
  - 5 → 51818
  - 6 → 90919
- A pagar — Prestadora:
  - 1,2 → 92003
  - 3 → 21898 (UNIODONTO DO BRASIL) / 22036 (outros)
  - 4 → 21898 (UNIODONTO DO BRASIL) / 22036 (outros)
  - 5 → 51818
  - 6 → 90919
- A receber — Operadora / Prestadora:
  - 1 → 30203
  - 2 → 40413
  - 3 → 30069
  - 4 → 30071
  - 5 → 31426
  - 6 → 30127

3) Regras de Histórico (coluna Historico do CSV de saída)
- A pagar:
  - 1,2,6 → 2005
  - 3 → 361 (UNIODONTO DO BRASIL) / 368 (outros)
  - 4 → 365
  - 5 → 179
- A receber:
  - 1,2,6 → 1021
  - 3 → 33
  - 4 → 228
  - 5 → 30

Regras especiais
----------------
1) CONVENÇÃO / CONVENCAO (busca por "CONVENCAO" ou "CONVENÇÃO" em Descricao)
- Se aparecer:
  - Se Tipo == "A pagar":
    - Debito → 53742
    - Credito → 21898 ou 22036 (ver regras abaixo) — no código a regra de crédito mapeia para 21898/22036 baseada em "PAULISTA" (veja `calculate_credit`).
    - Historico → 2005
  - Se Tipo == "A receber":
    - Debito → 84679
    - Credito → 30203 / 40413 / ... conforme outros critérios
    - Historico → 1021

2) LGPD e ATUARIO (aplicados quando CodigoTipoRecebimento == 5 e descrição contém as palavras)
- Se CodigoTipoRecebimento == 5 e Tipo == "A receber":
  - Se "LGPD" em Descricao → Debito 84679 ; Credito 30173 ; Historico 1021
  - Se "ATUARIO"/"ATUÁRIO" em Descricao → Debito 84679 ; Credito 30088 ; Historico 1021
- Se Tipo == "A pagar":
  - Se "LGPD" em Descricao → Debito 52129 ; Credito 22036 ; Historico 2005
  - Se "ATUARIO"/"ATUÁRIO" em Descricao → Debito 52451 ; Credito 22036 ; Historico 2005

3) Mensalidade inconsistente (regra de verificação, não altera dados)
- Quando CodigoTipoRecebimento == 2 (Custo Operacional) e DescricaoTipoRecebimento == "Repasse em Custo Operacional" e Descricao contém "mensalidade"/"mensalidades":
  - Sistema marca o campo `complemento` com prefixo "*** Lançamento Inconsistente, verifique | ..." para sinalizar ao usuário/contador que verifique manualmente. NÃO altera o CodigoTipoRecebimento.

Como o IRRF é tratado
---------------------
Existem duas abordagens dentro do sistema:

1) IRRF como coluna nos dados originais
- `calculate_irrf_from_original_data` soma a coluna `IRRF` presente no CSV original (após normalização).
- Essa função devolve:
  - total_irrf, irrf_a_pagar, irrf_a_receber, registros_com_irrf, valores brutos e líquidos por tipo.
- O relatório unificado (`generate_unified_report`) e a seção de IRRF usam essa função para calcular valores líquidos.

2) Geração de lançamentos de IRRF automaticamente
- Em `process_dataframe`, para cada linha original com IRRF > 0 (após `normalize_value`), o sistema cria uma nova linha de lançamento contábil (lançamento adicional):
  - Se Tipo == "A pagar":
    - Debito = (valor do campo `Credito` do lançamento original)
    - Credito = 23476
    - Historico = 2341
  - Se Tipo == "A receber":
    - Debito = 15456
    - Credito = (valor do campo `Debito` do lançamento original)
    - Historico = 22
  - DATA = último dia do mês anterior (configuração padrão)
  - complemento inclui " | IRRF" ao final para identificação

- Essas linhas adicionais aparecem no CSV contábil gerado e são detectáveis pela função `is_irrf_record` (procura por "IRRF" no final do `complemento`).

Campos de saída (CSV contábil)
-----------------------------
O CSV contábil final salvo pelo sistema usa, por padrão, 6 colunas principais (na ordem):

- Debito — código da conta debitada
- Credito — código da conta creditada
- Historico — código do histórico
- DATA — data do lançamento (formatada dd/mm/YYYY) — por padrão último dia do mês anterior (configurável)
- valor — valor do lançamento (monetário, com vírgula decimal no CSV exportado)
- complemento — texto usado para entendimento (NomeSingular | DescricaoTipoRecebimento | Descricao | Tipo) — ou sinalização de inconsistencia; para lançamentos IRRF contém " | IRRF" no final

Além destas, o DataFrame de exportação preserva colunas auxiliares para filtros (quando exporta como "Arquivo Editado" ou exibe no Streamlit):
- Tipo, TipoSingular, NomeSingular, CodigoTipoRecebimento, DescricaoTipoRecebimento, Descricao, ValorBruto, IRRF

Exemplo prático (linha de entrada → lançamentos gerados)
-------------------------------------------------------
Entrada (exemplo de CSV original, colunas essenciais):
| Tipo | NomeSingular | TipoSingular | CodigoTipoRecebimento | DescricaoTipoRecebimento | ValorBruto | IRRF | Descricao |
|------|--------------|--------------|-----------------------|--------------------------|------------|------|-----------|
| A pagar | UNIODO EXEMPLO | Operadora | 3 | Taxa de Manutenção | 1.234,56 | 0 | Mensalidade Agosto |

Processamento:
- normalize_value("1.234,56") → 1234.56
- calculate_debit → para A pagar / Operadora / codigo 3 / NomeSingular != "UNIODONTO DO BRASIL" → Debito = 52632
- calculate_credit → A pagar / Operadora / codigo 3 / NomeSingular != "UNIODONTO DO BRASIL" → Credito = 22036
- calculate_history → codigo 3 / A pagar / NomeSingular != UNIODONTO DO BRASIL → Historico = 368
- DATA = último dia do mês anterior
- complemento = "UNIODO EXEMPLO | Taxa de Manutenção | Mensalidade Agosto | A pagar"
- IRRF = 0 → NÃO cria linha adicional de IRRF

Saída (linha no CSV contábil):
Debito;Credito;Historico;DATA;valor;complemento
52632;22036;368;30/07/2025;1.234,56;UNIODO EXEMPLO | Taxa de Manutenção | Mensalidade Agosto | A pagar

Exemplo com IRRF
----------------
Entrada:
| Tipo | NomeSingular | TipoSingular | CodigoTipoRecebimento | ValorBruto | IRRF | Descricao |
| A receber | CLINICA X | Prestadora | 1 | 2.500,00 | 50,00 | Pagamento Serviços |

Processamento:
- Gera o lançamento original com Debito/Credito/Histórico conforme regras (A receber / Prestadora / codigo 1):
  - Debito → 19253
  - Credito → 30203
  - Historico → 1021
  - valor = 2500.00
- IRRF > 0 → gera linha adicional:
  - Para Tipo "A receber": Debito = 15456 ; Credito = Debito do lançamento original (19253) ; Historico = 22 ; valor = 50.00 ; complemento inclui " | IRRF"
- Resultado: duas linhas no CSV contábil — a linha original e a linha de IRRF.

Verificação e controles para contadores
---------------------------------------
1) Conferência por totalizações
- Use `calculate_irrf_from_original_data` lógica (ou os relatórios gerados pelo aplicativo) para comparar:
  - soma dos `ValorBruto` por Tipo (A pagar / A receber)
  - soma da coluna IRRF original (se disponível)
  - soma dos lançamentos adicionais de IRRF no CSV contábil (procure `complemento` terminando em IRRF)

2) Validação de consistência Código ↔ Descrição
- O sistema já corrige inconsistências priorizando o código.
- Auditor: revisar o relatório de "inconsistências corrigidas" (o app exibe um expander com detalhes no Streamlit quando encontra divergências).

3) Sinais de alerta
- Complemento com prefixo "*** Lançamento Inconsistente, verifique" indica possível erro sem correção automática (verificar manualmente).
- Mensagens de erro/warning no Streamlit informam se houve alterações automáticas na coluna `CodigoTipoRecebimento`.

4) Conferir mapeamento de contas
- Sempre cruzar os códigos numéricos (ex.: 52631) com o dicionário presente em `NOMES_CONTAS_CONTABEIS` no código/fonte.
- Para facilitar, carregue `documentacao/mapa_de_arquivos.md` (em breve) ou consulte `test_output/` que traz exemplos reais.

Boas práticas para uso em produção / auditoria
----------------------------------------------
- Sempre conservar o arquivo CSV original importado.
- Antes de gerar contabilidade definitiva, valide no sistema:
  - resumo executivo (valores brutos, líquidos, IRRF)
  - relatórios por categoria (Taxas de Manutenção, Marketing, Multas/Juros, Outras, Pré-pagamento, Custo Operacional)
- Faça reconciliação entre:
  - Total bruto (soma de `ValorBruto` dos registros originais)
  - Total líquido (bruto - IRRF)
  - Total dos lançamentos contábeis (soma dos `valor` nos CSV contábeis, incluindo linhas IRRF adicionais)
- Revisar manualmente lançamentos com marcação de inconsistência.

Como identificar lançamentos de IRRF no CSV de saída
---------------------------------------------------
- Procurar `complemento` que contenha "IRRF" no final — a função `is_irrf_record` faz essa detecção no código.
- Alternativamente, procurar `Historico` com códigos 22 ou 2341 — o sistema atribui esses históricos às linhas de IRRF.

Uso dos relatórios gerados pelo sistema (visão contábil)
-------------------------------------------------------
- `generate_accounting_reports` → gera relatórios por categoria e um ZIP com vários PDFs e CSVs (ex.: `relatorios_contabeis.zip`).
- `generate_unified_report` → produz um PDF unificado com resumo executivo + detalhamento por categoria.
- `generate_irrf_report` → PDF focado em IRRF.
- PDFs contêm colunas com descrições das contas (Debito_Desc, Credito_Desc, Historico_Desc) para leitura humana, extraídas de `NOMES_CONTAS_CONTABEIS`.

Tópicos de troubleshooting mais comuns (resumo)
----------------------------------------------
1) Valores monetários incorretos após leitura
- Verifique se o CSV usa ponto-e-vírgula (;) como separador. O app tenta múltiplos encodings e separadores.
- Se valor convertido > 1.000.000 pode indicar erro de ponto/ vírgula; `normalize_value` tenta detectar e corrigir (ex.: dividir por 100 quando plausível).

2) CódigoTipoRecebimento alterado inesperadamente
- O app converte para numérico com `pd.to_numeric(..., errors='coerce').fillna(6).astype(int)` — se vierem valores não-numéricos, cai para 6 (Outros).
- Warnings são exibidos quando há alterações automáticas; revise o expander com detalhes.

3) Falta de colunas
- O app cria colunas padrão (com valores default) e emite avisos. Se faltar muitas colunas esperadas, o arquivo poderá ser rejeitado.

4) Relatórios vazios
- Os relatórios por categoria filtram por `CodigoTipoRecebimento` e `TipoSingular`. Se estiverem vazios, confirme que os campos existem e contêm exatamente os valores esperados (ex.: "Operadora" vs "operadora" — o app utiliza comparação direta e as strings devem bater).

Checklist para o contador antes de importar/usar arquivos contábeis gerados
-------------------------------------------------------------------------
- [ ] Conferir arquivo original e manter cópia imutável.
- [ ] Rodar processamento no app em modo pré-visualização e revisar warnings.
- [ ] Revisar lançamentos com marcador de inconsistencia (prefixo "*** Lançamento Inconsistente...").
- [ ] Conferir totais (Bruto, IRRF, Líquido) no resumo executivo do app.
- [ ] Verificar linhas de IRRF adicionais e garantir que os códigos (Debito/Credito/Historico) condizem com plano contábil.
- [ ] Exportar CSV contábil e abrir no sistema contábil para testes em ambiente de homologação.
- [ ] Gerar e salvar relatório PDF (unificado/IRRF/por categoria) para evidência de processamento.
- [ ] Registrar observações e qualquer ajuste manual em ticket ou changelog.

Exemplos de comandos / localização (para equipe técnica)
-------------------------------------------------------
- Código com regras: `app.py` (local: raiz do projeto).
- Exemplos de saída gerados: `test_output/` (ex.: `taxas_manutencao.csv`, `relatorio_irrf.pdf`).
- Para desenvolvimento local: veja `README.md` e `requirements.txt` para instalar dependências (`streamlit`, `pandas`, `reportlab`).

Glossário rápido
----------------
- Debito / Crédito: códigos contábeis numéricos usados no CSV de saída.
- Historico: código que descreve a natureza do lançamento (preenchido conforme regras).
- Complemento: campo textual com contexto (NomeSingular | DescricaoTipoRecebimento | Descricao | Tipo).
- IRRF: Imposto de Renda Retido na Fonte — pode estar presente na coluna original e também gerar lançamentos adicionais.
- CodigoTipoRecebimento: classificação do tipo de receita/despesa (1..6) — núcleo das regras de mapeamento.

Links úteis (documentação interna)
---------------------------------
- [[00_INDEX.md]] — índice principal da documentação
- [[mapa_de_arquivos.md]] — (recomendado ler em seguida) mapeia onde as regras estão implementadas no código
- [[banco_de_dados.md]] — (a criar) se houver persistência em banco, documentar tabelas e campos

Notas finais
-----------
Este documento descreve as regras implementadas atualmente no código disponível em `app.py` (commit atual). Se houver alterações no código (mapeamentos, novos casos especiais), atualize este arquivo. Posso gerar também um arquivo em formato CSV/Excel com todas as combinações (Tipo × TipoSingular × CodigoTipoRecebimento → Debito/Credito/Historico) para facilitar a revisão contábil. Deseja que eu gere essa matriz como arquivo dentro de `documentacao/`?

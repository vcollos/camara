# Regras de Negócio — Visão Contábil (linguagem para contadores)

Objetivo
--------
Documento escrito em linguagem contábil, sem trechos de código, para que contadores entendam de forma prática e direta como os lançamentos são gerados pelo sistema. Use este arquivo como referência operacional: o que debitar, o que creditar, quando surgem lançamentos adicionais (ex.: IRRF) e quais verificações realizar antes de importar os arquivos contábeis para seu ERP.

Resumo executivo (o essencial)
------------------------------
- Para cada linha do arquivo de entrada (CSV) o sistema gera um lançamento contábil principal com:
  - Conta do Débito
  - Conta do Crédito
  - Código de Histórico
  - Data (último dia do mês de referência)
  - Valor (bruto)
  - Complemento explicativo (Nome da entidade | Tipo de recebimento | Descrição | Tipo A pagar/A receber)
- Se houver IRRF informado na linha original, o sistema gera também um lançamento adicional somente para o imposto (lançamento de IRRF).
- O campo CodigoTipoRecebimento (valores 1 a 6) é a chave que determina a maioria das contas aplicadas.
- Existem regras especiais que sobrepõem mapeamentos comuns (ex.: CONVENÇÃO, LGPD, ATUÁRIO); essas regras alteram conta de débito, conta de crédito e histórico conforme descrito abaixo.

Mapeamento de Tipo de Recebimento (1..6)
----------------------------------------
Use essa referência para entender o significado contábil de cada código:

- 1 — Repasse em Pré-pagamento
- 2 — Repasse em Custo Operacional
- 3 — Taxa de Manutenção
- 4 — Fundo de Marketing
- 5 — Juros
- 6 — Outros

Regras gerais de contabilização (por visão contábil)
---------------------------------------------------
As regras são aplicadas com base em três variáveis principais:
1. Tipo: "A pagar" ou "A receber"
2. TipoSingular: "Operadora" ou "Prestadora"
3. CodigoTipoRecebimento: 1..6

A seguir os mapeamentos práticos (para uso contábil direto).

1) Lançamentos quando Tipo = A pagar
- Se TipoSingular = Operadora:
  - Código 1 (Pré-pagamento): Débito na conta 31731 / Crédito na conta 90918 / Histórico 2005
  - Código 2 (Custo Operacional): Débito na conta 40507 / Crédito na conta 90919 / Histórico 2005
  - Código 3 (Taxa de Manutenção):
    - Se o nome da entidade for "UNIODONTO DO BRASIL": Débito 52631 / Crédito 21898 / Histórico 361
    - Caso contrário: Débito 52632 / Crédito 22036 / Histórico 368
  - Código 4 (Marketing): Débito 52532 / Crédito 21898 ou 22036 conforme entidade / Histórico 365
  - Código 5 (Juros): Débito 51818 / Crédito 51818 / Histórico 179
  - Código 6 (Outros): Débito 51202 / Crédito 90919 / Histórico 2005

- Se TipoSingular = Prestadora:
  - Códigos 1 e 2: Débito 40140 / Crédito 92003 / Histórico 2005
  - Código 3: Débito 52631 (UNIODONTO DO BRASIL) ou 52632 (outros) / Crédito 21898 ou 22036 / Histórico 361 ou 368
  - Código 4: Débito 52532 / Crédito 21898 ou 22036 / Histórico 365
  - Código 5: Débito 51818 / Crédito 51818 / Histórico 179
  - Código 6: Débito 51202 / Crédito 90919 / Histórico 2005

2) Lançamentos quando Tipo = A receber
- Se TipoSingular = Operadora:
  - Código 1: Débito 19958 / Crédito 30203 / Histórico 1021
  - Código 2: Débito 85433 / Crédito 40413 / Histórico 1021
  - Código 3,4,5: Débito 84679 / Crédito 30069/30071/31426 conforme natureza / Histórico 33/228/30 ou 30 conforme regra
  - Código 6: Débito 19253 / Crédito 30127 / Histórico 1021

- Se TipoSingular = Prestadora:
  - Códigos 1 e 2: Débito 19253 / Crédito 30203/40413 / Histórico 1021
  - Código 3,4,5: Débito 84679 / Crédito 30069/30071/31426 / Histórico 33/228/30
  - Código 6: Débito 19253 / Crédito 30127 / Histórico 1021

Observações práticas:
- Quando o sistema apresenta duas opções de conta (ex.: 21898 / 22036), a escolha considera o nome da entidade (ex.: "UNIODONTO DO BRASIL" → 21898; outras entidades → 22036) ou busca palavras na descrição (ex.: "PAULISTA").
- Em lançamentos de juros (código 5) para alguns casos o sistema utiliza 51818 tanto em débito quanto em crédito ou combina conforme contexto; verifique a linha antes de importar.

Regras especiais detalhadas (casos que alteram as contas)
--------------------------------------------------------
1) CONVENÇÃO / CONVENCAO
- Quando a descrição contém "CONVENCAO" ou "CONVENÇÃO":
  - Se Tipo = A pagar:
    - Débito → conta 53742
    - Crédito → geralmente 21898 (se ligada à Federação/entidade específica) ou 22036 (outros)
    - Histórico → 2005
  - Se Tipo = A receber:
    - Débito → 84679
    - Crédito → conta correspondente à natureza (ex.: 30203/40413)
    - Histórico → 1021

Prática: marque essas linhas para revisão se houver dúvida sobre o destino do crédito (federação vs outra entidade).

2) LGPD e ATUÁRIO / ATUARIO
- Aplicável quando CodigoTipoRecebimento == 5 (Juros) e a Descrição contém "LGPD" ou "ATUARIO"/"ATUÁRIO".
- Se Tipo = A receber:
  - LGPD → Débito 84679 / Crédito 30173 / Histórico 1021
  - ATUÁRIO → Débito 84679 / Crédito 30088 / Histórico 1021
- Se Tipo = A pagar:
  - LGPD → Débito 52129 / Crédito 22036 / Histórico 2005
  - ATUÁRIO → Débito 52451 / Crédito 22036 / Histórico 2005

Prática: identificar pela palavra-chave na descrição; o sistema aplica automaticamente.

3) Mensalidade inconsistente (marcação, não correção)
- Quando CodigoTipoRecebimento == 2 (Custo Operacional) e DescricaoTipoRecebimento == "Repasse em Custo Operacional", mas a Descrição menciona "mensalidade" ou "mensalidades", o sistema NÃO altera o código. Em vez disso ele marca o campo complemento com o prefixo:
  - "*** Lançamento Inconsistente, verifique | {complemento}"
- Prática: esses registros devem ser revisados manualmente pelo contador para decidir se são pré-pagamento, taxa ou outro tratamento.

Tratamento do IRRF (imposto)
----------------------------
O sistema opera com duas frentes relativas ao IRRF:

1) Uso da coluna IRRF presente no arquivo original
- Se o arquivo original traz um valor em IRRF para uma linha, o sistema soma esses valores para fins de cálculo de líquidos e relatórios.
- Para obtenção do líquido: Valor Líquido = Valor Bruto − IRRF (quando aplicável).
- Relatórios apresentam total de IRRF por Tipo (A pagar / A receber) e total geral.

2) Criação de lançamentos de IRRF (lançamentos adicionais)
- Para cada registro original com IRRF > 0 o sistema cria uma nova linha de lançamento contábil destinada ao imposto:
  - Se Tipo = A pagar:
    - Débito = crédito do lançamento original (ou seja, representa apropriação contrária)
    - Crédito = 23476 (conta de IRRF a recolher)
    - Histórico = 2341
  - Se Tipo = A receber:
    - Débito = 15456 (conta de IRRF a compensar)
    - Crédito = débito do lançamento original
    - Histórico = 22
  - Complemento do lançamento de IRRF finaliza com " | IRRF" (para identificação)
- Prática: ao importar para o sistema contábil, trate as linhas com complemento contendo "IRRF" como lançamentos de imposto e faça a conciliação com guias/pagamentos.

Formato do arquivo contábil de saída (pronto para importar)
----------------------------------------------------------
O arquivo CSV gerado para contabilidade contém, por padrão, as seguintes colunas (ordem esperada):

1. Debito — código da conta debitada (inteiro)
2. Credito — código da conta creditada (inteiro)
3. Historico — código do histórico (inteiro)
4. DATA — data do lançamento (formato DD/MM/YYYY)
5. valor — valor do lançamento (monetário, vírgula como separador decimal, ex.: 1.234,56)
6. complemento — texto explicativo: "NomeSingular | DescricaoTipoRecebimento | Descricao | Tipo" ou "*** Lançamento Inconsistente, verifique | ..."

Campos auxiliares mantidos (para conferência)
- Tipo, TipoSingular, NomeSingular, CodigoTipoRecebimento, DescricaoTipoRecebimento, Descricao, ValorBruto, IRRF — são preservados internamente e podem acompanhar exportações em formatos auxiliares (arquivo editado).

Exemplos práticos (roteiro para o contador)
------------------------------------------
Exemplo 1 — Lançamento simples (sem IRRF)
- Entrada: A pagar / Operadora / CodigoTipoRecebimento = 3 / ValorBruto = 1.234,56 / Descricao = "Mensalidade Agosto"
- Processo:
  - Débito: 52632 (Taxa de Manutenção — entidade não Uniodonto do Brasil)
  - Crédito: 22036
  - Histórico: 368
  - Data: último dia do mês de referência
  - Complemento: "Nome da Entidade | Taxa de Manutenção | Mensalidade Agosto | A pagar"
- Ação do contador: conferir totals e importar.

Exemplo 2 — Lançamento com IRRF
- Entrada: A receber / Prestadora / CodigoTipoRecebimento = 1 / ValorBruto = 2.500,00 / IRRF = 50,00
- Processo:
  - Lançamento principal: Débito 19253 / Crédito 30203 / Histórico 1021 / valor 2.500,00
  - Lançamento IRRF gerado: Débito 15456 / Crédito 19253 / Histórico 22 / valor 50,00 / complemento termina em " | IRRF"
- Ação do contador: importar ambos; conciliar o IRRF com notas/guia.

Procedimento de verificação e conciliação (passo a passo)
---------------------------------------------------------
1. Preserve sempre o CSV original recebido do cliente/fornecedor.
2. Processar no aplicativo e revisar avisos/warnings exibidos (especialmente correções de código/descrição e marcações de inconsistência).
3. Verificar o Resumo Executivo:
   - Totais Bruto por Tipo (A pagar / A receber)
   - Totais de IRRF (A pagar / A receber)
   - Totais Líquidos (Bruto − IRRF)
4. Validar amostras de lançamentos (abrir CSV contábil gerado):
   - Confirmar que Débito + Crédito correspondem ao plano de contas esperado.
   - Confirmar que linhas de IRRF existem somente quando há valor em IRRF no original.
5. Filtrar e revisar registros marcados com "*** Lançamento Inconsistente" — ajustar antes de importar.
6. Importar para ambiente de homologação do ERP e rodar conciliações:
   - Conferir saldos por conta (principalmente contas de repasse, taxa e federação).
   - Conferir conta 23476 / 15456 (IRRF) contra documentos fiscais/guias de recolhimento.
7. Ao constatar divergência material, abrir ticket técnico e registrar evidência (CSV original, CSV contábil gerado e prints dos relatórios).

Recomendações operacionais
--------------------------
- Manter um controle de versão dos CSV originais e dos CSV contábeis gerados (data e usuário).
- Preferir importar primeiro em ambiente de homologação do ERP antes do ambiente produtivo.
- Configurar checklists mensais: reconciliar contas usadas pelo sistema (31731, 40507, 52631/52632, 90918/90919, etc.) com os lançamentos bancários e guias de recolhimento.
- Caso a contabilidade utilize Plano de Contas distinto, preparar um mapeamento de contas (arquivo de correspondência) para conversão automática antes da importação.

Referências internas
--------------------
- Documento técnico com lógica de regras (para desenvolvedores): [[contabilidade_regras.md]]
- Mapa do repositório e localização do código: [[mapa_de_arquivos.md]]
- Arquivos de exemplo gerados: pasta `test_output/` no repositório

Observações finais
-----------------
- Este documento resume a prática contábil esperada pelo sistema na versão corrente do código. Qualquer alteração na regra de negócios (por exemplo novos códigos de recebimento ou mudança em contas padrão) exige atualização imediata deste arquivo e comunicação para a equipe contábil.
- Caso deseje, posso gerar uma planilha (CSV/Excel) com a matriz completa: combinação (Tipo × TipoSingular × CodigoTipoRecebimento) → Débito / Crédito / Histórico, num formato que você possa importar direto para o seu ERP ou usar como checklist de homologação.

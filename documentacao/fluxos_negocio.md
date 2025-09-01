# Fluxos de Negócio — Aplicativo Camara

Objetivo
--------
Descrever os principais fluxos operacionais do sistema para usuários (contadores, analistas), operadores e desenvolvedores. Este documento descreve o passo-a-passo de cada fluxo, decisões, pontos de verificação e ações esperadas quando há exceções.

Atores
------
- Usuário / Operador: responsável por fazer upload dos arquivos CSV, revisar avisos e baixar relatórios.
- Contador: responsável por validar as regras contábeis, reconciliar resultados e aprovar importação ao ERP.
- Sistema (Camara): processamento automático e geração de artefatos (CSV/PDF/ZIP).
- Suporte/Desenvolvimento: corrige bugs, revisa logs e atualiza regras.
- Automação/CI (opcional): pipeline que roda testes e publica artefatos.

Visão geral dos fluxos
----------------------
1. Upload e Detecção
2. Validação e Normalização
3. Aplicação das Regras Contábeis
4. Geração de Artefatos (CSV contábil, PDFs, ZIP)
5. Revisão / Edição e Reprocessamento
6. Download / Entrega e Conciliação
7. Auditoria e Retenção de Evidências

Fluxo principal — Upload → Processamento → Download
----------------------------------------------------
1. Upload
   - Usuário acessa a aba "Processamento de Arquivos".
   - Faz upload de um ou mais CSVs (aceita `;` ou `,`, vários encodings).
   - O sistema faz leitura tentativa com múltiplos encodings/separadores.

2. Detecção e Mapeamento
   - Função `detect_csv_format` tenta:
     - Detectar se já está no formato da Câmara (colunas esperadas).
     - Detectar formato simplificado e mapear colunas.
     - Se não reconhecido, retorna erro explicando colunas encontradas.
   - Resultado: DataFrame mapeado ou mensagem de erro.

3. Validação e Normalização
   - `create_default_columns` preenche colunas ausentes com defaults (ex.: CodigoTipoRecebimento = 6).
   - `normalize_value` converte os valores monetários para float (BR/EN).
   - Warnings são exibidos para valores suspeitos (ex.: alteração de códigos, valores muito grandes).

4. Aplicação das Regras Contábeis
   - `sync_codigo_descricao` sincroniza Código ↔ Descrição.
   - Para cada linha:
     - `calculate_debit`, `calculate_credit`, `calculate_history` determinam contas e histórico.
   - Se IRRF > 0 (na coluna original), são geradas linhas adicionais de IRRF.
   - `complemento` é preenchido: "NomeSingular | DescricaoTipoRecebimento | Descricao | Tipo"
   - Registros com inconsistência detectada (ex.: `mensalidade` com código 2) recebem prefixo "*** Lançamento Inconsistente, verifique | ..."

5. Geração de Artefatos
   - `df_to_csv_string` formata CSV contábil (ponto-e-vírgula; vírgula decimal).
   - `generate_accounting_reports`, `generate_unified_report`, `generate_irrf_report` geram PDFs.
   - Arquivos salvos temporariamente e oferecidos para download (link base64 ou ZIP).

6. Revisão / Edição e Reprocessamento
   - Usuário pode editar dados na aba "Edição de Dados".
   - Após salvar, o app reprocessa o DataFrame com as novas regras e atualiza `st.session_state`.
   - Reprocessado substitui os resultados para geração de relatórios subsequentes.

7. Download / Entrega e Conciliação
   - Usuário baixa:
     - CSV contábil (pronto para importação)
     - PDFs de resumo e detalhamento
     - ZIP com todos os relatórios
   - Contador deve:
     - Validar totais brutos, IRRF e totais líquidos
     - Verificar lançamentos marcados como inconsistentes
     - Importar primeiro em homologação e reconciliar (contas e IRRF)

8. Auditoria e Retenção
   - Manter cópia do CSV original
   - Salvar PDFs e CSVs gerados como evidência (repositório de evidências ou storage central)
   - Se implementar persistência, gravar metadados do processamento (arquivo, usuário, warnings)

Fluxos alternativos / exceções
-----------------------------
A. Arquivo não reconhecido
   - Mensagem detalhando colunas encontradas e colunas esperadas.
   - Ação recomendada: renomear colunas ou ajustar fonte de dados; retornar ao upload.

B. Erro de parsing / encoding
   - App tenta encodings listados (`utf-8`, `latin1`, `iso-8859-1`, `cp1252`).
   - Se falhar, exibir amostra do conteúdo para o usuário identificar separador/encoding.

C. Valores monetários inválidos
   - `normalize_value` tenta heurísticas; se persistir, marca valor como 0 e exibe warning.
   - Ação: revisar arquivo fonte e corrigir os formatos.

D. Alterações automáticas em CodigoTipoRecebimento
   - App converte para numérico e corrige; se houve alteração, exibe warning com expander listando alterações.
   - Ação: contabilidade revisar e, se necessário, editar e reprocessar.

E. Geração de PDF falha (problemas com ReportLab)
   - Possíveis causas: falta de fontes ou dependências nativas.
   - Ação: checar logs de erro do container/VM; instalar dependências nativas ou usar container com base compatível.

Seqüência simplificada (texto)
------------------------------
1) Upload CSV → 2) detect_csv_format() → 3) create_default_columns() → 4) normalize_value() → 5) sync_codigo_descricao() → 6) calculate_debit/credit/history() → 7) adicionar IRRF rows → 8) montar df_export → 9) df_to_csv_string() / generate PDFs → 10) disponibilizar download

Pontos de verificação (checkpoints)
-----------------------------------
- Antes do processamento: confirmar backup do CSV original.
- Após mapeamento: checar se colunas esperadas existem.
- Após normalização: validar totais brutos vs valores originais (amostragem).
- Após aplicação das regras: revisar amostras para Débito/Credito/Historico.
- Antes da importação final: validar relatórios PDF e CSV em ambiente de homologação.

Recomendações por função
------------------------
- Operador:
  - Fazer upload somente de arquivos verificados.
  - Revisar mensagens de warning e inconsistências.
- Contador:
  - Conferir matriz (documentacao/matriz_contabil.csv) para entender contas aplicadas.
  - Reconciliar IRRF e ssalvar evidências.
- Desenvolvedor:
  - Monitorar logs e warnings, adicionar testes para novos casos.
  - Atualizar documentação quando alterar regras.
- Suporte:
  - Disponibilizar instruções de rollback e quem contatar em caso de divergência.

SLA e tempos esperados (recomendação)
------------------------------------
- Tempo de processamento esperado (para arquivos pequenos/medianos — <100k linhas): minutos.
- Para arquivos muito grandes (>100k linhas): avaliar processamento assíncrono (offload para worker).
- SLA de resposta para suporte: 24-48 horas em horário comercial (ajustar conforme contrato).

Mapeamento para o código (onde checar durante o fluxo)
------------------------------------------------------
- Upload / UI: `app.py` (blocos Streamlit nas abas)
- Detect / Map: `UniodontoCsvProcessor.detect_csv_format`, `detect_simplified_format`
- Defaults: `create_default_columns`
- Normalização: `normalize_value`
- Regras: `calculate_debit`, `calculate_credit`, `calculate_history`
- IRRF handling: `calculate_irrf_from_original_data`, adição de linhas em `process_dataframe`
- Export CSV: `df_to_csv_string`, `export_to_csv`
- PDFs: `generate_accounting_reports`, `generate_unified_report`, `generate_irrf_report`

Checklists práticos (para rodar no dia a dia)
---------------------------------------------
Pré-processamento
- [ ] Backup do CSV original
- [ ] Rodar upload em ambiente de homologação primeiro

Pós-processamento (antes de importar no ERP)
- [ ] Conferir total bruto vs relatório fonte
- [ ] Conferir total IRRF vs fonte
- [ ] Verificar registros com prefixo "*** Lançamento Inconsistente"
- [ ] Validar amostras aleatórias de Débito/Credito/Historico
- [ ] Exportar CSV contábil e importar para homologação

Observabilidade e logs
---------------------
- Habilitar logging detalhado durante homologação para capturar:
  - correções automáticas (sync)
  - linhas rejeitadas ou com parsing falho
  - erros de geração de PDF
- Armazenar logs centralmente (ELK/Loki) e agrupar por arquivo para investigação.

Links úteis
-----------
- Regras técnicas: [[contabilidade_regras.md]]
- Matriz de contas: `documentacao/matriz_contabil.csv`
- Mapas e pontos do código: [[mapa_de_arquivos.md]]
- Exemplo de testes/fixtures: [[testes.md]] / `test_output/`

Arquivo gerado em: 2025-08-29

# Troubleshooting — Aplicativo Camara

Objetivo
--------
Documento de suporte para resolver problemas comuns ao usar o app: erros de parsing, problemas de geração de PDF, falhas em relatórios, questões de encoding, performance e como coletar informações úteis para abrir chamados para a equipe de desenvolvimento.

Como usar este guia
-------------------
1. Identifique o sintoma (erro no UI, PDF não gerado, relatório vazio, discrepância de valores).
2. Consulte a seção correspondente para passos rápidos de diagnóstico.
3. Colete logs e arquivos solicitados antes de abrir um chamado.
4. Se for possível, reproduza em ambiente de homologação com arquivo de exemplo.

1. Erros ao ler CSV / Arquivo não reconhecido
---------------------------------------------
Sintoma: App exibe mensagem de "FORMATO NÃO RECONHECIDO" ou lista de colunas inesperadas.

Diagnóstico rápido:
- Verifique se o CSV tem separador `;` ou `,`. O app tenta ambos, mas às vezes precisa de correção manual.
- Abra o arquivo com um editor e confirme o encoding (UTF-8 vs Latin1).
- Verifique cabeçalhos: nomes esperados como `Tipo`, `Nome`, `Valor a Receber` devem estar presentes ou mapeáveis.

Correção:
- Renomear cabeçalhos para equivalentes conhecidos (ex.: `Nome` → `NomeSingular`, `Código` → `CodigoSingular`) ou usar o formato simplificado (ver `modelos_de_dados.md`).
- Salvar arquivo como UTF-8 e tentar novamente.
- Se persistir, enviar amostra (primeiras 50 linhas) para suporte.

Dados para abrir chamado:
- Arquivo CSV original
- Captura da tela do erro no Streamlit
- Saída do expander de diagnóstico (se disponível no UI)

2. Valores monetários errados (ponto/vírgula)
--------------------------------------------
Sintoma: Valores muito grandes (ex.: 123456000) ou valores truncados/invertidos.

Diagnóstico rápido:
- O `normalize_value` tenta detectar BR/EN e aplicar heurísticas (ex.: dividir por 100 se plausível).
- Verifique strings no CSV: presença de pontos de milhares e vírgula decimal (ex.: "1.234,56") vs "1,234.56".

Correção:
- Re-salvar CSV no formato uniforme (preferência: ponto decimal "." e sem separador de milhares, ou formato BR consistentemente "1.234,56").
- Se impossível, editar o CSV para remover caracteres não numéricos indesejados.
- Rodar processamento em um pequeno subset e verificar `ValorBruto` no preview.

Dados para abrir chamado:
- Linha(s) problemática(s) do CSV
- Screenshot mostrando valor antes e depois do processamento

3. Inconsistências CódigoTipoRecebimento ↔ Descrição
----------------------------------------------------
Sintoma: Mensagens de correção automática; registro listado no expander com descrição/código alterado.

Diagnóstico:
- O app prioriza o código como fonte da verdade e corrige a descrição. Se o código for inválido, tenta corrigir baseado na descrição, senão define como 6 (Outros).

Ação:
- Se a correção não refletir a intenção do cliente, editar o CSV (coluna `CodigoTipoRecebimento`) ou usar a aba de edição para corrigir e reprocessar.
- Registrar as ocorrências e revisar com a área responsável pelos dados de origem.

Dados para abrir chamado:
- Exemplo de registro com divergência (linha original)
- Screenshot do expander das correções

4. Relatórios vazios (por categoria)
------------------------------------
Sintoma: Relatório de Taxas/Pré-pagamento aparece sem registros.

Diagnóstico:
- Conferir os filtros aplicados no relatório (ex.: CodigoTipoRecebimento e TipoSingular).
- Verificar se os dados processados contêm as colunas e valores esperados (ex.: `TipoSingular` exatamente "Operadora").

Ação:
- Revisar colunas do CSV e mapear valores para os esperados.
- Reprocessar e conferir o DataFrame consolidado (na UI ou através de `st.session_state.processed_dfs`).

Dados para abrir chamado:
- CSV original
- Print do DataFrame processado que mostra colunas e valores
- Descrição do relatório esperado vs resultado

5. Erro ao gerar PDF / PDFs corrompidos
--------------------------------------
Sintoma: `generate_accounting_reports` / `generate_unified_report` falha, PDF não abre ou ReportLab lança exceção.

Diagnóstico:
- Verificar logs de erro (traceback). Problemas comuns:
  - Falta de fontes ou dependências nativas no ambiente/container.
  - Problemas com imagens (logo remoto ou caminho inválido).
  - Conteúdo muito longo em células não tratado adequadamente.

Ação:
- Conferir se o arquivo de logo está acessível (`_get_logo_png_path`) — o código tenta usar um caminho local ou URL remoto.
- Testar gerar o PDF em máquina local com `tests/generate_sample_pdf.py` para reproduzir erro.
- Se ocorrer erro de font, instalar pacotes de fonte no container (ex.: `fonts-liberation` em Debian) ou fornecer caminho para fontes suportadas.

Dados para abrir chamado:
- Traceback completo
- Exemplo pequeno de CSV que reproduz falha
- Versão do OS/container (se aplicável)

6. Exceções e crashes (memória / tempo)
---------------------------------------
Sintoma: Processo morre, uso altíssimo de RAM ou tempo de processamento muito longo.

Diagnóstico:
- Tamanho do arquivo CSV (nº de linhas).
- Se o processamento é feito em memória e DataFrame é muito grande, a aplicação pode ficar sem memória.

Ação:
- Processar arquivos grandes em chunks (dividir em arquivos menores).
- Considerar implementar processamento em lote assíncrono (job worker).
- Para ambiente Docker/K8s, aumentar recursos (memória/CPU) ou configurar limite de upload.

Dados para abrir chamado:
- Tamanho do CSV e número de linhas
- Logs de uso de memória (se disponível)
- Configuração de container/VM

7. Problemas na detecção do separador
-------------------------------------
Sintoma: Colunas aparecem concatenadas em uma única coluna.

Correção:
- Abrir CSV num editor e confirmar separador.
- Forçar separador correto salvando como `;` ou `,`.
- Se o CSV é gerado por sistema legado, ajustar exportação para usar `;`.

8. Problemas de permissão ao salvar arquivos
--------------------------------------------
Sintoma: Erro ao gravar PDF/CSV no disco.

Diagnóstico:
- Verificar permissões do diretório temporário (tempfile.mkdtemp()) ou do diretório customizado passado como `output_dir`.

Ação:
- Ajustar permissões ou fornecer `output_dir` diferente com permissão de escrita.
- Em container, mapear volumes com permissões corretas.

9. Logs úteis para investigação
-------------------------------
Sempre coletar:
- Output do terminal do Streamlit (stdout/stderr)
- Mensagens que aparecem na UI (warnings/expander)
- Tracebacks completos (se ocorrerem)
- Exemplo do CSV (preferencialmente anônimo) que reproduz o problema
- Tempo/URL e user-id (se aplicável)

10. Como abrir chamado (modelo)
-------------------------------
- Título: [Camara] <Resumo curto do problema>
- Descrição:
  - Passos para reproduzir
  - Arquivos anexados (CSV original, screenshot, traceback)
  - Ambiente (local / container / staging / produção)
  - Prioridade (bloqueador / alta / média / baixa)
- Anexos essenciais:
  - CSV original
  - Log do Streamlit / traceback
  - PDF/CSV gerado (se aplicável)
  - Versão do commit (hash) do repositório

11. Contato e SLA
-----------------
- Para problemas críticos de produção: abrir chamado com prioridade alta e marcar equipe responsável.
- Para suporte regular: abrir chamado no backlog e atribuir acordo de SLA definido pelo time.

Referências rápidas
------------------
- `app.py` — seções de parsing, regras e geração de relatórios
- `test_output/` — fixtures para reproduzir casos
- `testes.md` — como montar fixtures e reproduzir casos de teste

Arquivo gerado em: 2025-08-29

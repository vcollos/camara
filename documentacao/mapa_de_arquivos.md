# Mapa de Arquivos — Aplicativo Camara

Objetivo
--------
Mapa técnico do repositório para desenvolvedores e contadores: descreve cada arquivo/pasta relevante, para que serve, onde estão as regras contábeis e como navegar no código. Use este arquivo como referência rápida para localizar implementação, testes e exemplos de saída. Links para outros documentos da documentação: [[00_INDEX.md]] e [[contabilidade_regras.md]].

Visão geral da raiz do projeto
------------------------------
Estrutura (arquivos e pastas principais presentes no repositório):

- app.py
  - Descrição: Aplicação principal em Streamlit que contém toda a lógica de processamento de CSV, normalização, regras contábeis, geração de relatórios (CSV, PDF) e interface web.
  - Contém as classes e funções centrais:
    - Classe: `UniodontoCsvProcessor`
      - Métodos importantes:
        - `__init__` — mapeamentos iniciais (CodigoTipoRecebimento ↔ Descricao) e dicionário de nomes de contas `NOMES_CONTAS_CONTABEIS`.
        - `sync_codigo_descricao(df)` — sincroniza/corrige CódigoTipoRecebimento e DescricaoTipoRecebimento.
        - `normalize_value(value)` — normalização robusta de valores monetários.
        - `process_dataframe(df)` — pipeline principal que aplica regras, cria colunas Debito/Credito/Historico, adiciona linhas IRRF e monta DataFrame de exportação.
        - `calculate_debit(row)`, `calculate_credit(row)`, `calculate_history(row)` — regras de mapeamento para contas e histórico (a lógica contábil está nestes métodos).
        - `create_download_link`, `df_to_csv_string` — helpers para exportação (CSV em formato brasileiro).
        - `generate_accounting_reports`, `generate_unified_report`, `generate_irrf_report` — geração de PDFs e CSVs por categoria e resumo.
        - `is_irrf_record`, `calculate_irrf_from_original_data`, `calculate_irrf_by_complemento` — lógica de identificação e sumarização de IRRF.
        - Helpers de PDF: `truncate_lines`, `format_currency`, `_draw_logo`, `_get_logo_png_path`.
  - Observações:
    - Toda a regra de negócio contábil está dentro de `UniodontoCsvProcessor`. Para alterações das regras contábeis, editar `calculate_debit`, `calculate_credit` e `calculate_history`.
    - Gera avisos e expander no Streamlit quando corrige inconsistências entre código/descrição.

- dicionario.csv
  - Descrição: (arquivo presente) provável dicionário de campos/códigos. Útil para mapear colunas do CSV de entrada para os campos esperados pela aplicação. Verificar conteúdo para enriquecer a documentação de campos.

- requirements.txt
  - Descrição: dependências do projeto (ex.: streamlit, pandas, reportlab, seaborn, matplotlib, etc.).
  - Uso: criar ambiente virtual e instalar dependências via `pip install -r requirements.txt`.

- README.md
  - Descrição: informações gerais do projeto (verificar para instruções de setup e execução local).

- .env
  - Descrição: arquivo de ambiente (presente). Pode conter variáveis sensíveis/paths. Observação: `app.py` não usa diretamente um carregador explícito de .env no código atual; caso necessário, adicionar `python-dotenv` e centralizar configurações (ex.: PATHs, URL do logo, ajustes).

Pastas de exemplos e testes
---------------------------
- test_output/
  - Conteúdo: exemplos de saída já gerados pelo sistema:
    - outras.csv / outras.pdf
    - pre_pagamento_prestadoras.csv / pre_pagamento_prestadoras.pdf
    - relatorio_camara_compensacao.pdf
    - relatorio_irrf.pdf
    - relatorios_contabeis.zip
    - resumo_relatorios.pdf
    - taxas_manutencao.csv / taxas_manutencao.pdf
  - Uso: referência visual e de formato para validar regressões e resultados de contabilidade.
  - Recomendações: manter estes arquivos como fixtures para QA e contabilidade (comparar totais).

- tests/
  - tests/generate_sample_pdf.py
    - Descrição: script de teste usado para gerar PDFs de exemplo. Útil para verificar layout e formatação de relatórios sem Streamlit.
    - Uso: executar localmente (verificar dependências).

Código auxiliar / assets
-----------------------
- imagem/
  - logo_contag.png, logo_contag.svg
  - Observação: `app.py` tenta usar um PNG remoto (https://collos.com.br/...) em `_get_logo_png_path` — essa função também verifica se o caminho existe localmente. Ajuste se quiser usar o logo local.

Configurações e execução
-----------------------
- Execução local:
  - Criar venv: `python -m venv .venv`
  - Ativar e instalar: `pip install -r requirements.txt`
  - Rodar app: `streamlit run app.py`
- Variáveis/config:
  - `processor.last_day_of_previous_month` pode ser sobrescrito via interface (data manual).
  - Se desejar mover configurações (por exemplo, URL do logo, paths de saída), crie loader de `.env` e passe para `UniodontoCsvProcessor`.

Onde estão implementadas as regras contábeis
--------------------------------------------
Principais pontos no código:
- Mapeamentos e nomes de contas: variável global `NOMES_CONTAS_CONTABEIS` (topo de `app.py`) — atualize este dicionário para ajustar descrições exibidas nos PDFs.
- Regras de mapeamento (lógica decisória):
  - `calculate_debit(self, row)` — devolve código de débito baseado em Tipo, TipoSingular, CodigoTipoRecebimento, NomeSingular, e conteúdo de Descricao (CONVENCAO, LGPD, ATUARIO).
  - `calculate_credit(self, row)` — devolve código de crédito (mesmas variáveis consideradas).
  - `calculate_history(self, row)` — devolve código de histórico.
- Normalização de valores:
  - `normalize_value` — trata formatos BR/EN, remove símbolos, detecta erros comuns (divisão por 100 quando plausível).
- Criação de lançamentos IRRF:
  - Em `process_dataframe` depois do cálculo inicial, para cada linha onde IRRF > 0 cria uma linha adicional com regras específicas de débito/ crédito/ histórico.
- Identificação de registros IRRF:
  - `is_irrf_record` — regex para detectar complemento terminando com "IRRF".
- Exportação:
  - `df_to_csv_string` — formata CSV com ponto-e-vírgula e vírgula decimal, cuida de complementos, formatação monetária, e preserva colunas originais quando exportando "Arquivo Editado".

Onde procurar quando precisar alterar/estender
---------------------------------------------
- Adicionar novos tipos de recebimento / mudança de códigos:
  - Atualizar `codigo_descricao_map` no `__init__` se houver novos códigos.
  - Atualizar `calculate_debit`, `calculate_credit`, `calculate_history` para incluir novos mapeamentos.
  - Atualizar `NOMES_CONTAS_CONTABEIS` para incluir descrições e facilitar PDFs.
- Ajustes de parsing:
  - `detect_csv_format`, `detect_simplified_format` — pontos para melhorar heurísticas de mapeamento de colunas de entrada.
- Relatórios:
  - `generate_accounting_reports`, `generate_unified_report`, `generate_irrf_report` — para mudanças no layout do PDF, colunas de resumo, e lógica de totalização.
- Testes:
  - Adicionar fixtures em `test_output/` e scripts em `tests/` para cobrir novos cenários (por ex.: novos tipos especiais como LGPD/NOVO_TIPO).

Sugestões de documentação adicional (próximos arquivos recomendados)
-------------------------------------------------------------------
- [[banco_de_dados.md]] — (se houver persistência) mapear tabelas, colunas e migrações.
- [[modelos_de_dados.md]] — descrever estruturas de DataFrame esperadas e colunas auxiliares criadas (Debito, Credito, Historico, DATA, valor, complemento).
- [[fluxos_negocio.md]] — fluxos: subir CSV → validação → processamento → gerar CSV contábil → homologação → enviar ao sistema contábil.
- [[guias_de_desenvolvimento.md]] — setup local, comandos úteis e como rodar testes.
- [[obsidian_index.md]] — mapa de links para Obsidian (tags, backlinks automáticos).

Boas práticas ao editar código-fonte
------------------------------------
- Sempre atualizar também os documentos Markdown em `documentacao/` quando mudar regras contábeis.
- Para alterações nas regras contábeis:
  - Adicionar testes unitários que cubram combinações (Tipo × TipoSingular × CodigoTipoRecebimento) e casos especiais (LGPD, ATUARIO, CONVENCAO).
  - Reprocessar `test_output/` e versionar novos arquivos de exemplo para QA.
- Antes de deploy:
  - Validar PDFs gerados e conferir que o CSV contábil possui os formatos esperados pelo ERP/rotina contábil.

Links rápidos
-------------
- Índice da documentação: [[00_INDEX.md]]
- Regras contábeis detalhadas: [[contabilidade_regras.md]]

---

Arquivo gerado em: 2025-08-29

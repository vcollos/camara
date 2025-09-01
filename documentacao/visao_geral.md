# Visão Geral — Aplicativo Camara

Resumo
------
Aplicativo "Camara" é uma ferramenta em Python + Streamlit para processar arquivos CSV da "Câmara de Compensação" (ex.: Uniodonto), aplicar regras contábeis predefinidas e gerar artefatos contábeis prontos para conferência: CSV contábil (formatado), relatórios PDF por categoria, relatório unificado e pacote ZIP com todos os relatórios. O sistema normaliza valores, detecta formatos simplificados, corrige inconsistências mínimas e sinaliza casos que exigem revisão manual.

Objetivo do produto
-------------------
- Automatizar a conversão de relatórios da câmara em lançamentos contábeis compatíveis com sistemas de contabilidade.
- Reduzir retrabalhos manuais e erros de mapeamento de contas.
- Entregar evidências (PDFs) e CSVs prontos para homologação e importação.
- Fornecer transparência e rastreabilidade das regras aplicadas (audit trail via complementos e relatórios).

Público-alvo
------------
- Contabilidade (analistas e coordenadores) — para homologação e importação dos lançamentos.
- Analistas financeiros — para conferência de totais e IRRF.
- Desenvolvedores / DevOps — para manutenção, extensão e implantação do sistema.
- Equipe de QA — para validar regras e fixtures.

Funcionalidades principais
--------------------------
- Upload de múltiplos CSVs (interface Streamlit).
- Detecção automática de formato e mapeamento de colunas.
- Normalização de valores monetários (suporta formatos BR/EN).
- Regras contábeis automáticas para Débito, Crédito e Histórico por combinação:
  Tipo (A pagar / A receber) × TipoSingular (Operadora / Prestadora) × CodigoTipoRecebimento (1..6).
- Regras especiais (CONVENÇÃO, LGPD, ATUÁRIO, marcação de mensalidades inconsistentes).
- Geração automática de lançamentos de IRRF quando aplicável.
- Exportação de CSV contábil com formatação BR (ponto-e-vírgula e vírgula decimal).
- Geração de PDFs: relatórios por categoria, relatório unificado e relatório IRRF.
- Download individual e em lote (ZIP).
- Edição básica dos dados originais e reprocessamento automático das regras contábeis.

Entradas e saídas
-----------------
- Entrada: um ou mais arquivos CSV (separador `;` ou `,`, múltiplos encodings suportados).
- Saída:
  - CSV contábil (colunas: Debito;Credito;Historico;DATA;valor;complemento).
  - PDFs por categoria e um PDF unificado.
  - ZIP contendo PDFs e CSVs.
  - Arquivos de exemplo/fixtures em `test_output/`.

Visão do fluxo de alto nível
---------------------------
1. Usuário faz upload do(s) CSV(s).
2. App detecta/normaliza formato e colunas.
3. Aplica regras de negócio (Debito/Credito/Historico, complementos, IRRF).
4. Gera DataFrame de exportação e arquivos (CSV/PDF).
5. Usuário revisa avisos e baixa os artefatos; pode editar e reprocessar.

Dependências técnicas
---------------------
- Linguagem: Python 3.9+ recomendado.
- Framework web: Streamlit.
- Manipulação de dados: pandas, numpy
- Geração de PDFs: reportlab
- Visualização auxiliares: matplotlib, seaborn (opcional)
- Outras libs: io, base64, zipfile, re, datetime
- Arquivos: `requirements.txt` lista as dependências.

Estrutura mínima para executar localmente
----------------------------------------
1. Criar ambiente:
   python -m venv .venv
   source .venv/bin/activate  (macOS / Linux) ou .venv\Scripts\activate (Windows)
2. Instalar dependências:
   pip install -r requirements.txt
3. Rodar:
   streamlit run app.py
4. Acessar a interface web (URL padrão fornecida pelo Streamlit).

Restrições e pressupostos
-------------------------
- Não há banco de dados persistente no código atual; todo processamento é feito em memória e arquivos temporários.
- O sistema presume que o mapeamento lógico (TipoSingular, CodigoTipoRecebimento etc.) esteja coerente; aplica correções mínimas, mas sinaliza inconsistências.
- O plano de contas (códigos contábeis) é mantido no dicionário `NOMES_CONTAS_CONTABEIS` em `app.py`. Alterações no plano exigem atualização deste dicionário e testes.
- Arquivos originais devem ser preservados; o app cria versões processadas e reprocessadas.

Métricas e evidências para processos de qualidade
-----------------------------------------------
- Fixtures em `test_output/` para regressão visual e numérica.
- Logs/avisos exibidos no Streamlit para cada correção automática (sincronização código/descrição, conversão numérica).
- PDF e CSV gerados para prova e auditoria; sugerimos armazenar artefatos em repositório de evidências.

Integrações e pontos de atenção operacionais
-------------------------------------------
- Logo: função `_get_logo_png_path` verifica localmente e usa uma URL remota; ajustar se desejar usar logo local.
- Exportação CSV: formatação brasileira (ponto-e-vírgula; vírgula decimal) — verifique compatibilidade com ERP antes de importação.
- Reprocessamento: edição pelo usuário gera reprocessamento automático e substitui os DataFrames em `st.session_state` para geração de relatórios subsequentes.

Próximos passos recomendados
---------------------------
- Criar `modelos_de_dados.md` (estruturar DataFrames de entrada/saída).
- Gerar `arquitetura.md` (diagrama técnico e descrição de componentes) — será criado em seguida.
- Adicionar testes unitários cobrindo combinações críticas (Tipo × TipoSingular × CodigoTipoRecebimento) e casos especiais (LGPD/ATUARIO/CONVENCAO).
- Padronizar e versionar fixtures em `test_output/` para CI.
- Se for necessário armazenamento persistente (logs, histórico de processamento), projetar camada de persistência (DB) e migrar parte do estado para o banco.

Links úteis
-----------
- Índice da documentação: [[00_INDEX.md]]
- Regras contábeis detalhadas (técnico): [[contabilidade_regras.md]]
- Regras de negócio (linguagem contábil): [[regras_de_negocio.md]]
- Mapa de arquivos: [[mapa_de_arquivos.md]]

Arquivo gerado em: 2025-08-29

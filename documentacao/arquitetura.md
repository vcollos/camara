# Arquitetura — Aplicativo Camara

Visão Geral
-----------
Documento descreve a arquitetura técnica do sistema "Camara": componentes, fluxos de dados, interfaces, pontos de integração e recomendações para deploy e evolução. O objetivo é dar a qualquer desenvolvedor/engenheiro infraestrutura suficiente contexto para replicar, operar ou alterar o sistema em produção.

Componentes principais
----------------------
1. Interface Web (Streamlit)
   - Função: upload de CSVs, visualização de prévias, configuração (data), exibição de warnings, controle de edição e gatilho para geração de relatórios.
   - Localização: `app.py` (parte UI com tabs).
   - Requisitos: roda como aplicação WSGI/ASGI simples via Streamlit (servidor web próprio do Streamlit).

2. Camada de Processamento (UniodontoCsvProcessor)
   - Função: toda a lógica de negócio:
     - Detecção/mapeamento de formatos CSV
     - Normalização de valores monetários
     - Sincronização CódigoTipoRecebimento ↔ DescricaoTipoRecebimento
     - Cálculo de Débito/Crédito/Histórico
     - Criação de lançamentos IRRF adicionais
     - Geração de DataFrames de exportação e CSV strings
   - Localização: classe `UniodontoCsvProcessor` dentro de `app.py`.

3. Exportadores / Geradores de Relatório
   - CSV: `df_to_csv_string`, `export_to_csv` — formatação BR (ponto-e-vírgula, vírgula decimal).
   - PDF: `generate_accounting_reports`, `generate_unified_report`, `generate_irrf_report` — usa ReportLab para montar PDF com tabelas e formatos legíveis.
   - ZIP: criação de ZIP com PDFs e CSVs para download em lote.
   - Localização: métodos dentro de `UniodontoCsvProcessor` em `app.py`.

4. Armazenamento temporário
   - O sistema usa diretórios temporários (tempfile.mkdtemp()) para gravar PDFs/CSVs antes de empacotar em ZIP e enviar ao cliente.
   - Não há persistência de longo prazo por padrão (arquivo `.env` pode ser usado para ajustar paths se necessário).

5. Sessão de usuário (Streamlit session_state)
   - Utilizada para:
     - Guardar DataFrames processados (`st.session_state.processed_dfs`)
     - Guardar versões editadas e reprocessadas
     - Manter estado entre abas (processamento, relatórios, edição)
   - Importante: não é persistente entre reinicializações do servidor.

6. Assets e configurações
   - `imagem/` — logos
   - `.env` — (presente) recomenda-se usar para URL do logo, paths e chaves sensíveis se integrar a serviços externos.
   - `requirements.txt` — dependências

Fluxo de dados (high-level)
---------------------------
1. Upload: usuário envia um ou mais arquivos CSV via UI.
2. Parsing: backend tenta múltiplos encodings e separadores; detecta formato e mapeia colunas.
3. Normalização: `normalize_value` trata valores monetários e conversões inválidas.
4. Regras: `calculate_debit`, `calculate_credit`, `calculate_history` aplicam lógica de negócio; `sync_codigo_descricao` corrige inconsistências.
5. Pós-processamento: criação de colunas `Debito`, `Credito`, `Historico`, `DATA`, `valor`, `complemento`; criação de linhas IRRF quando aplicável.
6. Exportação: geração de CSVs e PDFs, gravação temporária e expedição para o usuário (download link base64 ou ZIP).
7. Edição: usuário pode editar dados originais; o app salva em session_state, reprocessa e substitui DataFrames para geração de relatórios subsequentes.

Diagrama (conceitual)
---------------------
Abaixo um desenho textual simplificado (use para gerar um diagrama visual em ferramentas como draw.io/PlantUML):

[Usuário] --> (Streamlit UI - app.py)
(Streamlit UI) --> (UniodontoCsvProcessor) : upload CSV
(UniodontoCsvProcessor) --> (Parsing & Normalization)
(Parsing & Normalization) --> (Regras Contábeis: Debito/Credito/Historico)
(Regras Contábeis) --> (Gerador CSV / PDF)
(Gerador CSV / PDF) --> (Temp Storage / ZIP)
(Temp Storage / ZIP) --> (Streamlit UI) : download link

Componentes externos e integrações possíveis
-------------------------------------------
- Armazenamento de artefatos: S3, Azure Blob, Google Cloud Storage (opcional) — para guardar históricos de processamento.
- Banco de dados: Postgres/MySQL (opcional) — para persistir metadados de processamento, logs, e versão dos arquivos.
- Monitoramento: Prometheus/Grafana (metrics), Sentry (errors).
- CI/CD: GitHub Actions / GitLab CI para testes automatizados e deployment.
- Autenticação: caso exponha a app em produção, colocar autenticação (OAuth, SSO corporativo, ou proxy com autenticação) e HTTPS via reverse-proxy (NGINX/Caddy).

Detalhes de deployment (recomendado)
-----------------------------------
Opção leve (para MVP)
- Hospedar como serviço em uma VM ou contêiner:
  - Container Docker minimal que execute `streamlit run app.py --server.port $PORT`.
  - Proxy reverso (NGINX) na frente para TLS e headers.
- Volumes: montar um volume temporário se desejar persistir arquivos gerados por mais tempo.

Opção escalável (produção)
- Empacotar em container Docker e orquestrar com Kubernetes:
  - Deploy como Deployment com 1+ réplicas (atentar para session_state: sessão deve ser tratada como efêmera; para multi-replica, usar backend de sessão ou persistência para arquivos/intermediários).
  - Ingress (NGINX/Traefik) para TLS.
  - Storage: S3 para artefatos; um banco relacional (Postgres) para metadados/histórico.
  - Jobs: processamento pesado (geração de PDFs em lote) pode ser offloaded para Workers (Celery/RQ) se necessário.
- Observabilidade: Prometheus + Grafana, logs centralizados (ELK / Loki).

Exemplo de Dockerfile (exemplo mínimo)
--------------------------------------
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"]

Considerações operacionais e riscos
----------------------------------
- Statefulness: Streamlit guarda estado em memória por sessão; para múltiplas réplicas, padronizar estratégia (sticky sessions ou mover estado para armazenamento compartilhado).
- Tamanho de arquivos: arquivos CSV muito grandes podem consumir muita memória; testar limites e considerar streaming/chunking.
- Segurança:
  - Garantir que uploads sejam processados de forma segura (não executar código contido nos arquivos).
  - Sanitizar nomes de arquivos e paths.
  - Usar HTTPS e autenticação em produção.
  - Proteger endpoints de administração e áreas de edição.
- Dependências nativas: ReportLab e outras libs podem requerer fontes ou bibliotecas nativas dependendo do ambiente; testar em container de produção.

Logs, monitoramento e alertas
-----------------------------
- Logs de aplicação: configurar logger (python logging) em vez de depender apenas de prints/Streamlit messages. Registrar:
  - uploads processados (nome, tamanho, usuário, timestamp)
  - número de registros processados
  - warnings / inconsistências detectadas (correções automáticas)
  - erros de processamento
- Métricas:
  - contagem de arquivos processados
  - latência média do processamento
  - taxa de erros
- Alertas:
  - falhas recorrentes em parsing
  - excesso de memória ou tempo de execução para um arquivo
  - falhas no worker (se usar fila)

CI/CD e testes
--------------
- Testes unitários:
  - Cobrir `normalize_value`, `sync_codigo_descricao`, `calculate_debit/credit/history`, `process_dataframe`.
  - Testar formatos simplificados e mapeamentos falhos.
- Testes de integração:
  - Rodar fluxo completo: upload CSV fixture → processamento → geração CSV/PDF (comparar com fixtures esperadas em `test_output/`).
- Pipeline sugerido:
  - Git push → run linters + unit tests → gerar artefatos de teste → deploy para staging (manual approval) → deploy para produção.

Melhorias sugeridas (roadmap técnico)
-------------------------------------
- Extrair `UniodontoCsvProcessor` para módulo separado (ex.: `camara/processor.py`) e criar testes unitários independentes.
- Implementar camada de persistência para histórico de processamentos (Postgres) e metadados (usuário, arquivos, warnings).
- Adicionar autenticação (SSO) e autorização para controlar quem pode gerar arquivos e baixar relatórios.
- Externalizar templates de PDF e permitir customização por cliente (logo, cabeçalho, campos).
- Implementar fila/worker para processamentos pesados e permitir respostas assíncronas na UI.

Referências e arquivos relacionados
----------------------------------
- Código principal e regras: `app.py`
- Fixtures / exemplos: `test_output/`
- Regras contábeis (técnico): [[contabilidade_regras.md]]
- Regras de negócio (linguagem contábil): [[regras_de_negocio.md]]
- Mapa do repositório: [[mapa_de_arquivos.md]]
- Visão geral do produto: [[visao_geral.md]]

Arquivo gerado em: 2025-08-29

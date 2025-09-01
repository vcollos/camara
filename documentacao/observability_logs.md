# Observability & Logs — Aplicativo Camara

Objetivo
--------
Guia prático para instrumentar, coletar e investigar logs, métricas e traces do aplicativo Camara. Contém recomendações de formatação, exemplos de configuração de logging em Python, métricas Prometheus a expor, integração com sistemas de observabilidade (Sentry, Prometheus, Grafana, Loki) e playbooks rápidos para investigação de incidentes.

Resumo executivo
----------------
- Logs: usar logging estruturado (JSON) com níveis (DEBUG/INFO/WARNING/ERROR/CRITICAL). Registrar contexto mínimo: request_id, filename, user (se houver), nome do arquivo importado, commit/versão.
- Métricas: expor contadores e histogramas (tempo de processamento, arquivos processados, erros por tipo, número de registros processados).
- Traces: para operações longas (geração de PDF, processamento de arquivos grandes) considerar traces distribuídos (OpenTelemetry).
- Alertas: com base em taxas de erro, latência e diferença entre total bruto e total contábil (anomalias).
- Retenção: logs detalhados (DEBUG) retidos por curto período; logs INFO/WARN/ERROR retidos mais tempo. Métricas armazenadas conforme SLA.

Onde instrumentar (pontos do código)
-----------------------------------
- app.py (UI) — registrar upload recebidos, tamanho do arquivo, usuário (quando aplicável), início/fim do processamento.
- UniodontoCsvProcessor:
  - detect_csv_format / detect_simplified_format: logar decisões de mapeamento.
  - normalize_value: WARN quando aplicar heurística de divisão por 100.
  - sync_codigo_descricao: INFO sobre correções aplicadas (quantidade).
  - process_dataframe: METRIC + log start/end com contagens (n registros, n IRRF, n inconsistências).
  - generate_accounting_reports / generate_unified_report / generate_irrf_report: logar tempo de geração de PDFs + falhas.
- Exportadores: logar paths temporários criados e tamanho dos artefatos (CSV/PDF/ZIP).

Formato de logs recomendado
---------------------------
- JSON estruturado (fácil ingestão por Loki/ELK/Cloud).
- Campos mínimos recomendados:
  - timestamp (ISO8601)
  - level (DEBUG/INFO/WARNING/ERROR)
  - logger (module.name)
  - message
  - file (nome do arquivo CSV processado)
  - records_count (quando aplicável)
  - user_id (se houver autenticação)
  - request_id / correlation_id (UUID gerado por upload)
  - commit (hash do commit, opcional)
  - extra: stacktrace (se error)
- Exemplo JSON:
  {"timestamp":"2025-08-29T12:00:00Z","level":"INFO","logger":"app.processor","message":"process_started","file":"camara_ago.csv","records_count":2345,"request_id":"a1b2c3","commit":"c141f98"}

Exemplo de configuração Python (logging) — básico
------------------------------------------------
Exemplo usando logging + python-json-logger:

import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("camara")
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

Uso:
logger.info("process_started", extra={"file": filename, "records_count": n, "request_id": rid})

Observação: em containers, recomendamos escrever logs para stdout/stderr (agente coleta).

Métricas recomendadas (Prometheus)
---------------------------------
- Counters:
  - camara_files_processed_total{status="success|error"} — número de arquivos processados por status.
  - camara_irrf_rows_total — número total de lançamentos IRRF gerados.
  - camara_inconsistencies_total — registros marcados como inconsistentes.
- Histograms / Summaries:
  - camara_processing_duration_seconds — tempo gasto por arquivo (histogram buckets configuráveis).
  - camara_pdf_generation_duration_seconds — tempo de geração de PDF.
- Gauges:
  - camara_current_processing_jobs — jobs em processamento (para workers).
  - camara_queue_size — tamanho da fila (se usar workers).
- Labels úteis: tipo (a_pagar/a_receber), env (staging/prod), filename (opcional, para amostras).

Exemplo de instrumentação (prometheus_client)
---------------------------------------------
from prometheus_client import Counter, Histogram, start_http_server

FILES_PROCESSED = Counter('camara_files_processed_total', 'Files processed', ['status'])
PROCESS_TIME = Histogram('camara_processing_duration_seconds', 'Processing time')

@PROCESS_TIME.time()
def process_file(...):
    try:
        ...
        FILES_PROCESSED.labels(status='success').inc()
    except Exception:
        FILES_PROCESSED.labels(status='error').inc()
        raise

- Expôr /metrics em um HTTP server (p.ex. start_http_server(8000)) ou integrar com seu servidor web.

Tracing (opcional)
------------------
- Para operações longas (PDF, processamento grande) instrumentar com OpenTelemetry para rastreamento distribuído.
- Exportar traces para Jaeger/Zipkin/OTLP endpoint.
- Correlacionar trace_id com request_id nos logs.

Coleta e agregação (arquitetura recomendada)
-------------------------------------------
- Logs: enviar para Loki/ELK/Cloud Logging via agente (Fluentd/Promtail/Filebeat).
- Métricas: Scrape Prometheus ou push gateway se necessário.
- Traces: coletor OpenTelemetry -> backend (Jaeger/OTLP).
- Alerts/Visualização: Grafana + dashboards e alertas.

Dashboards e alertas sugeridos
------------------------------
Dashboards:
- Painel "Overview":
  - Files processed per minute
  - Success/error rate
  - Average processing duration (p95, p50)
  - IRRF totals over time
- Painel "Errors":
  - Top errors (by message)
  - Recent stacktraces
- Painel "Performance":
  - CPU/memory for worker pods
  - PDF generation time distribution

Alertas:
- Error rate > X% por 10 minutos → pager
- P95 processing time > threshold → warning
- Spike em inconsistências detectadas → revisão manual
- Disk usage on storage > 80% → ops

Retenção e níveis
-----------------
- DEBUG logs: curto (ex.: 3 dias)
- INFO logs: médio (ex.: 30 dias)
- WARN/ERROR: longo (ex.: 90 dias)
- Métricas: conservar granularidade alta por 7-30 dias; agregados por 90+ dias (dependendo de custo).

Playbook rápido — investigação de incidente
-------------------------------------------
1. Identificar alerta (Grafana/Sentry).
2. Coletar request_id(s) afetados (do alert ou logs).
3. Pesquisar logs por request_id: obter trace, erro, linha CSV.
4. Reproduzir em ambiente de staging com o mesmo CSV (fixtures).
5. Se for bug no código, anexar:
   - CSV original (anonymizado se necessário)
   - Traceback completo
   - Versão do commit (git rev-parse HEAD)
   - Tempo de ocorrência e ambiente
6. Corrigir o código, criar teste unitário/integration e rodar CI.

Sentry / APM (erros e exceções)
-------------------------------
- Integração recomendada: Sentry para capturar exceptions com contexto (user, request_id, filename).
- Capturar exceções não tratadas em geração de PDF e processamento.
- Enviar tags: env, commit, module, file.
- Usar Sentry issues para triagem e linking com PRs.

Logs sensíveis e privacidade
---------------------------
- Não registrar dados sensíveis (PII) em logs.
- Antes de armazenar logs/fixtures, anonimizar nomes de pessoas e CPFs.
- Para contabilidade, manter valores numéricos (só registre linhas inteiras quando necessário e com controle de acesso).

Configuração em Docker / Kubernetes
-----------------------------------
- Docker: escrever logs para stdout; expor /metrics para Prometheus.
- K8s:
  - Deploy: sidecar de logs (Fluentd/Promtail) ou DaemonSet.
  - ConfigMap para configurar logging level e endpoints (SENTRY_DSN, PROMETHEUS_METRICS_PORT).
  - Liveness/readiness probes para a app.
  - Resource requests/limits para evitar OOM.

Exemplo de log collection pipeline (simples)
--------------------------------------------
1. App escreve JSON logs em stdout.
2. Promtail recolhe logs e empurra para Loki (labels: app=camara, env=prod).
3. Prometheus scrapes /metrics expostas pelo app.
4. Grafana consulta Loki/Prometheus e dispara alertas.

Checklist de observability (implementação mínima)
-------------------------------------------------
- [ ] Logging estruturado (JSON) implementado
- [ ] Expor /metrics (Prometheus)
- [ ] Instrumentar counters e histograms básicos
- [ ] Integrar Sentry para exceptions
- [ ] Dashboards Grafana com painéis de overview e errors
- [ ] Alertas configurados (erro rate, latência, spikes em inconsistências)

Como coletar evidências para um bug
-----------------------------------
1. Anexe CSV original (ou pequena amostra).
2. Cole logs stdout/stderr do período.
3. Traceback completo.
4. Versão do commit + ambiente (staging/prod).
5. Passos exatos para reproduzir.

Referências
----------
- Prometheus client Python: https://github.com/prometheus/client_python
- OpenTelemetry Python: https://opentelemetry.io/
- Sentry Python: https://docs.sentry.io/platforms/python/
- Grafana Loki: https://grafana.com/oss/loki/

Arquivo gerado em: 2025-08-29

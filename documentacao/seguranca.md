# Segurança — Aplicativo Camara

Objetivo
--------
Reunir práticas, controles e recomendações de segurança aplicáveis ao aplicativo Camara para proteger dados sensíveis, controlar acesso, endurecer o ambiente e cumprir requisitos de auditoria e conformidade.

Princípios gerais
-----------------
- Princípio do menor privilégio: serviços, contas e usuários devem ter somente as permissões necessárias.
- Defense in depth: aplicar múltiplas camadas (rede, aplicação, armazenamento, observabilidade).
- Não gravar PII em logs ou artefatos sem anonimização e controle de acesso.
- Criptografia em trânsito e em repouso para dados sensíveis.
- Tratamento consciente de uploads — validar, sanitizar, isolar.

Classificação e tratamento de dados
-----------------------------------
- Dados sensíveis (ex.: CPFs, dados pessoais, dados fiscais detalhados)
  - Não salvar em logs sem anonimização.
  - Em exportações (fixtures, relatórios de teste) use sample anonymizado.
  - Acesso somente para usuários/roles autorizados.
- Dados operacionais (metadados, contagens, totais)
  - Podem ser registrados em logs/metrics, sem PII.
- Arquivos CSV originais
  - Devem ser armazenados apenas temporariamente.
  - Policy recomendada: manter arquivos originais por X dias (ex.: 30 dias) em storage seguro; permitir exclusão manual/automática.

Uploads e processamento
-----------------------
- Validação estrita do arquivo no upload:
  - Limitar tipos permitidos (apenas .csv).
  - Limitar tamanho máximo (configurar tamanho na UI e no servidor, ex.: 50 MB por upload).
  - Escanear por malware/virus em ambientes corporativos (integração com antivírus).
- Isolamento do processamento:
  - Processar arquivos em processos isolados (containers ou workers separados) para reduzir blast radius.
  - Evitar execução de qualquer conteúdo do arquivo; tratar tudo como dados.
- Proteção contra path traversal:
  - Nunca usar nome de arquivo do usuário para construir paths sem sanitização.
  - Usar diretórios temporários gerados por API segura (tempfile.mkdtemp()) e nomes não previsíveis.

Segredos e variáveis sensíveis
------------------------------
- Não commitar secrets em código (.env não versionado).
- Usar secret manager para produção: AWS Secrets Manager, Azure Key Vault, HashiCorp Vault, ou mecanismos equivalentes.
- No container/k8s:
  - Usar Kubernetes Secrets ou soluções de injeção de secrets via CSI/provider.
  - Evitar variáveis de ambiente com secrets em logs.
- Acesso de leitura para secrets restrito apenas ao componente que precisa.

Autenticação e autorização
--------------------------
- A aplicação Streamlit, em produção, deve estar atrás de autenticação:
  - SSO corporativo (OAuth2 / OIDC) ou proxy autenticador.
  - Não expor app sem autenticação pública.
- Controle de acesso:
  - Definir roles mínimas: operador, contador, administrador.
  - Auditar quem baixou/exportou quais arquivos (log de auditoria).
- Proteções contra CSRF/XSS:
  - Streamlit serve UI; ainda assim, tratar entradas do usuário com cautela e usar cabeçalhos de segurança via proxy (Content-Security-Policy, X-Frame-Options).

Criptografia
------------
- TLS obrigatório:
  - Todas as comunicações (UI, APIs, storage) via HTTPS/TLS com certificados válidos.
- Dados em repouso:
  - Se usar armazenamento em nuvem (S3, Blob), habilitar server-side encryption (SSE).
  - Se guardar metadados/DB (Postgres), usar disco criptografado e, se possível, criptografia a nível de coluna para PII.
- Chaves:
  - Rodar rotação periódica de chaves/credentials.

Hardening de containers e servidores
-----------------------------------
- Minimizar imagem base (ex.: python:3.x-slim).
- Definir user não-root no container.
- Aplicar scan de vulnerabilidades nas imagens (Trivy, Clair).
- Pin de versões de dependências (requirements.txt) e atualizar periódica/automatizadamente.
- Policies de runtime:
  - Limitar recursos (requests/limits), read-only root filesystem quando possível.
  - Não expor portas desnecessárias.

Proteção de logs e evidências
----------------------------
- Logs centralizados com controle de acesso (Loki/ELK).
- Sanitizar logs antes de envio (remover PII).
- Controle de retenção e purge automático conforme política.
- Exportação de evidências (PDF/CSV) deve ter autorização para download e rastreamento (audit trail).

Auditoria e rastreabilidade
--------------------------
- Gerar audit logs para ações sensíveis:
  - Uploads, downloads, edições manuais, reprocessamentos, geração de relatórios e exclusão de arquivos.
- Logar: user (ou sistema), timestamp, action, filename/id, request_id.
- Armazenar audit logs em local imutável (append-only) quando necessário para conformidade.

Proteção contra ataques e abusos
-------------------------------
- Rate limiting no proxy para uploads e endpoints críticos.
- Monitoramento de anomalias: spikes em uploads, picos de erros, tentativas de upload malformado.
- WAF (Web Application Firewall) para bloquear tráfego malicioso.

Backups e recuperação
--------------------
- Se houver persistência:
  - Fazer backups regulares do DB e testá-los (restore periodic).
  - Backups dos metadados/documents devem ser criptografados.
- Estratégia de recuperação:
  - Documentar RTO (Recovery Time Objective) e RPO (Recovery Point Objective).
  - Testar playbook de restore periodicamente.

Conformidade e privacidade
--------------------------
- Avaliar requisitos locais (LGPD no Brasil) sobre armazenamento e tratamento de dados pessoais.
- Obter consentimento / base legal para processamento quando necessário.
- Implementar processos para requisições de acesso/remoção de dados pessoais (request subject rights).
- Registrar políticas de retenção e eliminação de dados.

Segurança em desenvolvimento e CI
---------------------------------
- Scans automáticos de SCA (Dependabot, Snyk) para dependências.
- Executar linters e security checks no CI.
- Secrets scanning em PRs (pre-commit hooks).
- Pipeline de CI com etapas de segurança: build, test, SCA, scan de container, deploy para staging.

Plano de resposta a incidentes (resumo)
---------------------------------------
1. Detectar (alerta via Sentry/Grafana/Loki).
2. Isolar (suspender processamento, bloquear acessos se necessário).
3. Coletar evidências (logs, request_id, commits).
4. Comunicar (equipe de resposta e stakeholders).
5. Mitigar (rollback, patch, revogar credenciais).
6. Restaurar e validar integridade.
7. Post-mortem e lições aprendidas.

Checklist de segurança (implementação mínima)
--------------------------------------------
- [ ] TLS habilitado em todas as comunicações
- [ ] App atrás de autenticação em produção
- [ ] Secrets manager em uso para produção
- [ ] Logs sem PII e centralizados
- [ ] Scans de dependências automáticos em CI
- [ ] Backups testados e criptografados
- [ ] Rate limiting no upload
- [ ] Processo de rotação de chaves/credentials documentado

Boas práticas operacionais
--------------------------
- Repassar matriz contábil e mudanças de regras às áreas envolvidas antes de deploy.
- Ter ambiente de homologação idêntico (o mais próximo possível) ao de produção.
- Revisar regras contábeis e fixtures com contabilidade antes de mudanças em produção.

Referências e recursos
----------------------
- OWASP Top Ten: https://owasp.org/www-project-top-ten/
- NIST guidance and best practices
- LGPD / GDPR guidance (dependendo do escopo)

Arquivo gerado em: 2025-08-29

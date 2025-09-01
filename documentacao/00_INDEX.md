# Documentação — Aplicativo Camara

Bem-vindo à documentação do aplicativo "Camara". Este repositório de documentação foi criado para que qualquer membro de equipe (desenvolvedores, QA, DevOps, contadores e gerentes de produto) consiga entender, replicar, alterar e operar o sistema em produção. Os arquivos estão organizados para uso direto no Obsidian: cada referência a outro documento usa o formato de link interno [[Nome do Arquivo]] para criar conexões bidirecionais no vault do Obsidian.

Observação importante: o arquivo principal com as regras para contadores é [[contabilidade_regras.md]] — priorize a leitura deste arquivo se o seu objetivo for entender cálculos, lançamentos e lógica fiscal / contábil do sistema.

Sumário (arquivos a serem gerados)
- [[visao_geral.md]] — Visão geral do produto, objetivos, público-alvo e fluxos principais.
- [[arquitetura.md]] — Arquitetura geral, componentes, infraestrutura e diagrama.
- [[mapa_de_arquivos.md]] — Mapeamento dos arquivos do projeto: para que serve cada arquivo chave (e.g., app.py), onde ficam as rotas, scripts de geração de relatórios, templates.
- [[endpoints_api.md]] — Lista de endpoints (se houver API), rotas, parâmetros, exemplos de request/response.
- [[banco_de_dados.md]] — Estrutura do banco (tabelas, campos, relações), scripts SQL principais, como são feitas conexões.
- [[modelos_de_dados.md]] — Modelos de dados usados na aplicação (classes, DTOs) e como cada campo é populado.
- [[contabilidade_regras.md]] — (PRIORITÁRIO) Regras detalhadas para contadores: cálculos, lançamentos, contas contábeis, regras fiscais, mapeamento entre eventos e débitos/créditos.
- [[fluxos_negocio.md]] — Casos de uso e fluxos (ex.: geração de relatório, integração com clientes, compensação).
- [[guias_de_desenvolvimento.md]] — Setup local, ambiente, variáveis de ambiente, comandos úteis (venv, pip, run).
- [[deploy.md]] — Processo de deploy (manualmente e automatizado), dependências, variáveis sensíveis e onde armazená-las.
- [[testes.md]] — Estratégia de testes, como rodar testes existentes, geração de PDFs e amostras (ex.: tests/generate_sample_pdf.py).
- [[troubleshooting.md]] — Problemas comuns e como resolver (erros de dependência, geração de PDF, erros de conexão de DB).
- [[contribuir.md]] — Guia para contribuir (branching, commits, PR, revisão de código).
- [[glossario.md]] — Termos e siglas usadas no produto.
- [[changelog.md]] — Histórico de alterações relevantes (link para commits / releases).
- [[observability_logs.md]] — Onde achar logs, como habilitar logs mais verbosos, formatos de log.
- [[seguranca.md]] — Considerações de segurança, tratamento de dados sensíveis, recomendações.
- [[obsidian_index.md]] — (Opcional) Índice para Obsidian com tags e um mapa mental de ligações.

Como usar esse índice
- No Obsidian, crie vault apontando para a pasta `documentacao`. Os links do tipo [[nome_do_arquivo.md]] já foram pensados para conectar com os demais arquivos. Ex.: abrir [[contabilidade_regras.md]] vai automaticamente criar backlink para este índice.
- Nomes de arquivos seguem o padrão: snake_case em minúsculas, extensão `.md`. Evitar espaços nos nomes dos arquivos reais (links humanos podem mostrar espaços mas o arquivo será `contabilidade_regras.md`).

Formato padrão de cada documento
- Título (H1)
- Resumo/Objetivo
- Conteúdo principal dividido em seções com H2/H3
- Exemplos práticos (requests, SQL, trechos de código)
- Links relevantes para outros arquivos (usar [[nome_arquivo.md]])
- "Para desenvolvedores" — instruções técnicas, localização no código, pontos de atenção
- "Para contadores" — (quando aplicável) resumo das regras contábeis
- "Notas de auditoria" — onde checar para validar os resultados

Prioridade imediata
1. Gerar o arquivo [[contabilidade_regras.md]] com as regras completas para contadores (detalhes de cada tipo de lançamento, fórmulas, contas impactadas, exemplos de lançamentos e como interpretar os relatórios PDF gerados).
2. Gerar [[mapa_de_arquivos.md]] explicando cada arquivo do repositório (ex.: app.py, tests/, test_output/, dicionario.csv).
3. Gerar [[banco_de_dados.md]] mapeando tabelas e como a aplicação acessa o DB (strings de conexão em `.env`, ORMs ou queries raw).

Templates recomendados (exemplo de cabeçalho)
---
title: Nome do Documento
tags: [categoria, tecnica, contabilidade]
created: 2025-08-29
---

Checklist de criação dos arquivos (próximos passos)
- [x] Analisar requisitos iniciais e criar índice (este arquivo)
- [ ] Criar `contabilidade_regras.md` (prioridade máxima)
- [ ] Criar `mapa_de_arquivos.md`
- [ ] Criar `banco_de_dados.md`
- [ ] Criar `visao_geral.md`
- [ ] Criar `arquitetura.md` (incluir diagrama)
- [ ] Criar `endpoints_api.md`
- [ ] Criar `modelos_de_dados.md`
- [ ] Criar `fluxos_negocio.md`
- [ ] Criar `guias_de_desenvolvimento.md`
- [ ] Criar `deploy.md`
- [ ] Criar `testes.md`
- [ ] Criar `troubleshooting.md`
- [ ] Criar `contribuir.md`
- [ ] Criar `glossario.md`
- [ ] Criar `changelog.md`
- [ ] Criar `observability_logs.md`
- [ ] Criar `seguranca.md`
- [ ] Criar `obsidian_index.md` (mapa mental e tags)

Próxima ação
- A partir da sua confirmação eu vou começar pela criação do arquivo prioritário `contabilidade_regras.md` com nível de detalhe elevado (fórmulas, exemplos, tabelas, links para arquivos de código que implementam as regras). Se preferir, posso primeiro gerar também `mapa_de_arquivos.md` para que tenhamos referência direta de onde cada regra está implementada no código.

Notas finais
- Posso gerar os arquivos um-a-um (recomendado) para que você confirme a cada etapa. Cada arquivo será salvo em `documentacao/` com links no formato Obsidian.
- Se quiser que eu já comece criando vários arquivos de uma vez, me confirme e eu vou prosseguir passo-a-passo, criando cada arquivo e aguardando sua confirmação após cada criação.

# Obsidian Index — Vault "Camara"

Resumo
------
Índice pensado para uso direto no Obsidian. Contém um MOC (Map of Content) com tags e links bidirecionais entre os documentos principais da documentação. Cole este arquivo como ponto de entrada dentro do seu vault Obsidian (pasta `documentacao/`) e ative backlinks para navegar facilmente.

Como usar
---------
1. Abra o Obsidian e crie um Vault apontando para a pasta: `.../contag/camara/documentacao`
2. Abra este arquivo `obsidian_index.md` e marque-o como seu "Home / MOC".
3. Habilite backlinks e use o painel Graph para explorar conexões.
4. Quando criar novo documento, nomeie no padrão snake_case.md e adicione um link para o MOC para criar conexão automática.

Tags sugeridas (usar no topo de cada arquivo)
- #produto
- #contabilidade
- #desenvolvimento
- #arquitetura
- #fluxo
- #teste
- #operacao
- #moc

Mapa de Conteúdo (MOC)
----------------------
- [[00_INDEX.md]] — Índice principal resumido (visão de alto nível)
- [[visao_geral.md]] — Visão do produto, público-alvo, funcionalidades
- [[arquitetura.md]] — Arquitetura técnica, componentes, Docker e deploy
- [[mapa_de_arquivos.md]] — Mapa do repositório e onde estão as regras
- [[modelos_de_dados.md]] — Esquema de DataFrames de entrada/saída e sugestão de DB
- [[matriz_contabil.csv]] — Matriz (Tipo × TipoSingular × CodigoTipoRecebimento → Debito/Credito/Historico)
- [[contabilidade_regras.md]] — Regras contábeis detalhadas (técnico)
- [[regras_de_negocio.md]] — Regras em linguagem contábil (para contadores)
- [[fluxos_negocio.md]] — Fluxos operacionais e checkpoints
- [[guias_de_desenvolvimento.md]] — Setup dev, comandos e Docker
- [[testes.md]] — Estratégia de testes, fixtures e templates
- [[test_output]] — Pasta com exemplos (no Obsidian, criar nota que referencia arquivos nesta pasta)
- [[mapa_de_arquivos.md]] — (duplicado no somário para fácil acesso) — onde procurar o código
- [[obsidian_index.md]] — Este arquivo (MOC)

Seções úteis rápidas
--------------------
- Contabilidade (leitura imediata)
  - [[regras_de_negocio.md]] (linguagem para contador)
  - [[contabilidade_regras.md]] (documentação técnica)
  - [[matriz_contabil.csv]] (planilha de referência)
- Desenvolvimento / Infra
  - [[guias_de_desenvolvimento.md]]
  - [[arquitetura.md]]
  - [[modelos_de_dados.md]]
  - [[testes.md]]
- Operação
  - [[fluxos_negocio.md]]
  - (em breve) [[troubleshooting.md]], [[observability_logs.md]], [[seguranca.md]]

Templates e padrões de linkagem
------------------------------
- Nome de arquivo: snake_case.md (sem espaços, minúsculas)
- Para referência entre notas, sempre usar [[nome_do_arquivo.md]] ou [[nome_do_arquivo]] — Obsidian cria backlink automaticamente.
- Prefixos recomendados para títulos:
  - Para documentos técnicos: "Técnico — "
  - Para documentos contábeis: "Contábil — "
  - Para guias/operacionais: "Operação — "

Sugestão de tags por categoria (colocar no topo dos arquivos)
- contabilidade: #contabilidade #regras #calc
- desenvolvimento: #desenvolvimento #dev #arquitetura
- operação: #operacao #fluxo #procedimento
- teste: #teste #fixture #ci

Mapas visuais e Graph view
--------------------------
- Crie um diagrama em `arquitetura.md` e linke-o aqui com `![[arquitetura.md]]` (ou exporte PNG e adicione como imagem).
- Use Graph View do Obsidian filtrando por tags (#contabilidade, #desenvolvimento) para visualizar clusters.

Checklist de manutenção do Vault
--------------------------------
- [ ] Revisar `contabilidade_regras.md` a cada alteração em `app.py`
- [ ] Atualizar `matriz_contabil.csv` quando adicionar/alterar mapeamentos
- [ ] Adicionar fixtures novos em `test_output/` e linkar em `testes.md`
- [ ] Incluir release notes em `changelog.md` a cada mudança relevante

Observações finais
-----------------
- Este MOC serve como ponto único de entrada para o time. Quando criar novos documentos, adicione pelo menos um link de retorno a este MOC para manter o graph conectado.
- Posso gerar automaticamente um arquivo `obsidian_index.json` com metadados (tags, títulos, links) se quiser sincronizar com outras ferramentas.

Arquivo gerado em: 2025-08-29

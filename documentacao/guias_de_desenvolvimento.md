# Guias de Desenvolvimento — Aplicativo Camara

Objetivo
--------
Instruções práticas para desenvolvedores configurarem o ambiente local, rodarem a aplicação, depurarem, criarem novos testes e seguirem boas práticas antes de enviar PRs.

Sumário rápido
--------------
- Setup local (venv, dependências)
- Rodar a aplicação (Streamlit)
- Debug e desenvolvimento iterativo
- Lint, formatação e pre-commit
- Docker (execução local)
- Estrutura de código e pontos de extensão
- Boas práticas para alterações nas regras contábeis

1) Setup local
--------------
Requisitos
- Python 3.9+ (recomendado 3.10/3.11)
- Git
- (Opcional) Docker

Passos
1. Clonar repositório:
   git clone https://github.com/vcollos/camara.git
   cd camara

2. Criar e ativar virtualenv:
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate      # Windows (PowerShell: .venv\Scripts\Activate.ps1)

3. Instalar dependências:
   pip install --upgrade pip
   pip install -r requirements.txt

4. (Opcional) Instalar ferramentas de desenvolvimento:
   pip install black isort flake8 pre-commit pytest

5. Arquivo de ambiente:
   - Existe um arquivo `.env` no repositório. O app atualmente não depende fortemente dele, mas você pode usá-lo para:
     - URL do logo
     - PATHs de output
     - Chaves de serviços (S3, etc.)
   - Para usar variáveis de .env no código, adicione `python-dotenv` e carregue no início de `app.py`.

2) Rodando a aplicação localmente
---------------------------------
Com o ambiente ativado:
- Rodar Streamlit:
  streamlit run app.py

- Para modo com logs mais verbosos:
  streamlit run app.py --logger.level=debug

- Acesse a UI pelo URL que o Streamlit imprimir no terminal (padrão: http://localhost:8501).

3) Debug e desenvolvimento iterativo
------------------------------------
- Hot-reload: Streamlit recarrega automaticamente quando arquivos mudam.
- Depuração com prints: usar `st.write()` para inspecionar valores em runtime via UI.
- Logging: adicione logger usando `import logging` e configure no topo do app. Evite prints em produção.
- Teste de funções isoladas: abra um REPL (python) dentro do venv, importe `UniodontoCsvProcessor` do `app.py` e teste funções:
  from app import UniodontoCsvProcessor
  p = UniodontoCsvProcessor()
  p.normalize_value("1.234,56")

- Se quiser executar partes sem Streamlit, importe a classe e chame os métodos diretamente em scripts de teste.

4) Lint, formatação e pre-commit
--------------------------------
Recomendado padronizar código antes de abrir PR.

Exemplo de comandos:
- Formatar com Black:
  black .

- Organizar imports com isort:
  isort .

- Verificar com Flake8:
  flake8 .

Configurar pre-commit:
1. Criar .pre-commit-config.yaml (se ainda não existir) com black, isort, flake8.
2. Instalar hooks:
   pre-commit install

5) Docker (execução local)
--------------------------
Exemplo mínimo de uso (já documentado em arquitetura):

- Build:
  docker build -t camara:local .

- Run (mapear porta e volume opcional):
  docker run --rm -p 8501:8501 -v $(pwd)/test_output:/app/test_output camara:local

Notas:
- No container, garanta que fonts/depêndencias nativas necessárias ao ReportLab estejam presentes se PDFs falharem.
- Para produção, usar orchestrator (Kubernetes) e S3 para artefatos.

6) Estrutura do código (onde mexer)
-----------------------------------
Arquivo principal: `app.py` — contém UI + classe `UniodontoCsvProcessor`.

Pontos de interesse:
- Dicionário de contas: `NOMES_CONTAS_CONTABEIS` (topo do arquivo) — atualize descrições aqui.
- Regras contábeis: `calculate_debit`, `calculate_credit`, `calculate_history`
- Normalização/parse: `normalize_value`, `detect_csv_format`, `detect_simplified_format`
- Exportação: `df_to_csv_string`, `export_to_csv`
- PDFs: `generate_accounting_reports`, `generate_unified_report`, `generate_irrf_report`
- Helpers PDF: `truncate_lines`, `_draw_logo`, `_get_logo_png_path`

Recomendação: ao extrair lógica de domínio, mova `UniodontoCsvProcessor` para `camara/processor.py` e exponha uma API bem definida. Isso facilita testes unitários.

7) Boas práticas ao alterar regras contábeis
-------------------------------------------
- Sempre atualizar:
  - `documentacao/contabilidade_regras.md`
  - `documentacao/regras_de_negocio.md`
  - `documentacao/matriz_contabil.csv` (ou regenerar)

- Crie testes unitários que cubram cada combinação crítica (Tipo × TipoSingular × CodigoTipoRecebimento) e casos especiais (LGPD, ATUARIO, CONVENCAO).

- Use fixtures (em `test_output/`) para regressão: depois de alterar regras gere novos outputs e compare com outputs esperados.

8) Comandos úteis resumidos
---------------------------
- Criar venv e instalar:
  python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

- Rodar app:
  streamlit run app.py

- Rodar script de exemplo (PDF):
  python tests/generate_sample_pdf.py

- Rodar pytest:
  pytest -q

- Format & lint:
  black .
  isort .
  flake8 .

9) Integração contínua (exemplo)
-------------------------------
- Workflow básico GitHub Actions:
  - Ações: checkout, setup-python, install dependencies, run black --check, run flake8, run pytest.
- Se houver fixtures grandes, armazene em cache/artifacts para comparações.

10) Observações finais
----------------------
- Documente cada alteração significativa nas regras contábeis com link para ticket/PR.
- Se precisar, eu posso gerar um template de testes pytest cobrindo `normalize_value`, `calculate_debit`, `calculate_credit`, `calculate_history` com matrizes de entrada esperada/resultado.

# Testes — Aplicativo Camara

Objetivo
--------
Descrever a estratégia de testes, como rodar os testes locais e em CI, exemplos de casos de teste prioritários e templates para criar testes unitários e de integração usando pytest. Este documento ajuda a garantir que mudanças nas regras contábeis ou parsing não quebrem o comportamento esperado.

Visão geral da estratégia
-------------------------
- Testes unitários: funções puras e pequenos blocos (ex.: `normalize_value`, `sync_codigo_descricao`, `calculate_debit`, `calculate_credit`, `calculate_history`).
- Testes de integração: fluxo completo do pipeline (ler CSV fixture → process_dataframe → comparar CSV/Pandas resultante com saída esperada em `test_output/`).
- Testes end-to-end (opcionais): simular upload na interface Streamlit e validar geração de artefatos (PDF/CSV). Pode ser feito manualmente ou com ferramentas de teste de UI.
- Fixtures: usar arquivos em `test_output/` ou adicionar `tests/fixtures/` com CSVs de exemplo (casos normais e casos borda).

Configuração local
------------------
1. Instalar dependências de teste (recomendado dentro do venv):
   pip install pytest pytest-cov

2. Estrutura de pastas sugerida:
   - tests/
     - unit/
       - test_normalize.py
       - test_rules_matrix.py
     - integration/
       - test_pipeline_taxa_manutencao.py
     - fixtures/
       - sample_camara.csv
       - sample_irrf.csv

Rodando os testes
-----------------
- Rodar todos os testes:
  pytest -q

- Rodar testes com coverage:
  pytest --cov=./ -q

- Rodar apenas testes unitários:
  pytest tests/unit -q

- Rodar apenas testes de integração:
  pytest tests/integration -q

Casos de teste prioritários (lista)
-----------------------------------
1. normalize_value
   - "1.234,56" → 1234.56
   - "1234.56" → 1234.56
   - "1.234" (sem decimal explícito) → 1234.00 ou comportamento definido
   - Valores vazios / None → 0.0
   - Valor muito grande que pareça erro (usar divisão por 100) → verificar comportamento

2. sync_codigo_descricao
   - Código correto + descrição incorreta → descrição corrigida
   - Código inválido + descrição reconhecível → código corrigido
   - Nenhum valor válido → fallback para 6 ("Outros")

3. calculate_debit / calculate_credit / calculate_history
   - Cobrir todas as combinações críticas da matriz (Tipo × TipoSingular × CodigoTipoRecebimento)
   - Casos especiais: NomeSingular == "UNIODONTO DO BRASIL"; Descricao contendo "CONVENCAO", "LGPD", "ATUARIO"/"ATUÁRIO"
   - Validar que retorno seja número inteiro (ou string numérica) e consistente com `NOMES_CONTAS_CONTABEIS`

4. process_dataframe (integração pequena)
   - Entrada com IRRF > 0 → gera linha adicional de IRRF com histórico e contas corretas
   - Entrada em formato simplificado → é mapeada corretamente e processada
   - Arquivo com colunas faltantes → create_default_columns preenche e processa corretamente

5. df_to_csv_string / export_to_csv
   - Verificar formatação da coluna `valor` com vírgula decimal
   - Ordem das colunas e presença do cabeçalho correto
   - Preservação de colunas originais quando esperadas

Exemplos de testes (templates)
------------------------------
1) Teste unitário simplificado para normalize_value (tests/unit/test_normalize.py)
```python
import pytest
from app import UniodontoCsvProcessor

proc = UniodontoCsvProcessor()

def test_normalize_br_format():
    assert proc.normalize_value("1.234,56") == pytest.approx(1234.56)

def test_normalize_en_format():
    assert proc.normalize_value("1234.56") == pytest.approx(1234.56)

def test_normalize_empty():
    assert proc.normalize_value("") == 0.0

def test_normalize_none():
    assert proc.normalize_value(None) == 0.0
```

2) Teste para regras (matrix) (tests/unit/test_rules_matrix.py)
```python
import pandas as pd
from app import UniodontoCsvProcessor

def make_row(tipo, tiposingular, codigo):
    return pd.Series({
        'Tipo': tipo,
        'TipoSingular': tiposingular,
        'CodigoTipoRecebimento': codigo,
        'NomeSingular': 'TESTE',
        'Descricao': ''
    })

def test_debit_credit_matrix():
    p = UniodontoCsvProcessor()
    row = make_row('A pagar', 'Operadora', 1)
    assert p.calculate_debit(row) == 31731
    assert p.calculate_credit(row) == 90918
```

3) Teste de integração do pipeline (tests/integration/test_pipeline_basic.py)
```python
import pandas as pd
from app import UniodontoCsvProcessor

def test_process_sample_fixture(tmp_path):
    p = UniodontoCsvProcessor()
    fixture = 'tests/fixtures/sample_camara.csv'
    df = pd.read_csv(fixture, sep=';')
    mapped_df, info = p.detect_csv_format(df)
    processed = p.process_dataframe(mapped_df)
    # Verificar colunas de saída
    assert 'Debito' in processed.columns
    assert 'Credito' in processed.columns
    # Verificar que a data está formatada
    assert processed['DATA'].str.match(r'\d{2}/\d{2}/\d{4}').all()
```

Recomendações para fixtures
---------------------------
- Colocar em `tests/fixtures/` arquivos com:
  - Caso padrão com vários tipos 1..6
  - Caso com IRRF > 0 (para testar criação de linhas IRRF)
  - Caso com descriptografias (LGPD, ATUARIO, CONVENCAO)
  - Caso simplificado (colunas Nome / Valor a Receber / Valor a Pagar)

Integração com CI (exemplo GitHub Actions)
------------------------------------------
Arquivo de workflow (ex.: .github/workflows/ci.yml):
- name: CI
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - name: Set up Python
          uses: actions/setup-python@v4
          with: python-version: 3.10
        - name: Install dependencies
          run: |
            python -m pip install --upgrade pip
            pip install -r requirements.txt
            pip install pytest pytest-cov
        - name: Run tests
          run: pytest --cov=./

Boas práticas de teste
----------------------
- Isolar regras: manter as funções de mapeamento simples para fácil testabilidade.
- Cobertura: priorizar cobertura para lógica contábil (matrix) e parsing.
- Fixtures versionadas: qualquer alteração nas regras deve vir acompanhada de atualização das fixtures e do arquivo `documentacao/matriz_contabil.csv`.
- Testes determinísticos: evitar depender de data atual nos testes; sempre mockar datas (por ex., monkeypatch em pytest) para garantir resultados repetíveis.

Checklist pré-merge
-------------------
- [ ] Rodar linters e formatadores (black, isort, flake8)
- [ ] Rodar todos os testes locais (pytest)
- [ ] Atualizar/gerar novas fixtures se regras mudaram
- [ ] Atualizar documentação em `documentacao/` (contabilidade_regras.md, matriz_contabil.csv)
- [ ] Incluir teste(s) cobrindo a mudança no PR

Recursos adicionais
-------------------
- Exemplo de script de geração de PDF: `tests/generate_sample_pdf.py`
- Fixtures e exemplos atuais: `test_output/`
- Para ajuda na criação de testes automáticos, posso gerar templates de arquivos pytest prontos em `tests/` cobrindo as funções críticas.

Arquivo gerado em: 2025-08-29

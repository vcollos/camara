# Modelos de Dados — Aplicativo Camara

Objetivo
--------
Descrever de forma clara e prática os formatos de entrada e saída utilizados pelo sistema. Este documento serve como referência para desenvolvedores, analistas e contadores que precisam:
- preparar arquivos de entrada;
- entender o DataFrame interno (colunas, tipos e valores esperados);
- mapear o CSV contábil de saída para importação no ERP;
- criar testes e validações automáticas.

Sumário rápido
--------------
- Entrada esperada (formato "Câmara de Compensação")
- Formato simplificado detectado (heurística de mapeamento)
- Colunas criadas/transformadas durante o processamento
- DataFrame de saída (CSV contábil)
- Exemplos de linha (entrada e saída)
- Dicionários de valores e defaults
- Sugestões de modelo relacional (se persistir em DB)
- Checklist de validação automática

1. Formato de entrada esperado (após mapeamento)
-----------------------------------------------
O sistema aceita arquivos CSV variados e tenta mapear as colunas. O formato ideal, após o mapeamento automático, contém as colunas abaixo (nome de coluna exato esperado pelo pipeline):

- Tipo (string)
  - Valores esperados: "A pagar" | "A receber"
- CodigoSingular (inteiro ou string numérica)
- NomeSingular (string)
- TipoSingular (string)
  - Valores esperados: "Operadora" | "Prestadora"
- CodigoTipoRecebimento (inteiro) — 1..6
- DescricaoTipoRecebimento (string)
- ValorBruto (monetário; string ou numérico) — ex.: "1.234,56" ou 1234.56
- IRRF (monetário; string ou numérico) — pode ser 0 ou vazio
- Descricao (string) — campo livre usado para regras especiais e complemento

Colunas adicionais que podem existir no CSV de entrada (o app preserva quando presente):
- NumeroDocumento, RegistroANS, TaxaAdministrativa, Subtotal, OutrosTributos, ValorLiquido, etc.

2. Formato simplificado detectado
---------------------------------
Quando o CSV tiver cabeçalhos comuns de relatórios (ex.: "Nome", "Valor a Receber", "Valor a Pagar", "Código"), o app tenta converter para o formato da Câmara com as regras:
- "Nome" → NomeSingular
- "Código" → CodigoSingular
- "Tipo" → Tipo
- "Valor a Receber"/"Valor a Pagar" → ValorBruto (escolhe o valor > 0)
- Campos padrão criados: TipoSingular = "Operadora", CodigoTipoRecebimento = 6, DescricaoTipoRecebimento = "Outras", IRRF = 0, Descricao = "Importado de relatório simplificado"

3. Colunas criadas e transformadas no processamento
---------------------------------------------------
Durante process_dataframe, o sistema cria/transforma as seguintes colunas (ordem aproximada):

- Debito (int|string) — código da conta debitada (resultado de calculate_debit)
- Credito (int|string) — código da conta creditada (resultado de calculate_credit)
- Historico (int|string) — código do histórico (resultado de calculate_history)
- DATA (datetime / string) — por padrão: último dia do mês anterior; depois formatado como 'dd/mm/YYYY' para exportação
- valor (float) — ValorBruto normalizado pela função normalize_value
- complemento (string) — concatenação: NomeSingular | DescricaoTipoRecebimento | Descricao | Tipo (ou com prefixo de inconsistência)
- IRRF (float) — quando presente, normalizado; também utilizado para criar linhas adicionais de IRRF
- Colunas auxiliares preservadas: Tipo, TipoSingular, CodigoTipoRecebimento, NomeSingular, DescricaoTipoRecebimento, Descricao, ValorBruto original

Observações:
- A coluna `ValorBruto` pode vir em formatos diversos; `normalize_value` converte para float e faz correções heurísticas (e.g., dividir por 100 se plausível).
- O pipeline cria linhas adicionais para IRRF quando `IRRF` normalizado > 0. Essas linhas têm complemento terminando em " | IRRF" e históricos específicos (ex.: 22 ou 2341).

4. DataFrame de saída (CSV contábil)
-----------------------------------
O CSV contábil final exportado contém, por padrão, estas 6 colunas (ordem importante para importadores contábeis):

1. Debito — inteiro
2. Credito — inteiro
3. Historico — inteiro
4. DATA — string formatada "DD/MM/YYYY"
5. valor — string numérica formatada "1.234,56" (vírgula decimal)
6. complemento — string

Além destas, quando exporta o "Arquivo Editado (Original)" o sistema preserva as colunas originais do usuário.

5. Tipos recomendados (pandas dtypes)
-------------------------------------
Exemplo de dtypes sugeridos para uso com pandas (após mapeamento inicial):

- 'Tipo': string (categoria possível)
- 'CodigoSingular': Int64 (nullable) ou string se códigos não forem estritamente numéricos
- 'NomeSingular': string
- 'TipoSingular': string / category
- 'CodigoTipoRecebimento': Int64 (nullable)
- 'DescricaoTipoRecebimento': string
- 'ValorBruto': float (após normalize)
- 'IRRF': float (após normalize)
- 'Descricao': string

Exemplo de código para forçar dtypes após carregamento:
```python
df['CodigoTipoRecebimento'] = pd.to_numeric(df['CodigoTipoRecebimento'], errors='coerce').fillna(6).astype(int)
df['ValorBruto'] = df['ValorBruto'].apply(processor.normalize_value)
df['IRRF'] = df['IRRF'].apply(processor.normalize_value)
```

6. Exemplos de linhas (entrada e saída)
---------------------------------------
Exemplo (entrada CSV original — campos principais):
{
  "Tipo": "A pagar",
  "CodigoSingular": "123",
  "NomeSingular": "UNIODO EXEMPLO",
  "TipoSingular": "Operadora",
  "CodigoTipoRecebimento": "3",
  "DescricaoTipoRecebimento": "Taxa de Manutenção",
  "ValorBruto": "1.234,56",
  "IRRF": "",
  "Descricao": "Mensalidade Agosto"
}

Exemplo (linha no DataFrame de saída antes de escrita em CSV contábil):
{
  "Debito": 52632,
  "Credito": 22036,
  "Historico": 368,
  "DATA": "30/07/2025",
  "valor": 1234.56,
  "complemento": "UNIODO EXEMPLO | Taxa de Manutenção | Mensalidade Agosto | A pagar",
  "Tipo": "A pagar",
  "TipoSingular": "Operadora",
  "CodigoTipoRecebimento": 3,
  "NomeSingular": "UNIODO EXEMPLO",
  "DescricaoTipoRecebimento": "Taxa de Manutenção",
  "Descricao": "Mensalidade Agosto",
  "ValorBruto": "1.234,56",
  "IRRF": ""
}

Quando escrito em CSV contábil (linha):
52632;22036;368;30/07/2025;1.234,56;UNIODO EXEMPLO | Taxa de Manutenção | Mensalidade Agosto | A pagar

7. Dicionários de valores e defaults
-----------------------------------
- CodigoTipoRecebimento defaults:
  - valor padrão se missing: 6 (Outros)
- TipoSingular default: "Operadora"
- Tipo default: "A receber" (quando criado por create_default_columns)
- DescricaoTipoRecebimento default: "Outras"
- ValorBruto / IRRF default: 0.0

8. Sugestão de esquema relacional (se optar por persistir)
-----------------------------------------------------------
Tabela: processamento_arquivos (metadados)
- id SERIAL PK
- filename TEXT
- uploaded_by TEXT
- uploaded_at TIMESTAMP
- records_count INT
- status VARCHAR (processed/failed)
- warnings JSONB

Tabela: lancamentos_contabeis (linhas exportadas)
- id SERIAL PK
- processamento_id FK -> processamento_arquivos.id
- debito INT
- credito INT
- historico INT
- data DATE
- valor NUMERIC(14,2)
- complemento TEXT
- tipo VARCHAR
- tiposingular VARCHAR
- codigo_tipo_recebimento INT
- nome_singular TEXT
- descricao_tipo_recebimento TEXT
- descricao TEXT
- is_irrf BOOLEAN
- raw_json JSONB (linha original como backup)

Índices e observabilidade:
- Índice em processamento_id
- Índice em is_irrf
- Adicionar colunas para auditoria (created_by, created_at)

9. Regras de validação/QA automáticas (checklist para testes)
-------------------------------------------------------------
- Verificar presença de colunas obrigatórias após mapeamento.
- Validar que CodigoTipoRecebimento ∈ {1,2,3,4,5,6}.
- Confirmar que ValorBruto e IRRF são >= 0 e < 1e9 (sanity check).
- Validar que para cada linha `Debito` e `Credito` são inteiros não nulos (após processamento).
- Garantir que complementos de IRRF terminem em " | IRRF" e que `is_irrf_record` detecte corretamente.
- Conferir conversão de formatos monetários (p.ex.: "1.234,56" → 1234.56).
- Testar heurística de divisão por 100 em valores gigantescos (caso de parsing errado).

10. Notas para desenvolvedores
------------------------------
- Centralizar esquema em um objeto/arquivo de schema (p.ex. `schemas.py` com pydantic / pandera) facilita validação.
- Recomenda-se criar tests unitários que usem fixtures de `test_output/` para validar o pipeline completo.
- Ao alterar nomes de colunas no pipeline, atualizar também este documento e `documentacao/00_INDEX.md`.

Links úteis
-----------
- Regras técnicas de contabilidade: [[contabilidade_regras.md]]
- Regras para contadores (linguagem contábil): [[regras_de_negocio.md]]
- Exemplos e fixtures: `test_output/`
- Mapa do repositório: [[mapa_de_arquivos.md]]

Arquivo gerado em: 2025-08-29

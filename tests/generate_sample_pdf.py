#!/usr/bin/env python3
"""
Script de teste para gerar PDFs usando as funções do app.py.

Gera:
 - relatorio_camara_compensacao.pdf (relatório unificado)
 - relatorios_contabeis.zip (relatórios contábeis, se aplicável)

Uso:
    python3 tests/generate_sample_pdf.py

Observações:
 - Este script importa a classe UniodontoCsvProcessor definida em app.py.
 - Gera saída em ./test_output/
"""
import os
import pandas as pd
from app import UniodontoCsvProcessor

OUTPUT_DIR = "test_output"

def build_sample_dataframe():
    """
    Cria um DataFrame mínimo com as colunas esperadas pelo processor.
    """
    rows = [
        # A pagar - Operadora - taxa manutenção (3)
        {
            "Tipo": "A pagar",
            "CodigoSingular": 1001,
            "NomeSingular": "Coop A",
            "TipoSingular": "Operadora",
            "CodigoTipoRecebimento": 3,
            "DescricaoTipoRecebimento": "Taxa de Manutenção",
            "ValorBruto": "1.234,56",
            "IRRF": "0,00",
            "Descricao": "Serviço X - CONVENCAO EXEMPLO"
        },
        # A receber - Prestadora - pré-pagamento (1)
        {
            "Tipo": "A receber",
            "CodigoSingular": 2001,
            "NomeSingular": "Prestadora B",
            "TipoSingular": "Prestadora",
            "CodigoTipoRecebimento": 1,
            "DescricaoTipoRecebimento": "Repasse em Pré-pagamento",
            "ValorBruto": "2.500,00",
            "IRRF": "25,00",
            "Descricao": "Faturamento Mensal"
        },
        # A pagar - Outros (6)
        {
            "Tipo": "A pagar",
            "CodigoSingular": 3001,
            "NomeSingular": "Entidade C",
            "TipoSingular": "Operadora",
            "CodigoTipoRecebimento": 6,
            "DescricaoTipoRecebimento": "Outros",
            "ValorBruto": "150,00",
            "IRRF": "0,00",
            "Descricao": "Despesa diversa"
        }
    ]
    df = pd.DataFrame(rows)
    return df

def ensure_output_dir(path):
    os.makedirs(path, exist_ok=True)

def main():
    ensure_output_dir(OUTPUT_DIR)
    proc = UniodontoCsvProcessor()

    # Construir DataFrame de exemplo
    df_original = build_sample_dataframe()
    print("DataFrame exemplo criado:")
    print(df_original)

    # Processar dataframe (gera colunas Debito, Credito, Historico, DATA, valor, complemento, etc.)
    try:
        processed_df = proc.process_dataframe(df_original.copy())
    except Exception as e:
        print("Erro ao processar dataframe de exemplo:", e)
        return

    if processed_df is None:
        print("process_dataframe retornou None. Verifique logs.")
        return

    print("DataFrame processado (pré-relatório):")
    print(processed_df.head())

    # Gerar relatório unificado (PDF)
    try:
        result = proc.generate_unified_report(processed_df, output_dir=OUTPUT_DIR, display_result=False)
        pdf_file = result.get("pdf_file")
        if pdf_file and os.path.exists(pdf_file):
            print(f"Relatório unificado gerado: {pdf_file}")
        else:
            print("Geração do relatório unificado não retornou caminho válido.")
    except Exception as e:
        print("Erro ao gerar relatório unificado:", e)

    # Gerar relatórios contábeis (ZIP)
    try:
        accounting_results = proc.generate_accounting_reports(processed_df, output_dir=OUTPUT_DIR, display_result=False)
        zip_file = accounting_results.get("zip_file")
        if zip_file and os.path.exists(zip_file):
            print(f"Relatórios contábeis gerados em ZIP: {zip_file}")
        else:
            print("Geração dos relatórios contábeis não retornou ZIP válido.")
    except Exception as e:
        print("Erro ao gerar relatórios contábeis:", e)

    # Gerar relatório de IRRF (se aplicável)
    try:
        irrf_results = proc.generate_irrf_report(processed_df, output_dir=OUTPUT_DIR, display_result=False)
        if irrf_results and irrf_results.get("pdf_file") and os.path.exists(irrf_results["pdf_file"]):
            print(f"Relatório IRRF gerado: {irrf_results['pdf_file']}")
        else:
            print("Relatório IRRF não gerado (pode não haver registros com IRRF).")
    except Exception as e:
        print("Erro ao gerar relatório IRRF:", e)

    print("Teste concluído. Verifique a pasta ./test_output para os PDFs e ZIPs gerados.")

if __name__ == "__main__":
    main()

"""
Pipeline completo de adquisicion de datos ScoutLab
=====================================================
Ejecuta el scraping de WhoScored (stats) y Transfermarkt (valores),
fusiona los datos y entrena el modelo ML.

Uso:
    python notebooks/pipeline_datos.py                     # Pipeline completo
    python notebooks/pipeline_datos.py --solo-whoscored    # Solo WhoScored
    python notebooks/pipeline_datos.py --solo-transfermarkt # Solo Transfermarkt
    python notebooks/pipeline_datos.py --solo-merge        # Solo merge (CSVs ya existen)
    python notebooks/pipeline_datos.py --solo-ml           # Solo entrenar modelo

Prerequisitos:
    pip install -r requirements.txt
    pip install -r requirements_scraping.txt
"""

import sys
import os
import argparse
import time

# Anadir raiz del proyecto al path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

RAW_DIR = os.path.join(ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(ROOT, "data", "processed")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

WS_CSV = os.path.join(RAW_DIR, "whoscored_stats.csv")
TM_CSV = os.path.join(RAW_DIR, "transfermarkt_values.csv")
OUTPUT_CSV = os.path.join(PROCESSED_DIR, "jugadores.csv")


def paso_1_whoscored():
    """Paso 1: Ya no se usa WhoScored. Redirige a Transfermarkt."""
    print("\n[INFO] WhoScored ya no se usa. Ejecuta --solo-transfermarkt")


def paso_2_transfermarkt():
    """Paso 2: Scrapear stats + valores de Transfermarkt."""
    print("\n" + "=" * 60)
    print("SCRAPING TRANSFERMARKT (Stats + Valores de mercado)")
    print("=" * 60)

    from backend.scraper import scrape_all

    start = time.time()
    df = scrape_all(output_path=OUTPUT_CSV)
    elapsed = time.time() - start

    if not df.empty:
        print(f"\n[OK] Transfermarkt: {len(df)} jugadores en {elapsed/60:.1f} min")
        print(f"     Guardado: {OUTPUT_CSV}")
    else:
        print("\n[ERROR] No se obtuvieron datos")

    return df


def paso_3_merge():
    """Paso 3: Ya no se necesita merge separado."""
    print("\n[INFO] El merge ya esta integrado en el scraper de Transfermarkt.")


def paso_4_modelo_ml():
    """Paso 4: Entrenar modelo ML sobre datos fusionados."""
    print("\n" + "=" * 60)
    print("PASO 4: ENTRENAR MODELO ML")
    print("=" * 60)

    import pandas as pd
    from backend.data_loader import _clean_dataframe
    from backend.ml_model import train_model

    if not os.path.exists(OUTPUT_CSV):
        print(f"[ERROR] No existe: {OUTPUT_CSV}")
        print("  Ejecuta primero el merge")
        return None

    df = pd.read_csv(OUTPUT_CSV)
    df = _clean_dataframe(df)

    # Solo entrenar con jugadores que tengan valor de mercado y minutos
    df_train = df[(df["valor_mercado"] > 0) & (df["minutos"] > 0)]
    print(f"  Jugadores para entrenar: {len(df_train)} (con valor + minutos)")

    if len(df_train) < 50:
        print("[WARN] Pocos datos para entrenar. El modelo puede no ser preciso.")

    start = time.time()
    metrics = train_model(df_train)
    elapsed = time.time() - start

    print(f"\n[OK] Modelo entrenado en {elapsed:.1f} seg")
    print(f"  R2 train: {metrics['r2_train']:.3f}")
    print(f"  R2 test:  {metrics['r2_test']:.3f}")
    print(f"  MAE test: {metrics['mae_test']:,.0f} EUR")
    print(f"  Muestras: {metrics['n_samples']}")
    print(f"\n  Top features:")
    for k, v in list(metrics["feature_importance"].items())[:5]:
        print(f"    {k}: {v:.3f}")

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Pipeline de datos ScoutLab")
    parser.add_argument("--solo-whoscored", action="store_true",
                        help="Solo scrapear WhoScored")
    parser.add_argument("--solo-transfermarkt", action="store_true",
                        help="Solo scrapear Transfermarkt")
    parser.add_argument("--solo-merge", action="store_true",
                        help="Solo fusionar datos (CSVs deben existir)")
    parser.add_argument("--solo-ml", action="store_true",
                        help="Solo entrenar modelo ML")
    args = parser.parse_args()

    print("=" * 60)
    print("SCOUTLAB - PIPELINE DE ADQUISICION DE DATOS")
    print("=" * 60)

    total_start = time.time()

    if args.solo_whoscored:
        print("[INFO] WhoScored ya no se usa. Usa --solo-transfermarkt")
    elif args.solo_transfermarkt:
        paso_2_transfermarkt()
    elif args.solo_merge:
        print("[INFO] El merge ya esta integrado en el scraper")
    elif args.solo_ml:
        paso_4_modelo_ml()
    else:
        # Pipeline completo: Transfermarkt + ML
        paso_2_transfermarkt()
        paso_4_modelo_ml()

    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETADO en {total_elapsed/60:.1f} minutos")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

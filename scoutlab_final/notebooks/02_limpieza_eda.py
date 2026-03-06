"""
02 - Limpieza de Datos y EDA
=============================
Procesamiento de datos crudos, limpieza, analisis exploratorio,
y generacion de metricas derivadas.
"""

import pandas as pd
import numpy as np
import os

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")


def load_raw_data() -> pd.DataFrame:
    """Carga y combina los datos crudos de todas las fuentes."""
    transfermarkt_path = os.path.join(RAW_DIR, "transfermarkt_raw.csv")
    besoccer_path = os.path.join(RAW_DIR, "besoccer_goleadores.csv")

    dfs = []

    if os.path.exists(transfermarkt_path):
        df_tm = pd.read_csv(transfermarkt_path)
        print("Transfermarkt: " + str(len(df_tm)) + " registros")
        dfs.append(df_tm)

    if os.path.exists(besoccer_path):
        df_bs = pd.read_csv(besoccer_path)
        print("BeSoccer: " + str(len(df_bs)) + " registros")
        # Merge por nombre de jugador (requiere normalizacion)
        # Aqui se implementaria la logica de matching

    if not dfs:
        print("No se encontraron datos crudos. Usando datos de ejemplo.")
        return None

    return pd.concat(dfs, ignore_index=True) if dfs else None


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y normaliza los datos."""
    if df is None:
        return None

    # Eliminar duplicados
    df = df.drop_duplicates(subset=["nombre", "equipo"], keep="first")

    # Normalizar nombres
    df["nombre"] = df["nombre"].str.strip().str.title()

    # Tratar valores nulos
    numeric_cols = ["edad", "valor_mercado", "goles", "asistencias", "minutos", "partidos"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Eliminar jugadores sin nombre
    df = df[df["nombre"].notna() & (df["nombre"] != "")]

    return df


def generate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Genera metricas derivadas a partir de los datos limpios."""
    if df is None:
        return None

    # Metricas por 90 minutos
    if "minutos" in df.columns and "goles" in df.columns:
        min_safe = df["minutos"].replace(0, np.nan)
        df["goles_por_90"] = (df["goles"] / (min_safe / 90)).round(2).fillna(0)

    if "minutos" in df.columns and "asistencias" in df.columns:
        min_safe = df["minutos"].replace(0, np.nan)
        df["asistencias_por_90"] = (df["asistencias"] / (min_safe / 90)).round(2).fillna(0)

    # Participaciones de gol
    if "goles" in df.columns and "asistencias" in df.columns:
        df["participaciones_gol"] = df["goles"] + df["asistencias"]

    return df


def run_eda():
    """Ejecuta el pipeline completo de limpieza y EDA."""
    print("Cargando datos crudos...")
    df = load_raw_data()

    if df is None:
        print("No hay datos crudos. El sistema usara datos de ejemplo generados automaticamente.")
        return

    print("Limpiando datos...")
    df = clean_data(df)

    print("Generando metricas...")
    df = generate_metrics(df)

    # Guardar datos procesados
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    output_path = os.path.join(PROCESSED_DIR, "jugadores.csv")
    df.to_csv(output_path, index=False)
    print("Datos procesados guardados en: " + output_path)
    print("Total de jugadores: " + str(len(df)))

    # EDA basico
    print("\n=== ANALISIS EXPLORATORIO ===")
    print("\nDistribucion por posicion:")
    if "posicion" in df.columns:
        print(df["posicion"].value_counts().to_string())

    print("\nEstadisticas de valor de mercado:")
    if "valor_mercado" in df.columns:
        print(df["valor_mercado"].describe().to_string())

    print("\nDistribucion de edades:")
    if "edad" in df.columns:
        print(df["edad"].describe().to_string())


if __name__ == "__main__":
    run_eda()

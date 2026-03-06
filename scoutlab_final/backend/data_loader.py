"""
Modulo de carga de datos.
Centraliza la lectura de datasets procesados para su consumo
por la aplicacion Streamlit.
"""

import os
import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")


@st.cache_data(ttl=0)
def load_players(update_from_web: bool = False) -> pd.DataFrame:
    """
    Carga el dataset principal de jugadores con estadisticas
    y valores de mercado.
    """
    filepath = os.path.join(DATA_DIR, "jugadores.csv")
    if not os.path.exists(filepath):
        st.error("No se encontro el archivo de datos jugadores.csv")
        return pd.DataFrame()

    df = pd.read_csv(filepath)

    if update_from_web:
        df = _update_from_scraping(df)

    df = _clean_dataframe(df)
    return df


def _update_from_scraping(df: pd.DataFrame) -> pd.DataFrame:
    """Actualiza datos desde web scraping."""
    try:
        from backend.scraper import scrape_all_leagues

        scraped_df = scrape_all_leagues()
        if not scraped_df.empty:
            df["nombre_normalized"] = df["nombre"].str.lower().str.strip()
            scraped_df_copy = scraped_df.copy()
            scraped_df_copy["nombre_normalized"] = (
                scraped_df_copy["nombre"].str.lower().str.strip()
            )
            if "valor_mercado" in scraped_df_copy.columns:
                scraped_vals = scraped_df_copy[
                    ["nombre_normalized", "valor_mercado"]
                ].drop_duplicates()
                df = df.merge(
                    scraped_vals,
                    on="nombre_normalized",
                    how="left",
                    suffixes=("", "_web"),
                )
                df["valor_mercado"] = df["valor_mercado_web"].fillna(
                    df["valor_mercado"]
                )
                cols_to_drop = [c for c in df.columns if c.endswith("_web")]
                df = df.drop(columns=cols_to_drop)
            df = df.drop(columns=["nombre_normalized"], errors="ignore")
            os.makedirs(DATA_DIR, exist_ok=True)
            df.to_csv(os.path.join(DATA_DIR, "jugadores.csv"), index=False)
    except Exception as e:
        print(f"Error en web scraping: {e}")
    return df


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica limpieza basica al dataframe de jugadores."""
    numeric_cols = [
        "edad", "valor_mercado", "goles", "asistencias",
        "minutos", "partidos", "tarjetas_amarillas",
        "tarjetas_rojas", "goles_por_90", "asistencias_por_90",
        "participaciones_gol", "valor_predicho", "rating",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    str_cols = ["posicion", "equipo", "nombre", "liga", "pais", "nacionalidad"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    default_fields = {
        "partidos": 0,
        "minutos": 0,
        "goles": 0,
        "asistencias": 0,
        "tarjetas_amarillas": 0,
        "tarjetas_rojas": 0,
        "goles_por_90": 0.0,
        "asistencias_por_90": 0.0,
        "participaciones_gol": 0,
        "pie": "Derecho",
        "altura_cm": 180,
        "grupo": "",
        "temporada": "2025/26",
        "fecha_nacimiento": "",
        "pais": "",
        "rating": 6.0,
        "foto_url": "",
        "flag_url": "",
        "escudo_url": "",
    }

    for col, default_val in default_fields.items():
        if col not in df.columns:
            df[col] = default_val

    if "edad" in df.columns:
        df["edad"] = pd.to_numeric(df["edad"], errors="coerce").fillna(25).astype(int)

    if "valor_mercado" in df.columns:
        df["valor_mercado"] = (
            pd.to_numeric(df["valor_mercado"], errors="coerce").fillna(0)
        )

    return df


def get_teams_list(df: pd.DataFrame) -> list:
    return sorted(df["equipo"].unique().tolist())


def get_positions_list(df: pd.DataFrame) -> list:
    return sorted(df["posicion"].unique().tolist())


def get_leagues_list(df: pd.DataFrame) -> list:
    return sorted(df["liga"].unique().tolist())


def get_countries_list(df: pd.DataFrame) -> list:
    if "pais" in df.columns:
        return sorted(df["pais"].dropna().unique().tolist())
    return []


def get_nationalities_list(df: pd.DataFrame) -> list:
    return sorted(df["nacionalidad"].unique().tolist())

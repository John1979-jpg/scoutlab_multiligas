"""
Modulo de filtros del sidebar.
Renderiza y aplica filtros interactivos sobre el dataframe de jugadores.
"""

import pandas as pd
import streamlit as st


def render_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Renderiza filtros en sidebar y retorna df filtrado."""
    st.sidebar.markdown("### Filtros")
    filtered = df.copy()

    # --- Filtro por pais ---
    if "pais" in df.columns:
        paises = ["Todos"] + sorted(df["pais"].dropna().unique().tolist())
        pais_sel = st.sidebar.selectbox("Pais", paises, index=0)
        if pais_sel != "Todos":
            filtered = filtered[filtered["pais"] == pais_sel]

    # --- Filtro por liga ---
    ligas = ["Todas"] + sorted(filtered["liga"].dropna().unique().tolist())
    liga_sel = st.sidebar.selectbox("Liga", ligas, index=0)
    if liga_sel != "Todas":
        filtered = filtered[filtered["liga"] == liga_sel]

    # --- Filtro por equipo ---
    equipos = ["Todos"] + sorted(filtered["equipo"].dropna().unique().tolist())
    equipo_sel = st.sidebar.selectbox("Equipo", equipos, index=0)
    if equipo_sel != "Todos":
        filtered = filtered[filtered["equipo"] == equipo_sel]

    # --- Filtro por posicion ---
    posiciones = ["Todas"] + sorted(filtered["posicion"].dropna().unique().tolist())
    pos_sel = st.sidebar.selectbox("Posicion", posiciones, index=0)
    if pos_sel != "Todas":
        filtered = filtered[filtered["posicion"] == pos_sel]

    # --- Filtro por nacionalidad ---
    nacs = ["Todas"] + sorted(filtered["nacionalidad"].dropna().unique().tolist())
    nac_sel = st.sidebar.selectbox("Nacionalidad", nacs, index=0)
    if nac_sel != "Todas":
        filtered = filtered[filtered["nacionalidad"] == nac_sel]

    st.sidebar.markdown("---")

    # --- Busqueda por nombre (text_input) ---
    busqueda = st.sidebar.text_input("Buscar jugador", placeholder="Nombre...")
    if busqueda:
        filtered = filtered[
            filtered["nombre"].str.lower().str.contains(busqueda.lower(), na=False)
        ]

    st.sidebar.markdown("---")

    # --- Rango de edad (slider) ---
    edad_min = int(df["edad"].min())
    edad_max = int(df["edad"].max())
    edad_rango = st.sidebar.slider(
        "Rango de edad", edad_min, edad_max, (edad_min, edad_max)
    )
    filtered = filtered[
        (filtered["edad"] >= edad_rango[0]) & (filtered["edad"] <= edad_rango[1])
    ]

    # --- Rango de fecha nacimiento (date_input) ---
    if "fecha_nacimiento" in df.columns:
        df_fechas = pd.to_datetime(df["fecha_nacimiento"], errors="coerce").dropna()
        if len(df_fechas) > 0:
            fecha_min = df_fechas.min().date()
            fecha_max = df_fechas.max().date()
            col_f1, col_f2 = st.sidebar.columns(2)
            with col_f1:
                f_desde = st.date_input("Nacido desde", value=fecha_min, key="fnac_desde")
            with col_f2:
                f_hasta = st.date_input("Nacido hasta", value=fecha_max, key="fnac_hasta")
            filtered_fechas = pd.to_datetime(filtered["fecha_nacimiento"], errors="coerce")
            mask = (filtered_fechas >= pd.Timestamp(f_desde)) & (
                filtered_fechas <= pd.Timestamp(f_hasta)
            )
            filtered = filtered[mask | filtered_fechas.isna()]

    # --- Rango de valor de mercado (slider) ---
    val_min = int(df["valor_mercado"].min())
    val_max = int(df["valor_mercado"].max())
    if val_max > val_min:
        valor_rango = st.sidebar.slider(
            "Valor de mercado (EUR)",
            val_min, val_max, (val_min, val_max),
            step=5000, format="%d",
        )
        filtered = filtered[
            (filtered["valor_mercado"] >= valor_rango[0])
            & (filtered["valor_mercado"] <= valor_rango[1])
        ]

    # --- Minutos jugados (slider) ---
    max_min = int(df["minutos"].max())
    min_min = st.sidebar.slider("Minutos jugados (min)", 0, max_min, 0, step=90)
    filtered = filtered[filtered["minutos"] >= min_min]

    st.sidebar.markdown("---")

    # --- Checkboxes ---
    if st.sidebar.checkbox("Solo jugadores con goles"):
        filtered = filtered[filtered["goles"] > 0]

    if st.sidebar.checkbox("Solo jugadores con asistencias"):
        filtered = filtered[filtered["asistencias"] > 0]

    if st.sidebar.checkbox("Sin tarjetas rojas"):
        filtered = filtered[filtered["tarjetas_rojas"] == 0]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**{len(filtered)}** jugadores de **{len(df)}** totales")

    return filtered


def apply_quick_filter(df, column, value):
    """Aplica un filtro rapido sobre una columna."""
    if value and value != "Todos" and value != "Todas":
        return df[df[column] == value]
    return df

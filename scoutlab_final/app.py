"""
ScoutLab - Plataforma de Scouting Profesional
Punto de entrada principal de la aplicacion Streamlit.
"""

import streamlit as st

st.set_page_config(
    page_title="ScoutLab",
    page_icon="&#9917;",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Source Sans 3', sans-serif;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    h1 { color: #1B4332; font-weight: 700; letter-spacing: -0.5px; }
    h2, h3 { color: #1B4332; }

    /* Sidebar */
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F8FAE6 0%, #F0FDF4 100%);
    }
    .sidebar-header {
        font-size: 22px;
        font-weight: 700;
        color: #1B4332;
        padding: 4px 0 8px 0;
        border-bottom: 2px solid #1B4332;
        margin-bottom: 12px;
        letter-spacing: -0.3px;
    }
    .sidebar-user {
        font-size: 13px;
        color: #6B7280;
        margin-bottom: 8px;
    }

    /* Botones */
    .stButton > button {
        background-color: #1B4332;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: background-color 0.2s;
    }
    .stButton > button:hover {
        background-color: #2D6A4F;
    }

    /* Metricas */
    div[data-testid="stMetricValue"] {
        color: #1B4332;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        color: #6B7280;
        font-size: 13px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        color: #374151;
    }
    .stTabs [aria-selected="true"] {
        color: #1B4332;
    }

    /* Dataframes */
    .stDataFrame {
        border-radius: 8px;
    }

    /* Selectbox y inputs */
    div[data-baseweb="select"] {
        border-radius: 8px;
    }

    /* Footer */
    .app-footer {
        text-align: center;
        color: #9CA3AF;
        font-size: 12px;
        padding: 16px 0;
        margin-top: 24px;
        border-top: 1px solid #E5E7EB;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

from backend.auth import login_form, logout, get_current_user
from backend.data_loader import load_players
from backend.filters import render_sidebar_filters
import pandas as pd


def main():
    """Funcion principal de la aplicacion."""
    if not login_form():
        return

    user = get_current_user()
    if not user:
        user = {"nombre": "Invitado"}

    df = load_players()

    if df.empty:
        st.error("No se pudieron cargar los datos. Verifica el archivo jugadores.csv")
        return

    # --- Sidebar ---
    st.sidebar.markdown(
        '<div class="sidebar-header">ScoutLab</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        '<div class="sidebar-user">Sesion: <b>' + user["nombre"] + "</b></div>",
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Cerrar sesion", use_container_width=True):
        logout()

    st.sidebar.markdown("---")

    # Importar datos
    with st.sidebar.expander("Importar datos", expanded=False):
        st.markdown("**Importar desde CSV**")
        st.caption("Sube un CSV con datos de rendimiento")
        uploaded_file = st.file_uploader("Seleccionar archivo CSV", type=["csv"])
        if uploaded_file is not None:
            if st.button("Importar datos"):
                with st.spinner("Importando datos..."):
                    from backend.data_import import import_from_csv, merge_data
                    df_new = import_from_csv(uploaded_file)
                    if not df_new.empty:
                        df_merged = merge_data(df, df_new)
                        df_merged.to_csv("data/processed/jugadores.csv", index=False)
                        st.success(f"Importados {len(df_new)} jugadores")
                        st.rerun()
                    else:
                        st.error("Error al importar datos")

    with st.sidebar.expander("Actualizar datos (Web Scraping)", expanded=False):
        st.caption("Descarga datos reales de Transfermarkt (stats + valores)")

        from backend.scraper import LEAGUES

        all_leagues = sorted(LEAGUES.keys())
        selected_leagues = st.multiselect(
            "Ligas a scrapear",
            all_leagues,
            default=["Premier League", "LaLiga", "Serie A", "Bundesliga", "Ligue 1"],
            key="scrape_leagues",
        )

        if st.button("Iniciar scraping", type="primary", key="btn_scrape"):
            import os
            processed_dir = os.path.join(os.path.dirname(__file__), "data", "processed")
            os.makedirs(processed_dir, exist_ok=True)

            progress = st.progress(10, text="Scrapeando Transfermarkt...")
            try:
                from backend.scraper import scrape_all
                output_csv = os.path.join(processed_dir, "jugadores.csv")
                df_scraped = scrape_all(leagues=selected_leagues, output_path=output_csv)

                if not df_scraped.empty:
                    progress.progress(80, text="Reentrenando modelo ML...")

                    # Reentrenar ML
                    try:
                        from backend.data_loader import _clean_dataframe
                        from backend.ml_model import train_model
                        df_clean = _clean_dataframe(df_scraped.copy())
                        df_train = df_clean[
                            (df_clean["valor_mercado"] > 0) & (df_clean["minutos"] > 0)
                        ]
                        if len(df_train) > 50:
                            metrics = train_model(df_train)
                            st.success(
                                f"Datos: {len(df_scraped)} jugadores | "
                                f"ML R2: {metrics['r2_test']:.3f}"
                            )
                        else:
                            st.success(f"Datos: {len(df_scraped)} jugadores")
                    except Exception as e:
                        st.warning(f"ML: {e}")
                        st.success(f"Datos: {len(df_scraped)} jugadores guardados")

                    progress.progress(100, text="Completado")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("No se obtuvieron datos")
                    progress.empty()

            except Exception as e:
                st.error(f"Error: {e}")
                progress.empty()

    st.sidebar.markdown("---")

    # Navegacion
    page = st.sidebar.radio(
        "Navegacion",
        ["Inicio", "Estadisticas", "Comparador", "Watchlist"],
        label_visibility="collapsed",
    )

    st.sidebar.markdown("---")

    # Filtros
    df_filtered = render_sidebar_filters(df)

    # --- Contenido principal ---
    if page == "Inicio":
        from views.home import render_home
        render_home(df_filtered, df)
    elif page == "Estadisticas":
        from views.stats import render_stats
        render_stats(df_filtered, df)
    elif page == "Comparador":
        from views.comparator import render_comparator
        render_comparator(df_filtered, df)
    elif page == "Watchlist":
        from views.watchlist import render_watchlist
        render_watchlist(df_filtered, df)

    # Footer
    st.markdown(
        '<div class="app-footer">'
        "ScoutLab - Plataforma de Scouting Profesional | "
        "TFM Master en Python Avanzado Aplicado al Deporte (MPAD)"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

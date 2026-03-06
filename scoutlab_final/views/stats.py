"""
Pagina de Estadisticas (Stats).
Analisis detallado de jugadores individuales, comparativas,
metricas avanzadas con ML y buscador de jugadores similares.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from backend.pdf_export import generate_player_report
from backend.ml_model import predict_value, train_model


def render_stats(df_filtered, df_full):
    st.title("Estadisticas Avanzadas")
    st.caption("Analisis individual, Machine Learning y buscador de jugadores similares")

    tab1, tab2, tab3 = st.tabs([
        "Analisis Individual",
        "Jugadores Similares",
        "Modelo ML",
    ])

    with tab1:
        _render_individual_analysis(df_filtered)

    with tab2:
        _render_similar_players(df_filtered, df_full)

    with tab3:
        _render_ml_analysis(df_filtered, df_full)


def _get_flag(nationality: str) -> str:
    """Retorna emoji de bandera basado en nacionalidad."""
    flags = {
        "spain": "\U0001F1EA\U0001F1F8", "espana": "\U0001F1EA\U0001F1F8",
        "france": "\U0001F1EB\U0001F1F7", "francia": "\U0001F1EB\U0001F1F7",
        "germany": "\U0001F1E9\U0001F1EA", "alemania": "\U0001F1E9\U0001F1EA",
        "england": "\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F",
        "italy": "\U0001F1EE\U0001F1F9", "italia": "\U0001F1EE\U0001F1F9",
        "portugal": "\U0001F1F5\U0001F1F9",
        "brazil": "\U0001F1E7\U0001F1F7", "brasil": "\U0001F1E7\U0001F1F7",
        "argentina": "\U0001F1E6\U0001F1F7",
        "netherlands": "\U0001F1F3\U0001F1F1", "paises bajos": "\U0001F1F3\U0001F1F1",
        "belgium": "\U0001F1E7\U0001F1EA", "belgica": "\U0001F1E7\U0001F1EA",
        "croatia": "\U0001F1ED\U0001F1F7", "croacia": "\U0001F1ED\U0001F1F7",
        "uruguay": "\U0001F1FA\U0001F1FE",
        "colombia": "\U0001F1E8\U0001F1F4",
        "mexico": "\U0001F1F2\U0001F1FD",
        "united states": "\U0001F1FA\U0001F1F8", "usa": "\U0001F1FA\U0001F1F8",
        "japan": "\U0001F1EF\U0001F1F5", "japon": "\U0001F1EF\U0001F1F5",
        "south korea": "\U0001F1F0\U0001F1F7", "corea del sur": "\U0001F1F0\U0001F1F7",
        "turkey": "\U0001F1F9\U0001F1F7", "turquia": "\U0001F1F9\U0001F1F7",
        "morocco": "\U0001F1F2\U0001F1E6", "marruecos": "\U0001F1F2\U0001F1E6",
        "senegal": "\U0001F1F8\U0001F1F3",
        "nigeria": "\U0001F1F3\U0001F1EC",
        "cameroon": "\U0001F1E8\U0001F1F2", "camerun": "\U0001F1E8\U0001F1F2",
        "ghana": "\U0001F1EC\U0001F1ED",
        "ivory coast": "\U0001F1E8\U0001F1EE", "costa de marfil": "\U0001F1E8\U0001F1EE",
        "egypt": "\U0001F1EA\U0001F1EC", "egipto": "\U0001F1EA\U0001F1EC",
        "algeria": "\U0001F1E9\U0001F1FF", "argelia": "\U0001F1E9\U0001F1FF",
        "poland": "\U0001F1F5\U0001F1F1", "polonia": "\U0001F1F5\U0001F1F1",
        "austria": "\U0001F1E6\U0001F1F9",
        "switzerland": "\U0001F1E8\U0001F1ED", "suiza": "\U0001F1E8\U0001F1ED",
        "scotland": "\U0001F3F4\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F",
        "escocia": "\U0001F3F4\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F",
        "wales": "\U0001F3F4\U000E0067\U000E0062\U000E0077\U000E006C\U000E0073\U000E007F",
        "ireland": "\U0001F1EE\U0001F1EA", "irlanda": "\U0001F1EE\U0001F1EA",
        "denmark": "\U0001F1E9\U0001F1F0", "dinamarca": "\U0001F1E9\U0001F1F0",
        "sweden": "\U0001F1F8\U0001F1EA", "suecia": "\U0001F1F8\U0001F1EA",
        "norway": "\U0001F1F3\U0001F1F4", "noruega": "\U0001F1F3\U0001F1F4",
        "finland": "\U0001F1EB\U0001F1EE", "finlandia": "\U0001F1EB\U0001F1EE",
        "czech republic": "\U0001F1E8\U0001F1FF", "chequia": "\U0001F1E8\U0001F1FF",
        "serbia": "\U0001F1F7\U0001F1F8",
        "greece": "\U0001F1EC\U0001F1F7", "grecia": "\U0001F1EC\U0001F1F7",
        "romania": "\U0001F1F7\U0001F1F4", "rumania": "\U0001F1F7\U0001F1F4",
        "hungary": "\U0001F1ED\U0001F1FA", "hungria": "\U0001F1ED\U0001F1FA",
        "ukraine": "\U0001F1FA\U0001F1E6", "ucrania": "\U0001F1FA\U0001F1E6",
        "russia": "\U0001F1F7\U0001F1FA", "rusia": "\U0001F1F7\U0001F1FA",
        "chile": "\U0001F1E8\U0001F1F1",
        "peru": "\U0001F1F5\U0001F1EA",
        "ecuador": "\U0001F1EA\U0001F1E8",
        "venezuela": "\U0001F1FB\U0001F1EA",
        "paraguay": "\U0001F1F5\U0001F1FE",
        "canada": "\U0001F1E8\U0001F1E6",
        "australia": "\U0001F1E6\U0001F1FA",
        "china": "\U0001F1E8\U0001F1F3",
        "india": "\U0001F1EE\U0001F1F3",
        "israel": "\U0001F1EE\U0001F1F1",
        "iran": "\U0001F1EE\U0001F1F7",
        "tunisia": "\U0001F1F9\U0001F1F3", "tunez": "\U0001F1F9\U0001F1F3",
        "congo": "\U0001F1E8\U0001F1E9",
        "dr congo": "\U0001F1E8\U0001F1E9",
        "mali": "\U0001F1F2\U0001F1F1",
        "guinea": "\U0001F1EC\U0001F1F3",
        "jamaica": "\U0001F1EF\U0001F1F2",
        "costa rica": "\U0001F1E8\U0001F1F7",
        "honduras": "\U0001F1ED\U0001F1F3",
        "panama": "\U0001F1F5\U0001F1E6",
        "el salvador": "\U0001F1F8\U0001F1FB",
        "north macedonia": "\U0001F1F2\U0001F1F0",
        "slovenia": "\U0001F1F8\U0001F1EE", "eslovenia": "\U0001F1F8\U0001F1EE",
        "slovakia": "\U0001F1F8\U0001F1F0", "eslovaquia": "\U0001F1F8\U0001F1F0",
        "bosnia-herzegovina": "\U0001F1E7\U0001F1E6",
        "montenegro": "\U0001F1F2\U0001F1EA",
        "albania": "\U0001F1E6\U0001F1F1",
        "iceland": "\U0001F1EE\U0001F1F8", "islandia": "\U0001F1EE\U0001F1F8",
        "georgia": "\U0001F1EC\U0001F1EA",
        "bulgaria": "\U0001F1E7\U0001F1EC",
        "cote d'ivoire": "\U0001F1E8\U0001F1EE",
        "burkina faso": "\U0001F1E7\U0001F1EB",
        "gabon": "\U0001F1EC\U0001F1E6",
        "equatorial guinea": "\U0001F1EC\U0001F1F6",
        "mozambique": "\U0001F1F2\U0001F1FF",
        "south africa": "\U0001F1FF\U0001F1E6", "sudafrica": "\U0001F1FF\U0001F1E6",
        "new zealand": "\U0001F1F3\U0001F1FF", "nueva zelanda": "\U0001F1F3\U0001F1FF",
    }
    if not nationality:
        return ""
    key = str(nationality).lower().strip()
    return flags.get(key, "")


def _render_individual_analysis(df):
    st.subheader("Ficha del jugador")

    if df is None or df.empty:
        st.warning("No hay datos disponibles")
        return

    jugadores = sorted(df["nombre"].unique().tolist())
    if not jugadores:
        st.warning("No hay jugadores con los filtros seleccionados.")
        return

    jugador_sel = st.selectbox("Selecciona un jugador", jugadores, key="stats_jugador")
    jugador_data = df[df["nombre"] == jugador_sel].iloc[0]

    c1, c2 = st.columns([1, 2])

    with c1:
        # Foto del jugador
        foto = str(jugador_data.get("foto_url", ""))
        foto = foto.replace("/tiny/", "/head/").replace("/small/", "/header/")
        if foto.startswith("http"):
            st.image(foto, width=120)

        st.markdown(f"### {jugador_data['nombre']}")

        # Escudo del equipo
        escudo = str(jugador_data.get("escudo_url", ""))
        escudo = escudo.replace("/tiny/", "/head/").replace("/small/", "/head/")
        equipo_text = jugador_data.get("equipo", "-")
        if escudo.startswith("http"):
            st.markdown(
                f'<img src="{escudo}" width="20" style="vertical-align:middle"> '
                f'<b>{equipo_text}</b>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"**Equipo:** {equipo_text}")

        nac = jugador_data.get("nacionalidad", "-")
        flag_emoji = _get_flag(nac)
        info_items = [
            ("Liga", jugador_data.get("liga", "-")),
            ("Posicion", jugador_data.get("posicion", "-")),
            ("Edad", str(int(jugador_data["edad"]))),
            ("Nacionalidad", f"{flag_emoji} {nac}" if flag_emoji else nac),
            ("Altura", f"{int(jugador_data.get('altura_cm', 0))} cm"),
            ("Pie", jugador_data.get("pie", "-")),
            ("Rating", f"{jugador_data.get('rating', '-')}"),
        ]
        for label, value in info_items:
            st.markdown(f"**{label}:** {value}")

        valor = jugador_data["valor_mercado"]
        if valor >= 1_000_000:
            vstr = "{:.2f}M EUR".format(valor / 1_000_000)
        else:
            vstr = "{:.0f}K EUR".format(valor / 1_000)
        st.markdown(f"**Valor de mercado:** {vstr}")

    with c2:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Partidos", int(jugador_data["partidos"]))
        with m2:
            st.metric("Goles", int(jugador_data["goles"]))
        with m3:
            st.metric("Asistencias", int(jugador_data["asistencias"]))
        with m4:
            st.metric("Minutos", f"{int(jugador_data['minutos']):,}")

        # Radar chart
        categories = ["Goles", "Asistencias", "Partidos", "Minutos", "Valor"]
        maxvals = {
            "goles": max(df["goles"].max(), 1),
            "asistencias": max(df["asistencias"].max(), 1),
            "partidos": max(df["partidos"].max(), 1),
            "minutos": max(df["minutos"].max(), 1),
            "valor_mercado": max(df["valor_mercado"].max(), 1),
        }
        keys = ["goles", "asistencias", "partidos", "minutos", "valor_mercado"]
        values = [jugador_data[k] / maxvals[k] * 100 for k in keys]
        values.append(values[0])
        cats_r = categories + [categories[0]]

        fig = go.Figure()
        fig.add_trace(
            go.Scatterpolar(
                r=values, theta=cats_r, fill="toself",
                fillcolor="rgba(27,67,50,0.15)",
                line=dict(color="#1B4332", width=2),
                name=jugador_data["nombre"],
            )
        )
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=False,
            height=300,
            margin=dict(l=40, r=40, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Comparacion con media de posicion
    st.subheader("Comparacion con la media de su posicion")
    pos = jugador_data["posicion"]
    pos_df = df[df["posicion"] == pos]

    comp_data = {
        "Metrica": ["Goles", "Asistencias", "Partidos", "Minutos", "T. Amarillas", "Rating"],
        jugador_data["nombre"]: [
            jugador_data["goles"], jugador_data["asistencias"],
            jugador_data["partidos"], jugador_data["minutos"],
            jugador_data["tarjetas_amarillas"], jugador_data.get("rating", 0),
        ],
        f"Media {pos}": [
            round(pos_df["goles"].mean(), 1), round(pos_df["asistencias"].mean(), 1),
            round(pos_df["partidos"].mean(), 1), round(pos_df["minutos"].mean(), 1),
            round(pos_df["tarjetas_amarillas"].mean(), 1),
            round(pos_df["rating"].mean(), 1) if "rating" in pos_df.columns else 0,
        ],
    }
    st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

    st.markdown("---")
    if st.button("Exportar ficha a PDF", key="stats_pdf_ind"):
        pdata = jugador_data.to_dict()
        pdf_bytes = generate_player_report(pdata)
        fname = f"ficha_{jugador_data['nombre'].replace(' ', '_')}.pdf"
        st.download_button(
            "Descargar PDF", data=pdf_bytes, file_name=fname,
            mime="application/pdf", key="stats_dl_ind",
        )


def _render_similar_players(df, df_full):
    """Buscador de jugadores similares basado en distancia euclidiana normalizada."""
    st.subheader("Buscador de jugadores similares")
    st.caption(
        "Encuentra jugadores con perfil estadistico similar. "
        "Utiliza distancia euclidiana normalizada sobre las metricas seleccionadas."
    )

    if df is None or df.empty:
        st.warning("No hay datos disponibles")
        return

    jugadores = sorted(df["nombre"].unique().tolist())
    if not jugadores:
        st.warning("No hay jugadores con los filtros seleccionados.")
        return

    col_sel, col_opts = st.columns([2, 1])
    with col_sel:
        jugador_ref = st.selectbox(
            "Jugador de referencia", jugadores, key="similar_ref"
        )
    with col_opts:
        n_similar = st.slider("Jugadores similares a mostrar", 3, 20, 10, key="similar_n")

    # Metricas para calcular similitud (SIN edad para evitar duplicados)
    available_metrics = [
        "goles", "asistencias", "partidos", "minutos",
        "goles_por_90", "asistencias_por_90", "valor_mercado",
        "tarjetas_amarillas", "rating",
    ]
    present = [m for m in available_metrics if m in df.columns]

    selected_metrics = st.multiselect(
        "Metricas para calcular similitud",
        present,
        default=[m for m in ["goles", "asistencias", "partidos", "minutos", "goles_por_90"] if m in present],
        key="similar_metrics",
    )

    if not selected_metrics:
        st.warning("Selecciona al menos una metrica.")
        return

    # Buscar en todo el dataset o solo filtrado
    search_scope = st.radio(
        "Buscar en:",
        ["Solo datos filtrados", "Todas las ligas"],
        horizontal=True,
        key="similar_scope",
    )
    search_df = df if search_scope == "Solo datos filtrados" else df_full

    # Calcular similitud
    ref_row = df[df["nombre"] == jugador_ref]
    if ref_row.empty:
        st.error("Jugador no encontrado")
        return
    ref_data = ref_row.iloc[0]

    df_calc = search_df.copy()
    df_calc = df_calc.dropna(subset=selected_metrics)

    # Normalizar
    for m in selected_metrics:
        col_max = df_calc[m].max()
        col_min = df_calc[m].min()
        rng = col_max - col_min
        if rng > 0:
            df_calc[f"_norm_{m}"] = (df_calc[m] - col_min) / rng
        else:
            df_calc[f"_norm_{m}"] = 0.0

    norm_cols = [f"_norm_{m}" for m in selected_metrics]

    # Valor de referencia normalizado
    ref_norm = []
    for m in selected_metrics:
        col_max = df_calc[m].max()
        col_min = df_calc[m].min()
        rng = col_max - col_min
        ref_norm.append((ref_data[m] - col_min) / rng if rng > 0 else 0.0)

    ref_norm = np.array(ref_norm)

    # Distancia euclidiana
    df_calc["_distancia"] = df_calc[norm_cols].apply(
        lambda row: np.sqrt(((row.values - ref_norm) ** 2).sum()), axis=1
    )

    # Excluir el propio jugador y ordenar
    similares = (
        df_calc[df_calc["nombre"] != jugador_ref]
        .sort_values("_distancia")
        .head(n_similar)
    )

    if similares.empty:
        st.info("No se encontraron jugadores similares.")
        return

    # Mostrar resultado
    st.markdown(f"**Jugadores mas similares a {jugador_ref}:**")

    # Calcular similitud
    max_dist = similares["_distancia"].max()
    similares["Similitud"] = similares["_distancia"].apply(
        lambda d: round((1 - d / max(max_dist, 0.001)) * 100, 1)
    )

    # Construir tabla limpia sin duplicados
    show_cols = ["nombre", "equipo", "liga", "posicion", "edad"]
    for m in selected_metrics:
        if m not in show_cols:
            show_cols.append(m)
    show_cols.append("Similitud")

    # Solo columnas que existen
    show_cols = [c for c in show_cols if c in similares.columns]

    result_df = similares[show_cols].copy().reset_index(drop=True)
    result_df.index = result_df.index + 1
    st.dataframe(result_df, use_container_width=True, height=min(400, 50 + n_similar * 35))

    # Radar comparativo: referencia vs top 3 similares
    st.markdown("---")
    st.subheader("Radar comparativo: Referencia vs Top 3 similares")

    top3 = similares.head(3)
    radar_metrics = selected_metrics[:6]

    fig_radar = go.Figure()
    colors = ["#1B4332", "#DC2626", "#2563EB", "#7C3AED"]

    max_vals = {m: max(search_df[m].max(), 1) for m in radar_metrics}
    ref_vals = [ref_data[m] / max_vals[m] * 100 for m in radar_metrics]
    ref_vals.append(ref_vals[0])
    radar_labels = [m.replace("_", " ").title() for m in radar_metrics]
    radar_labels.append(radar_labels[0])

    fig_radar.add_trace(
        go.Scatterpolar(
            r=ref_vals, theta=radar_labels, fill="toself",
            fillcolor="rgba(27,67,50,0.15)",
            line=dict(color=colors[0], width=2),
            name=jugador_ref,
        )
    )

    for i, (_, row) in enumerate(top3.iterrows()):
        vals = [row[m] / max_vals[m] * 100 for m in radar_metrics]
        vals.append(vals[0])
        c = colors[i + 1] if i + 1 < len(colors) else "#888888"
        fig_radar.add_trace(
            go.Scatterpolar(
                r=vals, theta=radar_labels, fill="toself",
                fillcolor=f"rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.08)",
                line=dict(color=c, width=2),
                name=row["nombre"],
            )
        )

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False)),
        height=420,
        margin=dict(l=60, r=60, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_radar, use_container_width=True)


def _render_ml_analysis(df, df_full):
    st.subheader("Prediccion de valor de mercado (Machine Learning)")
    st.markdown(
        "El modelo utiliza un **Gradient Boosting Regressor** entrenado con las "
        "estadisticas de rendimiento para estimar el valor de mercado. "
        "La diferencia entre el valor estimado y el real indica "
        "si un jugador esta infravalorado o sobrevalorado."
    )

    if st.button("Entrenar / Re-entrenar modelo", key="ml_train"):
        with st.spinner("Entrenando modelo..."):
            metrics = train_model(df_full)

        st.success("Modelo entrenado correctamente")

        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.metric("R2 (test)", "{:.3f}".format(metrics["r2_test"]))
        with mc2:
            st.metric("MAE (test)", "{:,.0f} EUR".format(metrics["mae_test"]))
        with mc3:
            st.metric("Muestras", metrics["n_samples"])

        st.subheader("Importancia de variables")
        fi = metrics.get("feature_importance", {})
        if fi:
            fi_df = pd.DataFrame(
                {"Variable": list(fi.keys()), "Importancia": list(fi.values())}
            )
            fi_df = fi_df.sort_values("Importancia", ascending=True)
            fig = px.bar(
                fi_df, x="Importancia", y="Variable", orientation="h",
                color_discrete_sequence=["#2D6A4F"],
            )
            fig.update_layout(
                height=400,
                margin=dict(l=0, r=20, t=10, b=40),
                plot_bgcolor="white",
                paper_bgcolor="white",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("Prediccion para jugadores filtrados")
    with st.spinner("Generando predicciones..."):
        df_pred = predict_value(df)

    if "valor_predicho" in df_pred.columns and df_pred["valor_predicho"].notna().any():
        df_valid = df_pred.dropna(subset=["valor_predicho"])

        fig = px.scatter(
            df_valid, x="valor_mercado", y="valor_predicho",
            hover_data=["nombre", "equipo", "posicion"],
            color="liga" if "liga" in df_valid.columns else "posicion",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        max_v = max(df_valid["valor_mercado"].max(), df_valid["valor_predicho"].max())
        fig.add_trace(
            go.Scatter(
                x=[0, max_v], y=[0, max_v], mode="lines",
                line=dict(color="#9CA3AF", dash="dash", width=1), showlegend=False,
            )
        )
        fig.update_layout(
            xaxis_title="Valor real (EUR)",
            yaxis_title="Valor predicho (EUR)",
            height=500,
            margin=dict(l=0, r=20, t=10, b=40),
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(gridcolor="#F0F0F0"),
            yaxis=dict(gridcolor="#F0F0F0"),
        )
        st.plotly_chart(fig, use_container_width=True)

        display_cols = [
            "nombre", "equipo", "liga", "posicion", "edad",
            "goles", "asistencias", "valor_mercado", "valor_predicho", "diferencia_valor",
        ]
        avail = [c for c in display_cols if c in df_valid.columns]
        st.dataframe(
            df_valid[avail]
            .sort_values("diferencia_valor", ascending=False)
            .head(20)
            .reset_index(drop=True),
            use_container_width=True,
        )
    else:
        st.info("Entrena el modelo primero usando el boton de arriba.")

    st.markdown("---")

    st.subheader("Exportar informe de jugador")
    jugadores = sorted(df["nombre"].unique().tolist())
    if jugadores:
        jsel = st.selectbox("Selecciona jugador", jugadores, key="ml_pdf_j")
        if st.button("Generar PDF", key="ml_pdf_btn"):
            jdata = df[df["nombre"] == jsel].iloc[0].to_dict()
            if "valor_predicho" in df_pred.columns:
                pred_row = df_pred[df_pred["nombre"] == jsel]
                if len(pred_row) > 0 and pd.notna(pred_row.iloc[0].get("valor_predicho")):
                    jdata["valor_predicho"] = pred_row.iloc[0]["valor_predicho"]
            pdf_bytes = generate_player_report(jdata)
            fname = f"ficha_ml_{jsel.replace(' ', '_')}.pdf"
            st.download_button(
                "Descargar PDF", data=pdf_bytes, file_name=fname,
                mime="application/pdf", key="ml_dl",
            )

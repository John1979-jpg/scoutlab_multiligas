"""
Pagina de Estadisticas (Stats).
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from backend.pdf_export import generate_player_report
from backend.ml_model import predict_value, train_model

# Mapa de nacionalidades a codigos de pais para flagcdn.com
COUNTRY_CODES = {
    "france": "fr", "spain": "es", "germany": "de", "italy": "it",
    "england": "gb-eng", "portugal": "pt", "brazil": "br", "argentina": "ar",
    "netherlands": "nl", "belgium": "be", "croatia": "hr", "uruguay": "uy",
    "colombia": "co", "mexico": "mx", "united states": "us", "japan": "jp",
    "south korea": "kr", "turkey": "tr", "morocco": "ma", "senegal": "sn",
    "nigeria": "ng", "cameroon": "cm", "ghana": "gh", "egypt": "eg",
    "algeria": "dz", "poland": "pl", "austria": "at", "switzerland": "ch",
    "scotland": "gb-sct", "wales": "gb-wls", "ireland": "ie", "denmark": "dk",
    "sweden": "se", "norway": "no", "finland": "fi", "czech republic": "cz",
    "serbia": "rs", "greece": "gr", "romania": "ro", "hungary": "hu",
    "ukraine": "ua", "russia": "ru", "chile": "cl", "peru": "pe",
    "ecuador": "ec", "venezuela": "ve", "paraguay": "py", "canada": "ca",
    "australia": "au", "china": "cn", "india": "in", "israel": "il",
    "iran": "ir", "tunisia": "tn", "mali": "ml", "guinea": "gn",
    "jamaica": "jm", "costa rica": "cr", "honduras": "hn", "panama": "pa",
    "ivory coast": "ci", "cote d'ivoire": "ci", "burkina faso": "bf",
    "gabon": "ga", "south africa": "za", "dr congo": "cd", "congo": "cg",
    "bosnia-herzegovina": "ba", "bosnia and herzegovina": "ba",
    "montenegro": "me", "albania": "al",
    "iceland": "is", "georgia": "ge", "bulgaria": "bg", "slovenia": "si",
    "slovakia": "sk", "north macedonia": "mk", "new zealand": "nz",
    "republic of ireland": "ie", "northern ireland": "gb-nir",
    "korea, south": "kr", "korea republic": "kr",
    "trinidad and tobago": "tt", "dominican republic": "do",
    "el salvador": "sv", "curacao": "cw", "suriname": "sr",
    "cape verde": "cv", "benin": "bj", "togo": "tg",
    "zambia": "zm", "zimbabwe": "zw", "angola": "ao",
    "mozambique": "mz", "equatorial guinea": "gq",
    "cuba": "cu", "haiti": "ht", "guyana": "gy",
    "paraguay": "py", "bolivia": "bo",
    "luxemburg": "lu", "luxembourg": "lu",
    "albania": "al", "kosovo": "xk",
    "norway": "no", "democratic republic of congo": "cd",
    # Variantes de Transfermarkt
    "türkei": "tr", "frankreich": "fr", "spanien": "es",
    "deutschland": "de", "italien": "it", "brasilien": "br",
    "argentinien": "ar", "kolumbien": "co", "mexiko": "mx",
    "vereinigte staaten": "us", "niederlande": "nl",
    "belgien": "be", "kroatien": "hr", "griechenland": "gr",
    "rumänien": "ro", "ungarn": "hu", "tschechien": "cz",
    "serbien": "rs", "bulgarien": "bg", "slowenien": "si",
    "slowakei": "sk", "nordmazedonien": "mk", "dänemark": "dk",
    "schweden": "se", "norwegen": "no", "finnland": "fi",
    "österreich": "at", "schweiz": "ch", "schottland": "gb-sct",
    "irland": "ie", "ägypten": "eg", "algerien": "dz",
    "marokko": "ma", "kamerun": "cm", "südafrika": "za",
    "neuseeland": "nz", "australien": "au",
}


def _get_flag_url(nationality):
    """Retorna URL de imagen de bandera."""
    if not nationality:
        return ""
    key = str(nationality).lower().strip()
    code = COUNTRY_CODES.get(key, "")
    if not code:
        return ""
    return f"https://flagcdn.com/w40/{code}.png"


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


def _render_individual_analysis(df):
    st.subheader("Ficha del jugador")

    if df is None or df.empty:
        st.warning("No hay datos disponibles")
        return

    # Crear opciones con nombre + equipo para evitar confusiones
    df_unique = df.drop_duplicates(subset=["nombre", "equipo"]).copy()
    df_unique["display"] = df_unique["nombre"] + "  (" + df_unique["equipo"] + ")"
    opciones = sorted(df_unique["display"].tolist())

    if not opciones:
        st.warning("No hay jugadores con los filtros seleccionados.")
        return

    seleccion = st.selectbox("Selecciona un jugador", opciones, key="stats_jugador")

    # Buscar el jugador por nombre + equipo
    fila = df_unique[df_unique["display"] == seleccion]
    if fila.empty:
        st.warning("Jugador no encontrado")
        return
    jugador_data = fila.iloc[0]

    c1, c2 = st.columns([1, 2])

    with c1:
        # Foto del jugador
        foto = str(jugador_data.get("foto_url", ""))
        foto = foto.replace("/tiny/", "/big/").replace("/small/", "/big/")
        if foto.startswith("http"):
            st.image(foto, width=120)

        st.markdown(f"### {jugador_data['nombre']}")

        # Escudo del equipo
        escudo = str(jugador_data.get("escudo_url", ""))
        escudo = escudo.replace("/tiny/", "/big/").replace("/small/", "/big/")
        equipo_text = str(jugador_data.get("equipo", "-"))
        if escudo.startswith("http"):
            st.markdown(
                f'<img src="{escudo}" width="45" style="vertical-align:middle; margin-right:8px">'
                f'<span style="font-size:18px; font-weight:bold">{equipo_text}</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"**Equipo:** {equipo_text}")

        # Info basica
        st.markdown(f"**Liga:** {jugador_data.get('liga', '-')}")
        st.markdown(f"**Posicion:** {jugador_data.get('posicion', '-')}")
        st.markdown(f"**Edad:** {int(jugador_data['edad'])}")

        # Nacionalidad con bandera imagen
        nac = str(jugador_data.get("nacionalidad", "-"))
        flag_url = _get_flag_url(nac)
        if flag_url:
            st.markdown(
                f'**Nacionalidad:** <img src="{flag_url}" width="30" '
                f'style="vertical-align:middle; margin:0 6px"> {nac}',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"**Nacionalidad:** {nac}")

        st.markdown(f"**Altura:** {int(jugador_data.get('altura_cm', 0))} cm")
        st.markdown(f"**Pie:** {jugador_data.get('pie', '-')}")

        valor = jugador_data["valor_mercado"]
        if valor >= 1_000_000:
            vstr = "{:.2f}M EUR".format(valor / 1_000_000)
        elif valor > 0:
            vstr = "{:.0f}K EUR".format(valor / 1_000)
        else:
            vstr = "-"
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
        "Metrica": ["Goles", "Asistencias", "Partidos", "Minutos", "T. Amarillas"],
        jugador_data["nombre"]: [
            jugador_data["goles"], jugador_data["asistencias"],
            jugador_data["partidos"], jugador_data["minutos"],
            jugador_data["tarjetas_amarillas"],
        ],
        f"Media {pos}": [
            round(pos_df["goles"].mean(), 1), round(pos_df["asistencias"].mean(), 1),
            round(pos_df["partidos"].mean(), 1), round(pos_df["minutos"].mean(), 1),
            round(pos_df["tarjetas_amarillas"].mean(), 1),
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
    st.subheader("Buscador de jugadores similares")
    st.caption(
        "Encuentra jugadores con perfil estadistico similar. "
        "Utiliza distancia euclidiana normalizada."
    )

    if df is None or df.empty:
        st.warning("No hay datos disponibles")
        return

    # Opciones con equipo
    df_u = df.drop_duplicates(subset=["nombre", "equipo"]).copy()
    df_u["display"] = df_u["nombre"] + "  (" + df_u["equipo"] + ")"
    opciones = sorted(df_u["display"].tolist())

    if not opciones:
        st.warning("No hay jugadores.")
        return

    col_sel, col_opts = st.columns([2, 1])
    with col_sel:
        sel_ref = st.selectbox("Jugador de referencia", opciones, key="similar_ref")
    with col_opts:
        n_similar = st.slider("Similares a mostrar", 3, 20, 10, key="similar_n")

    available_metrics = [
        "goles", "asistencias", "partidos", "minutos",
        "goles_por_90", "asistencias_por_90", "valor_mercado",
        "tarjetas_amarillas",
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

    search_scope = st.radio(
        "Buscar en:", ["Solo datos filtrados", "Todas las ligas"],
        horizontal=True, key="similar_scope",
    )
    search_df = df if search_scope == "Solo datos filtrados" else df_full

    # Buscar referencia
    ref_fila = df_u[df_u["display"] == sel_ref]
    if ref_fila.empty:
        st.error("Jugador no encontrado")
        return
    ref_data = ref_fila.iloc[0]
    ref_nombre = ref_data["nombre"]
    ref_equipo = ref_data["equipo"]

    df_calc = search_df.copy().dropna(subset=selected_metrics)

    # Normalizar
    for m in selected_metrics:
        rng = df_calc[m].max() - df_calc[m].min()
        if rng > 0:
            df_calc[f"_n_{m}"] = (df_calc[m] - df_calc[m].min()) / rng
        else:
            df_calc[f"_n_{m}"] = 0.0

    ncols = [f"_n_{m}" for m in selected_metrics]
    ref_norm = []
    for m in selected_metrics:
        rng = df_calc[m].max() - df_calc[m].min()
        ref_norm.append((ref_data[m] - df_calc[m].min()) / rng if rng > 0 else 0.0)
    ref_norm = np.array(ref_norm)

    df_calc["_dist"] = df_calc[ncols].apply(
        lambda r: np.sqrt(((r.values - ref_norm) ** 2).sum()), axis=1
    )

    # Excluir el propio jugador
    similares = df_calc[
        ~((df_calc["nombre"] == ref_nombre) & (df_calc["equipo"] == ref_equipo))
    ].sort_values("_dist").head(n_similar)

    if similares.empty:
        st.info("No se encontraron jugadores similares.")
        return

    st.markdown(f"**Jugadores mas similares a {ref_nombre} ({ref_equipo}):**")

    max_dist = max(similares["_dist"].max(), 0.001)
    similares["Similitud"] = similares["_dist"].apply(
        lambda d: round((1 - d / max_dist) * 100, 1)
    )

    show_cols = ["nombre", "equipo", "liga", "posicion", "edad"]
    for m in selected_metrics:
        if m not in show_cols:
            show_cols.append(m)
    show_cols.append("Similitud")
    show_cols = [c for c in show_cols if c in similares.columns]

    result_df = similares[show_cols].copy().reset_index(drop=True)
    result_df.index = result_df.index + 1
    st.dataframe(result_df, use_container_width=True, height=min(400, 50 + n_similar * 35))

    # Radar comparativo
    st.markdown("---")
    st.subheader("Radar comparativo")

    top3 = similares.head(3)
    radar_metrics = selected_metrics[:6]
    fig_r = go.Figure()
    colors = ["#1B4332", "#DC2626", "#2563EB", "#7C3AED"]

    max_vals = {m: max(search_df[m].max(), 1) for m in radar_metrics}
    ref_vals = [ref_data[m] / max_vals[m] * 100 for m in radar_metrics]
    ref_vals.append(ref_vals[0])
    labels = [m.replace("_", " ").title() for m in radar_metrics] + [radar_metrics[0].replace("_", " ").title()]

    fig_r.add_trace(go.Scatterpolar(
        r=ref_vals, theta=labels, fill="toself",
        fillcolor="rgba(27,67,50,0.15)", line=dict(color=colors[0], width=2),
        name=ref_nombre,
    ))

    for i, (_, row) in enumerate(top3.iterrows()):
        vals = [row[m] / max_vals[m] * 100 for m in radar_metrics]
        vals.append(vals[0])
        c = colors[min(i + 1, len(colors) - 1)]
        fig_r.add_trace(go.Scatterpolar(
            r=vals, theta=labels, fill="toself",
            fillcolor=f"rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.08)",
            line=dict(color=c, width=2), name=row["nombre"],
        ))

    fig_r.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False)),
        height=420, margin=dict(l=60, r=60, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_r, use_container_width=True)


def _render_ml_analysis(df, df_full):
    st.subheader("Prediccion de valor de mercado (Machine Learning)")
    st.markdown(
        "El modelo utiliza un **Gradient Boosting Regressor** entrenado con las "
        "estadisticas de rendimiento para estimar el valor de mercado."
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

        fi = metrics.get("feature_importance", {})
        if fi:
            st.subheader("Importancia de variables")
            fi_df = pd.DataFrame({"Variable": list(fi.keys()), "Importancia": list(fi.values())})
            fi_df = fi_df.sort_values("Importancia", ascending=True)
            fig = px.bar(fi_df, x="Importancia", y="Variable", orientation="h",
                        color_discrete_sequence=["#2D6A4F"])
            fig.update_layout(height=400, margin=dict(l=0, r=20, t=10, b=40),
                            plot_bgcolor="white", paper_bgcolor="white")
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
        fig.add_trace(go.Scatter(
            x=[0, max_v], y=[0, max_v], mode="lines",
            line=dict(color="#9CA3AF", dash="dash", width=1), showlegend=False,
        ))
        fig.update_layout(
            xaxis_title="Valor real (EUR)", yaxis_title="Valor predicho (EUR)",
            height=500, margin=dict(l=0, r=20, t=10, b=40),
            plot_bgcolor="white", paper_bgcolor="white",
            xaxis=dict(gridcolor="#F0F0F0"), yaxis=dict(gridcolor="#F0F0F0"),
        )
        st.plotly_chart(fig, use_container_width=True)

        display_cols = ["nombre", "equipo", "liga", "posicion", "edad",
                       "goles", "asistencias", "valor_mercado", "valor_predicho", "diferencia_valor"]
        avail = [c for c in display_cols if c in df_valid.columns]
        st.dataframe(
            df_valid[avail].sort_values("diferencia_valor", ascending=False).head(20).reset_index(drop=True),
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

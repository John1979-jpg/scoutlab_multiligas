"""
Pagina de comparador de jugadores.
Permite comparar las estadisticas de multiples jugadores.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render_comparator(df_filtered, df_full):
    st.title("Comparador de Jugadores")
    st.caption("Compara las estadisticas de varios jugadores lado a lado")

    if df_filtered is None or df_filtered.empty:
        st.warning("No hay datos disponibles. Carga datos primero.")
        return

    player_list = sorted(df_filtered["nombre"].unique().tolist())

    if len(player_list) < 2:
        st.warning("Se necesitan al menos 2 jugadores para comparar.")
        return

    cols = st.columns([2, 1])
    with cols[0]:
        selected_players = st.multiselect(
            "Selecciona jugadores para comparar",
            options=player_list,
            max_selections=5,
            key="comparator_players",
        )
    with cols[1]:
        st.markdown("<br>", unsafe_allow_html=True)
        show_percentiles = st.checkbox("Mostrar percentiles", value=True)

    if not selected_players or len(selected_players) < 2:
        st.info("Selecciona al menos 2 jugadores para comparar.")
        return

    compare_df = df_filtered[df_filtered["nombre"].isin(selected_players)].copy()

    if compare_df.empty:
        st.error("Error al cargar datos de jugadores seleccionados")
        return

    if show_percentiles:
        for col in ["goles", "asistencias", "valor_mercado"]:
            if col in df_filtered.columns:
                compare_df[f"{col}_pct"] = compare_df[col].apply(
                    lambda x: round((df_filtered[col] <= x).mean() * 100, 1)
                )

    # --- Comparacion directa ---
    st.markdown("### Comparacion directa")
    display_cols = [
        "nombre", "equipo", "liga", "posicion", "edad",
        "partidos", "goles", "asistencias", "minutos", "rating", "valor_mercado",
    ]
    avail = [c for c in display_cols if c in compare_df.columns]
    st.dataframe(
        compare_df[avail].set_index("nombre"),
        use_container_width=True,
    )

    if show_percentiles:
        st.markdown("### Percentiles")
        pct_cols = ["nombre"]
        for col in ["goles", "asistencias", "valor_mercado"]:
            pct_name = f"{col}_pct"
            if pct_name in compare_df.columns:
                pct_cols.append(pct_name)
        if len(pct_cols) > 1:
            st.dataframe(
                compare_df[pct_cols].set_index("nombre"),
                use_container_width=True,
            )

    # --- Radar comparativo ---
    st.markdown("### Radar comparativo")

    categories = ["Goles", "Asistencias", "Partidos", "Minutos", "Valor"]
    max_goles = max(df_filtered["goles"].max(), 1)
    max_ast = max(df_filtered["asistencias"].max(), 1)
    max_part = max(df_filtered["partidos"].max(), 1)
    max_min = max(df_filtered["minutos"].max(), 1)
    max_val = max(df_filtered["valor_mercado"].max(), 1)

    fig = go.Figure()
    colors = ["#1B4332", "#DC2626", "#2563EB", "#7C3AED", "#059669"]

    for i, player in enumerate(selected_players):
        rows = compare_df[compare_df["nombre"] == player]
        if rows.empty:
            continue
        pdata = rows.iloc[0]
        values = [
            pdata["goles"] / max_goles * 100,
            pdata["asistencias"] / max_ast * 100,
            pdata["partidos"] / max_part * 100,
            pdata["minutos"] / max_min * 100,
            pdata["valor_mercado"] / max_val * 100,
        ]
        values.append(values[0])
        cats_r = categories + [categories[0]]

        c = colors[i % len(colors)]
        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=cats_r,
                fill="toself",
                fillcolor=f"rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.12)",
                line=dict(color=c, width=2),
                name=player,
            )
        )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False)),
        showlegend=True,
        height=450,
        margin=dict(l=60, r=60, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Rankings ---
    st.markdown("### Rankings por metricas")

    tabs = st.tabs(["Goles", "Asistencias", "Valor", "Eficiencia"])

    with tabs[0]:
        top = df_filtered.nlargest(10, "goles")[
            ["nombre", "equipo", "liga", "posicion", "goles", "goles_por_90"]
        ]
        st.dataframe(top, use_container_width=True, hide_index=True)

    with tabs[1]:
        top = df_filtered.nlargest(10, "asistencias")[
            ["nombre", "equipo", "liga", "posicion", "asistencias", "asistencias_por_90"]
        ]
        st.dataframe(top, use_container_width=True, hide_index=True)

    with tabs[2]:
        top = df_filtered.nlargest(10, "valor_mercado")[
            ["nombre", "equipo", "liga", "posicion", "valor_mercado"]
        ].copy()
        top["valor_mercado"] = top["valor_mercado"].apply(
            lambda x: f"{x/1000:.0f}K" if x < 1_000_000 else f"{x/1_000_000:.1f}M"
        )
        st.dataframe(top, use_container_width=True, hide_index=True)

    with tabs[3]:
        min_minutos = 500
        df_eff = df_filtered[df_filtered["minutos"] >= min_minutos].copy()
        if len(df_eff) > 0:
            df_eff["goles_90"] = df_eff["goles"] / (df_eff["minutos"] / 90)
            df_eff["asist_90"] = df_eff["asistencias"] / (df_eff["minutos"] / 90)
            df_eff["participacion_90"] = df_eff["goles_90"] + df_eff["asist_90"]
            top = df_eff.nlargest(10, "participacion_90")[
                ["nombre", "equipo", "liga", "posicion", "goles_90", "asist_90", "participacion_90"]
            ].copy()
            for c in ["goles_90", "asist_90", "participacion_90"]:
                top[c] = top[c].apply(lambda x: f"{x:.2f}")
            st.dataframe(top, use_container_width=True, hide_index=True)
        else:
            st.info(f"No hay jugadores con mas de {min_minutos} minutos jugados.")

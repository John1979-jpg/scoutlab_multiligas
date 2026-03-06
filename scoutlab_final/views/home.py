"""
Pagina de Inicio (Home).
Muestra un resumen general del mercado, KPIs principales,
y los jugadores destacados.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from backend.pdf_export import generate_team_report, generate_player_report
from backend.ml_model import predict_value, get_undervalued_players, get_overvalued_players


def _format_value(v):
    if pd.isna(v) or v is None:
        return "-"
    if v >= 1_000_000:
        return "{:.1f}M".format(v / 1_000_000)
    return "{:.0f}K".format(v / 1_000)


def render_home(df_filtered, df_full):
    st.title("ScoutLab - Panel de Control")
    st.caption("Analisis de mercado y rendimiento de jugadores en tiempo real")

    # --- KPIs principales ---
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Jugadores", f"{len(df_filtered):,}")
    with c2:
        st.metric("Equipos", df_filtered["equipo"].nunique())
    with c3:
        st.metric("Ligas", df_filtered["liga"].nunique())
    with c4:
        st.metric("Valor total", _format_value(df_filtered["valor_mercado"].sum()))
    with c5:
        st.metric("Edad media", "{:.1f}".format(df_filtered["edad"].mean()))
    with c6:
        st.metric("Goles totales", f"{int(df_filtered['goles'].sum()):,}")

    st.markdown("---")

    # --- Fila 1: Valor por equipo + Scatter edad vs valor ---
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.subheader("Valor de plantilla por equipo (Top 15)")
        ve = (
            df_filtered.groupby("equipo")["valor_mercado"]
            .sum()
            .sort_values(ascending=True)
            .tail(15)
        )
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=ve.values,
                y=ve.index,
                orientation="h",
                marker=dict(
                    color=ve.values,
                    colorscale=[[0, "#2D6A4F"], [0.5, "#40916C"], [1, "#95D5B2"]],
                    showscale=False,
                ),
                text=[_format_value(x) for x in ve.values],
                textposition="outside",
                textfont=dict(size=9, color="#1B4332"),
            )
        )
        fig.update_layout(
            height=440,
            margin=dict(l=10, r=80, t=10, b=30),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=10),
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor="#F0F0F0"),
            yaxis=dict(tickfont=dict(size=9)),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Edad vs Valor de mercado")
        fig_scatter = px.scatter(
            df_filtered,
            x="edad",
            y="valor_mercado",
            color="liga",
            size="goles",
            hover_data=["nombre", "equipo", "posicion"],
            opacity=0.6,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_scatter.update_layout(
            height=440,
            margin=dict(l=10, r=10, t=10, b=30),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=10),
            legend=dict(font=dict(size=9), orientation="h", y=-0.15),
            xaxis=dict(title="Edad", gridcolor="#F0F0F0"),
            yaxis=dict(title="Valor (EUR)", gridcolor="#F0F0F0"),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")

    # --- Fila 2: Heatmap posicion x liga + Distribucion edades ---
    col_h, col_v = st.columns([1, 1])

    with col_h:
        st.subheader("Heatmap: Jugadores por posicion y liga")
        heatmap_data = (
            df_filtered.groupby(["liga", "posicion"])
            .size()
            .reset_index(name="count")
        )
        pivot = heatmap_data.pivot(index="posicion", columns="liga", values="count").fillna(0)
        fig_heat = px.imshow(
            pivot.values,
            labels=dict(x="Liga", y="Posicion", color="Jugadores"),
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            color_continuous_scale=["#F0FDF4", "#2D6A4F", "#1B4332"],
            aspect="auto",
        )
        fig_heat.update_layout(
            height=400,
            margin=dict(l=10, r=10, t=10, b=10),
            font=dict(size=9),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_v:
        st.subheader("Distribucion de edades")
        try:
            edad_data = df_filtered["edad"].dropna()
            if len(edad_data) > 0:
                fig2 = go.Figure()
                fig2.add_trace(
                    go.Violin(
                        x=edad_data,
                        box_visible=True,
                        line_color="#1B4332",
                        fillcolor="#40916C",
                        opacity=0.6,
                        meanline_visible=True,
                        points=False,
                    )
                )
                media_edad = edad_data.mean()
                fig2.add_vline(
                    x=media_edad, line_dash="dash", line_color="#DC2626",
                    annotation_text=f"Media: {media_edad:.1f}",
                    annotation_position="top right",
                )
                fig2.update_layout(
                    xaxis_title="Edad",
                    height=400,
                    margin=dict(l=10, r=20, t=10, b=30),
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font=dict(size=10),
                    showlegend=False,
                    yaxis=dict(showticklabels=False, showgrid=False),
                    xaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig2, use_container_width=True)
        except Exception:
            st.warning("No se pudo generar el grafico de edades")

    st.markdown("---")

    # --- Fila 3: Top goleadores + Top asistentes ---
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("Top 10 Goleadores")
        tg = (
            df_filtered.nlargest(10, "goles")[
                ["nombre", "equipo", "liga", "posicion", "goles", "partidos", "goles_por_90"]
            ]
            .reset_index(drop=True)
        )
        tg.index = tg.index + 1
        tg["goles_por_90"] = tg["goles_por_90"].apply(lambda x: f"{x:.2f}")
        st.dataframe(tg, use_container_width=True, height=390)

    with col_g2:
        st.subheader("Top 10 Asistentes")
        ta = (
            df_filtered.nlargest(10, "asistencias")[
                ["nombre", "equipo", "liga", "posicion", "asistencias", "partidos", "asistencias_por_90"]
            ]
            .reset_index(drop=True)
        )
        ta.index = ta.index + 1
        ta["asistencias_por_90"] = ta["asistencias_por_90"].apply(lambda x: f"{x:.2f}")
        st.dataframe(ta, use_container_width=True, height=390)

    st.markdown("---")

    # --- Fila 4: Infravalorados + Sobrevalorados ---
    col_val1, col_val2 = st.columns(2)

    with col_val1:
        st.subheader("Jugadores infravalorados")
        st.caption("Valor estimado > Valor actual - Oportunidades de mercado")
        with st.spinner("Calculando predicciones..."):
            uv = get_undervalued_players(df_filtered, top_n=10)
        if len(uv) > 0:
            uv_d = uv[
                ["nombre", "equipo", "posicion", "valor_mercado", "valor_predicho", "diferencia_valor"]
            ].reset_index(drop=True)
            uv_d["valor_mercado"] = uv_d["valor_mercado"].apply(_format_value)
            uv_d["valor_predicho"] = uv_d["valor_predicho"].apply(_format_value)
            uv_d["diferencia_valor"] = uv_d["diferencia_valor"].apply(
                lambda x: f"+{_format_value(x)}"
            )
            uv_d.index = uv_d.index + 1
            st.dataframe(uv_d, use_container_width=True, height=390)
        else:
            st.info("No se encontraron jugadores infravalorados con los filtros actuales.")

    with col_val2:
        st.subheader("Jugadores sobrevalorados")
        st.caption("Valor actual > Valor estimado - Riesgo de sobreprecio")
        with st.spinner("Calculando predicciones..."):
            ov = get_overvalued_players(df_filtered, top_n=10)
        if len(ov) > 0:
            ov_d = ov[
                ["nombre", "equipo", "posicion", "valor_mercado", "valor_predicho", "diferencia_valor"]
            ].reset_index(drop=True)
            ov_d["valor_mercado"] = ov_d["valor_mercado"].apply(_format_value)
            ov_d["valor_predicho"] = ov_d["valor_predicho"].apply(_format_value)
            ov_d["diferencia_valor"] = ov_d["diferencia_valor"].apply(_format_value)
            ov_d.index = ov_d.index + 1
            st.dataframe(ov_d, use_container_width=True, height=390)
        else:
            st.info("No se encontraron jugadores sobrevalorados.")

    st.markdown("---")

    # --- Fila 5: Posicion donut + Pie chart ---
    col_pos, col_pie = st.columns(2)

    with col_pos:
        st.subheader("Distribucion por posicion")
        pc = df_filtered["posicion"].value_counts()
        colors_pos = [
            "#1B4332", "#2D6A4F", "#40916C", "#52B788", "#74C69D",
            "#95D5B2", "#B7E4C7", "#D8F3DC", "#E9F5EC", "#C1E6D0",
        ]
        fig3 = go.Figure(
            data=[
                go.Pie(
                    labels=pc.index,
                    values=pc.values,
                    hole=0.55,
                    marker=dict(colors=colors_pos[: len(pc)]),
                    textinfo="label+percent",
                    textposition="outside",
                    textfont=dict(size=9),
                )
            ]
        )
        fig3.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=10, b=10),
            paper_bgcolor="white",
            font=dict(size=10),
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col_pie:
        st.subheader("Valor medio por liga")
        val_liga = (
            df_filtered.groupby("liga")["valor_mercado"]
            .mean()
            .sort_values(ascending=True)
        )
        fig_vl = go.Figure()
        fig_vl.add_trace(
            go.Bar(
                x=val_liga.values,
                y=val_liga.index,
                orientation="h",
                marker=dict(
                    color=["#1B4332", "#2D6A4F", "#40916C", "#52B788",
                           "#74C69D", "#95D5B2", "#B7E4C7", "#D8F3DC"][: len(val_liga)],
                ),
                text=[_format_value(x) for x in val_liga.values],
                textposition="outside",
                textfont=dict(size=10, color="#1B4332"),
            )
        )
        fig_vl.update_layout(
            height=380,
            margin=dict(l=10, r=80, t=10, b=30),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=10),
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor="#F0F0F0"),
        )
        st.plotly_chart(fig_vl, use_container_width=True)

    st.markdown("---")

    # --- Exportar informes ---
    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        st.subheader("Exportar informe de equipo")
        equipos = sorted(df_filtered["equipo"].unique().tolist())
        if not equipos:
            st.warning("No hay equipos disponibles")
        else:
            eq = st.selectbox("Selecciona equipo", equipos, key="home_pdf_eq")
            if st.button("Generar PDF equipo", key="home_pdf_btn"):
                edf = df_filtered[df_filtered["equipo"] == eq]
                pdf_bytes = generate_team_report(eq, edf)
                fname = f"informe_{eq.replace(' ', '_')}.pdf"
                st.download_button(
                    "Descargar PDF",
                    data=pdf_bytes,
                    file_name=fname,
                    mime="application/pdf",
                )

    with col_exp2:
        st.subheader("Exportar informe de jugador")
        jugadores = sorted(df_filtered["nombre"].unique().tolist())
        if not jugadores:
            st.warning("No hay jugadores disponibles")
        else:
            jug = st.selectbox("Selecciona jugador", jugadores, key="home_pdf_jug")
            df_pred = predict_value(df_filtered[df_filtered["nombre"] == jug])
            if st.button("Generar PDF jugador", key="home_pdf_jug_btn"):
                jug_data = df_pred.iloc[0].to_dict() if len(df_pred) > 0 else {}
                pdf_bytes = generate_player_report(jug_data)
                fname = f"informe_{jug.replace(' ', '_')}.pdf"
                st.download_button(
                    "Descargar PDF",
                    data=pdf_bytes,
                    file_name=fname,
                    mime="application/pdf",
                )

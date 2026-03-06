"""
Pagina de Watchlist (Seguimiento de Jugadores).
Permite al usuario marcar jugadores para seguimiento,
definir alertas basadas en metricas y exportar la lista.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from backend.pdf_export import generate_player_report
from backend.ml_model import predict_value


def _init_watchlist():
    """Inicializa la watchlist en session_state si no existe."""
    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = []
    if "watchlist_notes" not in st.session_state:
        st.session_state["watchlist_notes"] = {}
    if "watchlist_alerts" not in st.session_state:
        st.session_state["watchlist_alerts"] = {}


def _format_value(v):
    if pd.isna(v) or v is None:
        return "-"
    if v >= 1_000_000:
        return "{:.1f}M".format(v / 1_000_000)
    return "{:.0f}K".format(v / 1_000)


def render_watchlist(df_filtered, df_full):
    st.title("Watchlist - Seguimiento de Jugadores")
    st.caption(
        "Marca jugadores para seguimiento, anade notas personalizadas "
        "y configura alertas de rendimiento"
    )

    _init_watchlist()

    tabs = st.tabs(["Mi Watchlist", "Anadir Jugadores", "Alertas"])

    with tabs[0]:
        _render_my_watchlist(df_full)

    with tabs[1]:
        _render_add_players(df_filtered, df_full)

    with tabs[2]:
        _render_alerts(df_full)


def _render_my_watchlist(df_full):
    """Muestra la lista de jugadores en seguimiento."""
    watchlist = st.session_state["watchlist"]

    if not watchlist:
        st.info(
            "Tu watchlist esta vacia. Ve a la pestana 'Anadir Jugadores' "
            "para empezar a seguir jugadores."
        )
        return

    st.markdown(f"**{len(watchlist)} jugadores** en seguimiento")
    st.markdown("---")

    # Obtener datos de los jugadores en watchlist
    wl_df = df_full[df_full["nombre"].isin(watchlist)].copy()

    if wl_df.empty:
        st.warning("No se encontraron datos para los jugadores de tu watchlist.")
        return

    # KPIs de la watchlist
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Jugadores", len(wl_df))
    with c2:
        st.metric("Edad media", f"{wl_df['edad'].mean():.1f}")
    with c3:
        st.metric("Valor total", _format_value(wl_df["valor_mercado"].sum()))
    with c4:
        st.metric("Goles totales", int(wl_df["goles"].sum()))

    st.markdown("---")

    # Tabla principal
    display_cols = [
        "nombre", "equipo", "liga", "posicion", "edad",
        "goles", "asistencias", "partidos", "rating", "valor_mercado",
    ]
    avail = [c for c in display_cols if c in wl_df.columns]
    wl_display = wl_df[avail].sort_values("valor_mercado", ascending=False).reset_index(drop=True)
    wl_display.index = wl_display.index + 1
    st.dataframe(wl_display, use_container_width=True)

    # Notas por jugador
    st.markdown("---")
    st.subheader("Notas de scouting")
    notes = st.session_state["watchlist_notes"]

    for jugador in watchlist:
        with st.expander(jugador, expanded=False):
            col_note, col_actions = st.columns([3, 1])
            with col_note:
                current_note = notes.get(jugador, "")
                new_note = st.text_area(
                    "Nota", value=current_note,
                    key=f"note_{jugador}", label_visibility="collapsed",
                    placeholder="Escribe tus observaciones sobre este jugador...",
                )
                if new_note != current_note:
                    st.session_state["watchlist_notes"][jugador] = new_note

            with col_actions:
                if st.button("Quitar", key=f"remove_{jugador}", use_container_width=True):
                    st.session_state["watchlist"].remove(jugador)
                    st.session_state["watchlist_notes"].pop(jugador, None)
                    st.session_state["watchlist_alerts"].pop(jugador, None)
                    st.rerun()

                # PDF individual
                jug_rows = df_full[df_full["nombre"] == jugador]
                if not jug_rows.empty:
                    if st.button("PDF", key=f"pdf_{jugador}", use_container_width=True):
                        jdata = jug_rows.iloc[0].to_dict()
                        pdf_bytes = generate_player_report(jdata)
                        st.download_button(
                            "Descargar",
                            data=pdf_bytes,
                            file_name=f"ficha_{jugador.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            key=f"dl_{jugador}",
                        )

    # Radar de toda la watchlist
    if len(wl_df) >= 2:
        st.markdown("---")
        st.subheader("Radar comparativo de la watchlist")

        categories = ["Goles", "Asistencias", "Partidos", "Minutos", "Valor"]
        maxvals = {
            "goles": max(df_full["goles"].max(), 1),
            "asistencias": max(df_full["asistencias"].max(), 1),
            "partidos": max(df_full["partidos"].max(), 1),
            "minutos": max(df_full["minutos"].max(), 1),
            "valor_mercado": max(df_full["valor_mercado"].max(), 1),
        }
        keys = ["goles", "asistencias", "partidos", "minutos", "valor_mercado"]

        fig = go.Figure()
        colors = [
            "#1B4332", "#DC2626", "#2563EB", "#7C3AED", "#059669",
            "#D97706", "#DB2777", "#4F46E5", "#0891B2", "#65A30D",
        ]

        for i, (_, row) in enumerate(wl_df.head(10).iterrows()):
            vals = [row[k] / maxvals[k] * 100 for k in keys]
            vals.append(vals[0])
            c = colors[i % len(colors)]
            fig.add_trace(
                go.Scatterpolar(
                    r=vals,
                    theta=categories + [categories[0]],
                    fill="toself",
                    fillcolor=f"rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.08)",
                    line=dict(color=c, width=2),
                    name=row["nombre"],
                )
            )

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False)),
            height=450,
            margin=dict(l=60, r=60, t=30, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Limpiar watchlist
    st.markdown("---")
    if st.button("Vaciar toda la watchlist", type="secondary"):
        st.session_state["watchlist"] = []
        st.session_state["watchlist_notes"] = {}
        st.session_state["watchlist_alerts"] = {}
        st.rerun()


def _render_add_players(df_filtered, df_full):
    """Permite anadir jugadores a la watchlist."""
    st.subheader("Anadir jugadores a la watchlist")

    watchlist = st.session_state["watchlist"]

    # Busqueda rapida
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search = st.text_input(
            "Buscar por nombre", placeholder="Escribe el nombre...",
            key="wl_search",
        )
    with col_filter:
        pos_filter = st.selectbox(
            "Filtrar por posicion",
            ["Todas"] + sorted(df_filtered["posicion"].unique().tolist()),
            key="wl_pos_filter",
        )

    candidates = df_filtered.copy()
    if search:
        candidates = candidates[
            candidates["nombre"].str.lower().str.contains(search.lower(), na=False)
        ]
    if pos_filter != "Todas":
        candidates = candidates[candidates["posicion"] == pos_filter]

    # Excluir los que ya estan en watchlist
    candidates = candidates[~candidates["nombre"].isin(watchlist)]

    if candidates.empty:
        st.info("No hay jugadores disponibles con esos criterios.")
        return

    st.markdown(f"**{len(candidates)} jugadores** disponibles")

    # Mostrar top candidatos
    display_cols = [
        "nombre", "equipo", "liga", "posicion", "edad",
        "goles", "asistencias", "rating", "valor_mercado",
    ]
    avail = [c for c in display_cols if c in candidates.columns]
    top = candidates[avail].sort_values("valor_mercado", ascending=False).head(20)
    st.dataframe(top, use_container_width=True, hide_index=True)

    # Selector para anadir
    to_add = st.multiselect(
        "Selecciona jugadores para anadir",
        sorted(candidates["nombre"].unique().tolist()),
        key="wl_add_select",
    )

    if to_add and st.button("Anadir a watchlist", type="primary"):
        for name in to_add:
            if name not in st.session_state["watchlist"]:
                st.session_state["watchlist"].append(name)
        st.success(f"Anadidos {len(to_add)} jugadores a la watchlist")
        st.rerun()


def _render_alerts(df_full):
    """Sistema de alertas sobre jugadores de la watchlist."""
    st.subheader("Configurar alertas")
    st.caption(
        "Define umbrales para las metricas de tus jugadores. "
        "Cuando un jugador supere o no alcance el umbral, se marcara como alerta."
    )

    watchlist = st.session_state["watchlist"]

    if not watchlist:
        st.info("Anade jugadores a tu watchlist primero.")
        return

    # Configuracion de alertas globales
    st.markdown("### Umbrales de alerta")

    col1, col2, col3 = st.columns(3)
    with col1:
        min_goles = st.number_input("Goles minimos", min_value=0, value=5, key="alert_goles")
    with col2:
        min_asist = st.number_input("Asistencias minimas", min_value=0, value=3, key="alert_asist")
    with col3:
        max_edad = st.number_input("Edad maxima", min_value=16, max_value=45, value=30, key="alert_edad")

    col4, col5 = st.columns(2)
    with col4:
        min_minutos = st.number_input("Minutos minimos", min_value=0, value=500, step=100, key="alert_min")
    with col5:
        min_rating = st.number_input("Rating minimo", min_value=0.0, max_value=10.0, value=6.0, step=0.1, key="alert_rating")

    st.markdown("---")

    if st.button("Evaluar alertas", type="primary"):
        wl_df = df_full[df_full["nombre"].isin(watchlist)].copy()

        if wl_df.empty:
            st.warning("No se encontraron datos.")
            return

        # Evaluar condiciones
        alerts = []
        for _, row in wl_df.iterrows():
            issues = []
            if row["goles"] < min_goles:
                issues.append(f"Goles: {int(row['goles'])} < {min_goles}")
            if row["asistencias"] < min_asist:
                issues.append(f"Asist: {int(row['asistencias'])} < {min_asist}")
            if row["edad"] > max_edad:
                issues.append(f"Edad: {int(row['edad'])} > {max_edad}")
            if row["minutos"] < min_minutos:
                issues.append(f"Min: {int(row['minutos'])} < {min_minutos}")
            if "rating" in row and row["rating"] < min_rating:
                issues.append(f"Rating: {row['rating']:.1f} < {min_rating}")

            status = "OK" if not issues else "ALERTA"
            alerts.append({
                "Jugador": row["nombre"],
                "Equipo": row["equipo"],
                "Liga": row.get("liga", "-"),
                "Estado": status,
                "Alertas": " | ".join(issues) if issues else "Cumple todos los umbrales",
            })

        alerts_df = pd.DataFrame(alerts)

        # Resumen
        n_ok = len(alerts_df[alerts_df["Estado"] == "OK"])
        n_alert = len(alerts_df[alerts_df["Estado"] == "ALERTA"])

        c1, c2 = st.columns(2)
        with c1:
            st.metric("Cumplen umbrales", n_ok)
        with c2:
            st.metric("Con alertas", n_alert)

        # Tabla de alertas
        st.markdown("### Resultado de alertas")

        # Destacar alertas
        if n_alert > 0:
            st.markdown("**Jugadores con alertas:**")
            alert_rows = alerts_df[alerts_df["Estado"] == "ALERTA"]
            st.dataframe(alert_rows, use_container_width=True, hide_index=True)

        if n_ok > 0:
            st.markdown("**Jugadores que cumplen todos los umbrales:**")
            ok_rows = alerts_df[alerts_df["Estado"] == "OK"]
            st.dataframe(ok_rows, use_container_width=True, hide_index=True)

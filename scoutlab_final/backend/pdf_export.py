"""
Modulo de exportacion a PDF con fpdf2.
Informes profesionales de 1 pagina.
"""

import os
import re
import tempfile
import requests
from fpdf import FPDF


def _download_image(url) -> str:
    """Descarga imagen y retorna path temporal."""
    url = str(url) if url else ""
    if not url or not url.startswith("http"):
        return ""
    # Mejorar resolucion: pedir version grande
    url = url.replace("/tiny/", "/big/").replace("/small/", "/big/")
    url = url.replace("/kader/", "/header/").replace("/profil/", "/header/")
    # Para escudos: tiny -> normal
    if "wappen" in url or "verein" in url.lower():
        url = url.replace("/tiny/", "/normal/").replace("/small/", "/normal/")
    try:
        r = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        if r.status_code == 200 and len(r.content) > 200:
            ext = ".png" if "png" in url.lower() else ".jpg"
            tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except Exception:
        pass
    return ""


def _cleanup(path):
    if path:
        try:
            os.unlink(path)
        except Exception:
            pass


# Mapa de banderas: nacionalidad -> URL de flagcdn
FLAG_URL = "https://flagcdn.com/w40/{code}.png"
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
    "bosnia-herzegovina": "ba", "montenegro": "me", "albania": "al",
    "iceland": "is", "georgia": "ge", "bulgaria": "bg", "slovenia": "si",
    "slovakia": "sk", "north macedonia": "mk", "new zealand": "nz",
    "el salvador": "sv", "equatorial guinea": "gq", "mozambique": "mz",
    "cape verde": "cv", "benin": "bj", "togo": "tg", "zambia": "zm",
    "zimbabwe": "zw", "angola": "ao", "curacao": "cw", "suriname": "sr",
    "guyana": "gy", "haiti": "ht", "trinidad and tobago": "tt",
    "dominican republic": "do", "cuba": "cu", "korea, south": "kr",
    "republic of ireland": "ie", "northern ireland": "gb-nir",
}


def _get_flag_path(nationality: str) -> str:
    """Descarga bandera del pais y retorna path temporal."""
    if not nationality:
        return ""
    key = str(nationality).lower().strip()
    code = COUNTRY_CODES.get(key, "")
    if not code:
        return ""
    url = FLAG_URL.format(code=code)
    return _download_image(url)


class ScoutLabPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(27, 67, 50)
        self.cell(0, 6, "ScoutLab - Plataforma de Scouting Profesional", align="L")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(107, 114, 128)
        self.cell(0, 6, "Analista: John Triguero", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(27, 67, 50)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        from datetime import datetime
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(156, 163, 175)
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 8, f"Generado: {fecha} | Analista: John Triguero | ScoutLab", align="C")


def _format_euros(value):
    try:
        v = float(value)
        if v >= 1_000_000:
            return "{:.2f}M EUR".format(v / 1_000_000)
        return "{:,.0f} EUR".format(v)
    except (ValueError, TypeError):
        return "- EUR"


def generate_player_report(player_data: dict) -> bytes:
    """Genera informe PDF de 1 pagina."""
    pdf = ScoutLabPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    # === CABECERA: Foto + Nombre + Escudo ===
    y_top = pdf.get_y()

    # Foto jugador (izquierda)
    foto_path = _download_image(player_data.get("foto_url", ""))
    if foto_path:
        try:
            pdf.image(foto_path, x=10, y=y_top, w=25, h=30)
        except Exception:
            pass
        _cleanup(foto_path)

    # Escudo equipo (derecha)
    escudo_path = _download_image(player_data.get("escudo_url", ""))
    if escudo_path:
        try:
            pdf.image(escudo_path, x=178, y=y_top, w=18, h=18)
        except Exception:
            pass
        _cleanup(escudo_path)

    # Nombre y equipo
    x_name = 40 if foto_path else 10
    pdf.set_xy(x_name, y_top + 2)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(27, 67, 50)
    nombre = player_data.get("nombre", "Sin nombre")
    pdf.cell(130, 8, nombre)

    pdf.set_xy(x_name, y_top + 11)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(107, 114, 128)
    equipo = player_data.get("equipo", "-")
    liga = player_data.get("liga", "-")
    pdf.cell(130, 6, f"{equipo} | {liga}")

    # Bandera + nacionalidad
    nac = str(player_data.get("nacionalidad", "-"))
    flag_path = _get_flag_path(nac)
    pdf.set_xy(x_name, y_top + 19)
    if flag_path:
        try:
            pdf.image(flag_path, x=x_name, y=y_top + 19, h=5)
            pdf.set_x(x_name + 10)
        except Exception:
            pass
        _cleanup(flag_path)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(60, 6, nac)

    pdf.set_y(y_top + 32)

    # === DATOS PERSONALES (2 columnas) ===
    pdf.set_draw_color(229, 231, 235)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(27, 67, 50)
    pdf.cell(0, 6, "Datos Personales", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    campos_izq = [
        ("Posicion", player_data.get("posicion", "-")),
        ("Edad", str(player_data.get("edad", "-"))),
        ("Fecha nac.", str(player_data.get("fecha_nacimiento", "-"))),
        ("Pais", player_data.get("pais", "-")),
    ]
    campos_der = [
        ("Altura", f"{player_data.get('altura_cm', '-')} cm"),
        ("Pie", player_data.get("pie", "-")),
        ("Valor mercado", _format_euros(player_data.get("valor_mercado", 0))),
    ]

    y_datos = pdf.get_y()
    pdf.set_font("Helvetica", "", 8)
    for label, val in campos_izq:
        pdf.set_text_color(107, 114, 128)
        pdf.cell(30, 5, label, new_x="RIGHT")
        pdf.set_text_color(26, 26, 46)
        pdf.cell(65, 5, str(val), new_x="LMARGIN", new_y="NEXT")

    y_after_izq = pdf.get_y()
    pdf.set_y(y_datos)
    for label, val in campos_der:
        pdf.set_x(105)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(30, 5, label, new_x="RIGHT")
        pdf.set_text_color(26, 26, 46)
        pdf.cell(60, 5, str(val), new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(max(y_after_izq, pdf.get_y()) + 2)

    # === ESTADISTICAS (2 columnas) ===
    pdf.set_draw_color(229, 231, 235)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(27, 67, 50)
    pdf.cell(0, 6, "Estadisticas de Rendimiento", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    partidos = player_data.get("partidos", 0)
    minutos = player_data.get("minutos", 0)
    goles = player_data.get("goles", 0)
    asistencias = player_data.get("asistencias", 0)
    g90 = player_data.get("goles_por_90", 0)
    a90 = player_data.get("asistencias_por_90", 0)

    stats_izq = [
        ("Partidos", str(partidos)),
        ("Minutos", str(minutos)),
        ("Goles", str(goles)),
        ("Asistencias", str(asistencias)),
    ]
    stats_der = [
        ("G/90 min", f"{g90:.2f}" if g90 else "0.00"),
        ("A/90 min", f"{a90:.2f}" if a90 else "0.00"),
        ("T. Amarillas", str(player_data.get("tarjetas_amarillas", 0))),
        ("T. Rojas", str(player_data.get("tarjetas_rojas", 0))),
    ]

    y_stats = pdf.get_y()
    pdf.set_font("Helvetica", "", 8)
    for label, val in stats_izq:
        pdf.set_text_color(107, 114, 128)
        pdf.cell(30, 5, label, new_x="RIGHT")
        pdf.set_text_color(26, 26, 46)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(65, 5, val, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)

    y_after_stats = pdf.get_y()
    pdf.set_y(y_stats)
    for label, val in stats_der:
        pdf.set_x(105)
        pdf.set_text_color(107, 114, 128)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(30, 5, label, new_x="RIGHT")
        pdf.set_text_color(26, 26, 46)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(60, 5, val, new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(max(y_after_stats, pdf.get_y()) + 2)

    # === METRICAS AVANZADAS ===
    pdf.set_draw_color(229, 231, 235)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(27, 67, 50)
    pdf.cell(0, 6, "Metricas Avanzadas", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    min_per_match = f"{minutos/partidos:.1f}" if partidos > 0 else "-"
    participacion = (g90 or 0) + (a90 or 0)

    metricas = [
        ("Min/partido", min_per_match),
        ("Participacion G+A/90", f"{participacion:.2f}"),
        ("Gol+Asist total", f"{goles+asistencias}"),
    ]

    pdf.set_font("Helvetica", "", 8)
    for label, val in metricas:
        pdf.set_text_color(107, 114, 128)
        pdf.cell(40, 5, label, new_x="RIGHT")
        pdf.set_text_color(26, 26, 46)
        pdf.cell(50, 5, val, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)

    # === VALORACION ML ===
    valor = player_data.get("valor_mercado", 0)
    valor_pred = player_data.get("valor_predicho", None)

    if valor_pred and float(valor_pred) > 0:
        pdf.set_draw_color(229, 231, 235)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(27, 67, 50)
        pdf.cell(0, 6, "Valoracion Machine Learning", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

        diferencia = float(valor_pred) - float(valor)
        porcentaje = (diferencia / float(valor) * 100) if float(valor) > 0 else 0

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(40, 5, "Valor mercado", new_x="RIGHT")
        pdf.set_text_color(26, 26, 46)
        pdf.cell(50, 5, _format_euros(valor), new_x="LMARGIN", new_y="NEXT")

        pdf.set_text_color(107, 114, 128)
        pdf.cell(40, 5, "Valor estimado ML", new_x="RIGHT")
        pdf.set_text_color(26, 26, 46)
        pdf.cell(50, 5, _format_euros(valor_pred), new_x="LMARGIN", new_y="NEXT")

        pdf.set_text_color(107, 114, 128)
        pdf.cell(40, 5, "Diferencia", new_x="RIGHT")

        if diferencia > 0:
            pdf.set_text_color(22, 163, 74)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, f"+{_format_euros(abs(diferencia))} (+{porcentaje:.1f}%) - INFRAVALORADO",
                     new_x="LMARGIN", new_y="NEXT")
        elif diferencia < 0:
            pdf.set_text_color(220, 38, 38)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, f"-{_format_euros(abs(diferencia))} ({porcentaje:.1f}%) - SOBREVALORADO",
                     new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_text_color(107, 114, 128)
            pdf.cell(0, 5, "Valor coincide con estimacion", new_x="LMARGIN", new_y="NEXT")

    output = pdf.output(dest="S")
    if isinstance(output, str):
        return output.encode("latin-1")
    return bytes(output)


def generate_team_report(team_name: str, players_df) -> bytes:
    """Genera informe PDF de equipo."""
    pdf = ScoutLabPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(27, 67, 50)
    pdf.cell(0, 10, f"Informe: {team_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Resumen
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(27, 67, 50)
    pdf.cell(0, 6, "Resumen de Plantilla", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(229, 231, 235)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    n = len(players_df)
    liga = players_df["liga"].mode().iloc[0] if "liga" in players_df.columns and len(players_df) > 0 else "-"
    resumen = [
        ("Liga", liga),
        ("Jugadores", str(n)),
        ("Edad media", "{:.1f}".format(players_df["edad"].mean())),
        ("Valor total", _format_euros(players_df["valor_mercado"].sum())),
        ("Total goles", str(int(players_df["goles"].sum()))),
        ("Total asistencias", str(int(players_df["asistencias"].sum()))),
    ]

    pdf.set_font("Helvetica", "", 8)
    for label, value in resumen:
        pdf.set_text_color(107, 114, 128)
        pdf.cell(40, 5, label, new_x="RIGHT")
        pdf.set_text_color(26, 26, 46)
        pdf.cell(0, 5, str(value), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Tabla
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(27, 67, 50)
    pdf.cell(0, 6, "Plantilla", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(229, 231, 235)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    col_widths = [50, 30, 15, 15, 15, 15, 15, 35]
    headers = ["Nombre", "Posicion", "Edad", "PJ", "Gol", "Ast", "TA", "Valor"]

    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(243, 244, 246)
    pdf.set_text_color(55, 65, 81)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 5, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(26, 26, 46)
    sorted_df = players_df.sort_values("valor_mercado", ascending=False)
    for _, row in sorted_df.head(30).iterrows():
        pdf.cell(col_widths[0], 4, str(row["nombre"])[:25], border=1)
        pdf.cell(col_widths[1], 4, str(row["posicion"])[:15], border=1)
        pdf.cell(col_widths[2], 4, str(int(row["edad"])), border=1, align="C")
        pdf.cell(col_widths[3], 4, str(int(row["partidos"])), border=1, align="C")
        pdf.cell(col_widths[4], 4, str(int(row["goles"])), border=1, align="C")
        pdf.cell(col_widths[5], 4, str(int(row["asistencias"])), border=1, align="C")
        pdf.cell(col_widths[6], 4, str(int(row["tarjetas_amarillas"])), border=1, align="C")
        pdf.cell(col_widths[7], 4, "{:,.0f}".format(row["valor_mercado"]), border=1, align="R")
        pdf.ln()

    output = pdf.output(dest="S")
    if isinstance(output, str):
        return output.encode("latin-1")
    return bytes(output)

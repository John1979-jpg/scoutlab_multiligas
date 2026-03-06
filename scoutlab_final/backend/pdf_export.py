"""
Modulo de exportacion a PDF con fpdf2.
Informes profesionales de 1 pagina A4 completa.
"""

import os
import tempfile
import requests
import numpy as np
from fpdf import FPDF


def _dl(url):
    url = str(url) if url else ""
    if not url or not url.startswith("http"):
        return ""
    url = url.replace("/tiny/", "/big/").replace("/small/", "/big/")
    if "wappen" in url or "verein" in url.lower():
        url = url.replace("/tiny/", "/normal/").replace("/small/", "/normal/")
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and len(r.content) > 200:
            ext = ".png" if "png" in url.lower() else ".jpg"
            tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except Exception:
        pass
    return ""


def _rm(p):
    if p:
        try:
            os.unlink(p)
        except Exception:
            pass


CC = {
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
    "republic of ireland": "ie", "northern ireland": "gb-nir", "korea, south": "kr",
}


def _flag(nat):
    if not nat:
        return ""
    code = CC.get(str(nat).lower().strip(), "")
    return _dl(f"https://flagcdn.com/w80/{code}.png") if code else ""


def _radar(pd):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        cats = ["Goles", "Asistencias", "Partidos", "Minutos", "Valor"]
        vals = [float(pd.get("goles", 0)), float(pd.get("asistencias", 0)),
                float(pd.get("partidos", 0)), float(pd.get("minutos", 0)),
                float(pd.get("valor_mercado", 0))]
        mx = [50, 30, 40, 3500, 200000000]
        norm = [min(v / m * 100, 100) if m > 0 else 0 for v, m in zip(vals, mx)]

        N = len(cats)
        ang = [n / float(N) * 2 * np.pi for n in range(N)]
        norm.append(norm[0])
        ang.append(ang[0])

        fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        # Anillos de fondo con colores progresivos
        rings = [(25, "#f0fdf4"), (50, "#dcfce7"), (75, "#bbf7d0"), (100, "#86efac")]
        for ring_val, ring_color in rings:
            ca = np.linspace(0, 2 * np.pi, 100)
            ax.fill(ca, [ring_val] * 100, color=ring_color, alpha=0.3)
        for ring_val in [25, 50, 75, 100]:
            ca = np.linspace(0, 2 * np.pi, 100)
            ax.plot(ca, [ring_val] * 100, color="#86efac", linewidth=0.3)

        # Lineas radiales
        for a in ang[:-1]:
            ax.plot([a, a], [0, 100], color="#d1d5db", linewidth=0.4)

        # Area principal con efecto de profundidad
        ax.fill(ang, norm, color="#047857", alpha=0.25, zorder=3)
        ax.fill(ang, [n * 0.5 for n in norm], color="#059669", alpha=0.15, zorder=3)
        ax.plot(ang, norm, color="#047857", linewidth=3, zorder=4)

        # Puntos con halo
        for i in range(N):
            ax.plot(ang[i], norm[i], "o", color="#047857", markersize=12,
                    zorder=5, alpha=0.3)
            ax.plot(ang[i], norm[i], "o", color="white", markersize=9,
                    zorder=6, markeredgecolor="#047857", markeredgewidth=2.5)
            # Valor real con caja
            vt = str(int(vals[i])) if vals[i] < 10000 else f"{vals[i]/1e6:.0f}M"
            ax.annotate(vt, xy=(ang[i], norm[i]),
                       xytext=(0, 16), textcoords="offset points",
                       ha="center", fontsize=11, fontweight="bold", color="#064e3b",
                       bbox=dict(boxstyle="round,pad=0.2", fc="white",
                                ec="#047857", alpha=0.95, lw=1))

        ax.set_xticks(ang[:-1])
        ax.set_xticklabels(cats, size=12, fontweight="bold", color="#1f2937")
        ax.set_yticks([])
        ax.set_ylim(0, 120)
        ax.spines["polar"].set_visible(False)
        ax.grid(False)

        ax.set_title("Perfil de Rendimiento", pad=20, fontsize=12,
                     fontweight="bold", color="#064e3b")

        plt.tight_layout(pad=0.5)
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        fig.savefig(tmp.name, dpi=200, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return tmp.name
    except Exception:
        return ""

# Variable necesaria para matplotlib
    # Variable de radar chart definida en funcion


class ScoutLabPDF(FPDF):
    def header(self):
        self.set_fill_color(27, 67, 50)
        self.rect(0, 0, 210, 9, "F")
        self.set_xy(10, 1)
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(255, 255, 255)
        self.cell(95, 6, "SCOUTLAB  |  INFORME DE SCOUTING", align="L")
        self.set_font("Helvetica", "", 7)
        self.cell(95, 6, "Analista: John Triguero", align="R")
        self.set_y(11)

    def footer(self):
        from datetime import datetime
        self.set_fill_color(27, 67, 50)
        self.rect(0, 288, 210, 9, "F")
        self.set_xy(10, 288.5)
        self.set_font("Helvetica", "", 6)
        self.set_text_color(255, 255, 255)
        f = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 6, f"Generado: {f}  |  Analista: John Triguero  |  ScoutLab", align="C")


def _fe(v):
    try:
        v = float(v)
        if v >= 1e6: return "{:.1f}M".format(v / 1e6)
        if v >= 1e3: return "{:.0f}K".format(v / 1e3)
        return "{:,.0f}".format(v)
    except:
        return "-"


def generate_player_report(player_data: dict) -> bytes:
    pdf = ScoutLabPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    pj = int(player_data.get("partidos", 0))
    g = int(player_data.get("goles", 0))
    a = int(player_data.get("asistencias", 0))
    mn = int(player_data.get("minutos", 0))
    g90 = player_data.get("goles_por_90", 0) or 0
    a90 = player_data.get("asistencias_por_90", 0) or 0
    ta = int(player_data.get("tarjetas_amarillas", 0))
    tr = int(player_data.get("tarjetas_rojas", 0))
    val = player_data.get("valor_mercado", 0) or 0
    nom = player_data.get("nombre", "-")
    eq = player_data.get("equipo", "-")
    li = player_data.get("liga", "-")
    nac = str(player_data.get("nacionalidad", "-"))

    y = pdf.get_y() + 3  # Bajar un poco la cabecera

    # ============================================
    # BLOQUE 1: Identidad (foto + nombre + escudo + bandera + valor)
    # Height: ~25mm
    # ============================================
    fp = _dl(player_data.get("foto_url", ""))
    ep = _dl(player_data.get("escudo_url", ""))
    # Bandera: primero intentar flag_url del CSV, luego flagcdn.com
    flp = ""
    flag_csv = str(player_data.get("flag_url", ""))
    if flag_csv.startswith("http"):
        flp = _dl(flag_csv)
    if not flp:
        flp = _flag(nac)

    if fp:
        try: pdf.image(fp, x=10, y=y, w=20, h=24)
        except: pass
        _rm(fp)

    xi = 34
    pdf.set_xy(xi, y)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(27, 67, 50)
    pdf.cell(75, 8, nom)

    pdf.set_xy(xi, y + 8)
    if ep:
        try:
            pdf.image(ep, x=xi, y=y + 9, w=6, h=6)
            pdf.set_x(xi + 8)
        except: pass
        _rm(ep)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(55, 65, 81)
    pdf.cell(75, 6, f"{eq}  |  {li}")

    pdf.set_xy(xi, y + 16)
    if flp:
        try:
            pdf.image(flp, x=xi, y=y + 16, h=7)
            pdf.set_x(xi + 14)
        except: pass
        _rm(flp)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(60, 7, nac)

    # Valor mercado arriba derecha
    pdf.set_xy(148, y)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(52, 4, "VALOR DE MERCADO", align="C")
    pdf.set_xy(148, y + 4)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(27, 67, 50)
    pdf.cell(52, 8, f"{_fe(val)} EUR", align="C")

    y += 26

    # Linea separadora
    pdf.set_draw_color(27, 67, 50)
    pdf.set_line_width(0.6)
    pdf.line(10, y, 200, y)
    y += 2

    # ============================================
    # BLOQUE 2: RADAR CHART GRANDE CENTRADO
    # Height: ~110mm (ocupa la zona central del folio)
    # ============================================
    rp = _radar(player_data)
    if rp:
        try:
            rw = 100
            rx = (210 - rw) / 2
            pdf.image(rp, x=rx, y=y, w=rw)
        except: pass
        _rm(rp)

    y += 100

    # ============================================
    # BLOQUE 3: Metric boxes (fila de cajas)
    # Height: ~16mm
    # ============================================
    pdf.set_draw_color(27, 67, 50)
    pdf.set_line_width(0.6)
    pdf.line(10, y, 200, y)
    y += 2

    bw = 23.5
    bh = 13
    gap = 0.3
    mets = [
        ("PJ", str(pj), (27,67,50)), ("Goles", str(g), (5,150,105)),
        ("Asist", str(a), (37,99,235)), ("Min", str(mn), (45,106,79)),
        ("G/90", f"{g90:.2f}", (124,58,237)), ("A/90", f"{a90:.2f}", (217,119,6)),
        ("TA", str(ta), (202,138,4)), ("TR", str(tr), (220,38,38)),
    ]
    for i, (lb, vl, co) in enumerate(mets):
        x = 10 + i * (bw + gap)
        pdf.set_fill_color(*co)
        pdf.rect(x, y, bw, bh, "F")
        pdf.set_xy(x, y + 1)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(bw, 6, vl, align="C")
        pdf.set_xy(x, y + 7.5)
        pdf.set_font("Helvetica", "", 5.5)
        pdf.set_text_color(220, 240, 230)
        pdf.cell(bw, 4, lb, align="C")

    y += bh + 2

    # ============================================
    # BLOQUE 4: Datos personales + Metricas + ML (3 columnas)
    # Height: ~55mm (hasta el footer)
    # ============================================
    pdf.set_draw_color(27, 67, 50)
    pdf.set_line_width(0.6)
    pdf.line(10, y, 200, y)
    y += 2

    # Col 1: Datos personales
    c1x = 10
    pdf.set_xy(c1x, y)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(27, 67, 50)
    pdf.cell(60, 5, "DATOS PERSONALES")
    yd = y + 6
    campos = [
        ("Posicion", player_data.get("posicion", "-")),
        ("Edad", str(player_data.get("edad", "-"))),
        ("Fecha nac.", str(player_data.get("fecha_nacimiento", "-"))),
        ("Pais", player_data.get("pais", "-")),
        ("Altura", f"{player_data.get('altura_cm', '-')} cm"),
        ("Pie", player_data.get("pie", "-")),
    ]
    for lb, vl in campos:
        pdf.set_xy(c1x, yd)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(20, 4.5, lb)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(40, 4.5, str(vl))
        yd += 4.5

    # Col 2: Metricas avanzadas
    c2x = 75
    pdf.set_xy(c2x, y)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(27, 67, 50)
    pdf.cell(60, 5, "METRICAS AVANZADAS")
    yd2 = y + 6
    part = g90 + a90
    mp = f"{mn/pj:.1f}" if pj > 0 else "-"
    avz = [
        ("Min/partido", mp),
        ("G+A por 90", f"{part:.2f}"),
        ("G+A total", str(g + a)),
        ("Rendimiento", f"{g+a}/{pj}" if pj > 0 else "-"),
        ("Contrib. gol", f"{(g+a)/pj*100:.0f}%" if pj > 0 else "-"),
        ("Min jugados", f"{mn/90:.1f} x90" if mn > 0 else "-"),
    ]
    for lb, vl in avz:
        pdf.set_xy(c2x, yd2)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(22, 4.5, lb)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(38, 4.5, str(vl))
        yd2 += 4.5

    # Col 3: Valoracion ML
    c3x = 140
    vp = player_data.get("valor_predicho", None)
    pdf.set_xy(c3x, y)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(27, 67, 50)
    pdf.cell(60, 5, "VALORACION ML")
    yd3 = y + 6

    if vp and float(vp) > 0:
        dif = float(vp) - float(val)
        pct = (dif / float(val) * 100) if float(val) > 0 else 0

        ml_items = [
            ("Valor real", f"{_fe(val)} EUR"),
            ("Estimado ML", f"{_fe(vp)} EUR"),
            ("Diferencia", f"{_fe(abs(dif))} EUR"),
            ("Porcentaje", f"{pct:+.1f}%"),
        ]
        for lb, vl in ml_items:
            pdf.set_xy(c3x, yd3)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(107, 114, 128)
            pdf.cell(22, 4.5, lb)
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(26, 26, 46)
            pdf.cell(38, 4.5, vl)
            yd3 += 4.5

        yd3 += 2
        if dif > 0:
            pdf.set_fill_color(220, 252, 231)
            cd = (22, 163, 74)
            tx = "INFRAVALORADO"
        elif dif < 0:
            pdf.set_fill_color(254, 226, 226)
            cd = (220, 38, 38)
            tx = "SOBREVALORADO"
        else:
            pdf.set_fill_color(243, 244, 246)
            cd = (107, 114, 128)
            tx = "VALOR JUSTO"

        pdf.rect(c3x, yd3, 60, 7, "F")
        pdf.set_xy(c3x, yd3 + 1)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*cd)
        pdf.cell(60, 5, tx, align="C")
    else:
        pdf.set_xy(c3x, yd3)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(60, 5, "Entrena el modelo ML")
        yd3 += 5
        pdf.set_xy(c3x, yd3)
        pdf.cell(60, 5, "para ver valoracion")

    output = pdf.output(dest="S")
    if isinstance(output, str):
        return output.encode("latin-1")
    return bytes(output)


def generate_team_report(team_name, players_df):
    pdf = ScoutLabPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(27, 67, 50)
    pdf.cell(0, 8, f"Informe: {team_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    n = len(players_df)
    li = players_df["liga"].mode().iloc[0] if "liga" in players_df.columns and n > 0 else "-"

    bw, bh = 31, 13
    mets = [
        ("Jugadores", str(n), (27,67,50)),
        ("Edad media", f"{players_df['edad'].mean():.1f}", (45,106,79)),
        ("Valor total", f"{_fe(players_df['valor_mercado'].sum())}", (5,150,105)),
        ("Goles", str(int(players_df["goles"].sum())), (37,99,235)),
        ("Asistencias", str(int(players_df["asistencias"].sum())), (124,58,237)),
        ("Liga", li, (107,114,128)),
    ]
    ym = pdf.get_y()
    for i, (lb, vl, co) in enumerate(mets):
        x = 10 + i * (bw + 1)
        pdf.set_fill_color(*co)
        pdf.rect(x, ym, bw, bh, "F")
        pdf.set_xy(x, ym + 1)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(bw, 6, vl, align="C")
        pdf.set_xy(x, ym + 7.5)
        pdf.set_font("Helvetica", "", 5.5)
        pdf.set_text_color(220, 240, 230)
        pdf.cell(bw, 4, lb, align="C")

    pdf.set_y(ym + bh + 4)

    cw = [50, 30, 15, 15, 15, 15, 15, 35]
    hd = ["Nombre", "Posicion", "Edad", "PJ", "Gol", "Ast", "TA", "Valor"]
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(27, 67, 50)
    pdf.set_text_color(255, 255, 255)
    for w, h in zip(cw, hd):
        pdf.cell(w, 6, h, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    sdf = players_df.sort_values("valor_mercado", ascending=False)
    for idx, (_, row) in enumerate(sdf.head(30).iterrows()):
        bg = (245, 247, 240) if idx % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(cw[0], 5, str(row["nombre"])[:25], fill=True)
        pdf.cell(cw[1], 5, str(row["posicion"])[:15], fill=True)
        pdf.cell(cw[2], 5, str(int(row["edad"])), fill=True, align="C")
        pdf.cell(cw[3], 5, str(int(row["partidos"])), fill=True, align="C")
        pdf.cell(cw[4], 5, str(int(row["goles"])), fill=True, align="C")
        pdf.cell(cw[5], 5, str(int(row["asistencias"])), fill=True, align="C")
        pdf.cell(cw[6], 5, str(int(row["tarjetas_amarillas"])), fill=True, align="C")
        pdf.cell(cw[7], 5, f"{_fe(row['valor_mercado'])}", fill=True, align="R")
        pdf.ln()

    output = pdf.output(dest="S")
    if isinstance(output, str):
        return output.encode("latin-1")
    return bytes(output)

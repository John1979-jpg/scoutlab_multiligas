"""
ScoutLab - Scraper Transfermarkt (equipo por equipo)

Flujo probado:
1. Liga /startseite/ -> extrae URLs de equipos (verein IDs)
2. Equipo /kader/verein/ID/plus/1 -> plantilla con valores de mercado + info basica
3. Equipo /leistungsdaten/verein/ID/plus/1 -> stats de rendimiento
4. Merge interno por nombre de jugador dentro del mismo equipo

Solo usa requests + BeautifulSoup. Sin Selenium.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
import os
from typing import Optional, List, Dict, Tuple
from unidecode import unidecode

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://www.transfermarkt.us/",
}

BASE = "https://www.transfermarkt.us"

LEAGUES = {
    "Premier League": {"code": "GB1", "slug": "premier-league", "country": "Inglaterra"},
    "LaLiga": {"code": "ES1", "slug": "laliga", "country": "Espana"},
    "Bundesliga": {"code": "L1", "slug": "bundesliga", "country": "Alemania"},
    "Serie A": {"code": "IT1", "slug": "serie-a", "country": "Italia"},
    "Ligue 1": {"code": "FR1", "slug": "ligue-1", "country": "Francia"},
    "Eredivisie": {"code": "NL1", "slug": "eredivisie", "country": "Paises Bajos"},
    "Liga Portugal": {"code": "PO1", "slug": "liga-portugal", "country": "Portugal"},
    "Super Lig": {"code": "TR1", "slug": "super-lig", "country": "Turquia"},
    "Championship": {"code": "GB2", "slug": "championship", "country": "Inglaterra"},
    "LaLiga2": {"code": "ES2", "slug": "laliga2", "country": "Espana"},
    "Serie B": {"code": "IT2", "slug": "serie-b", "country": "Italia"},
    "2. Bundesliga": {"code": "L2", "slug": "2-bundesliga", "country": "Alemania"},
    "Ligue 2": {"code": "FR2", "slug": "ligue-2", "country": "Francia"},
    "Jupiler Pro League": {"code": "BE1", "slug": "jupiler-pro-league", "country": "Belgica"},
    "Scottish Premiership": {"code": "SC1", "slug": "scottish-premiership", "country": "Escocia"},
    "Super League Suiza": {"code": "C1", "slug": "super-league", "country": "Suiza"},
    "Bundesliga Austria": {"code": "A1", "slug": "bundesliga", "country": "Austria"},
    "MLS": {"code": "MLS1", "slug": "major-league-soccer", "country": "EEUU"},
}

# Traduccion de posiciones
POS_MAP = {
    "goalkeeper": "Portero", "keeper": "Portero",
    "centre-back": "Defensa Central", "center back": "Defensa Central",
    "left-back": "Lateral Izquierdo", "right-back": "Lateral Derecho",
    "defensive midfield": "Mediocentro Defensivo",
    "central midfield": "Mediocentro",
    "attacking midfield": "Mediapunta",
    "left midfield": "Centrocampista Izquierdo",
    "right midfield": "Centrocampista Derecho",
    "left winger": "Extremo Izquierdo", "right winger": "Extremo Derecho",
    "centre-forward": "Delantero Centro", "center forward": "Delantero Centro",
    "second striker": "Mediapunta",
}


def _session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def _wait(lo=2, hi=4):
    time.sleep(random.uniform(lo, hi))


def _parse_value(txt: str) -> Optional[int]:
    """'€1.50m' -> 1500000, '€500k' -> 500000"""
    if not txt or txt.strip() in ("-", ""):
        return None
    txt = txt.replace("€", "").replace("\xa0", "").replace(" ", "")
    m = re.search(r"([\d.,]+)\s*([mkMK])?", txt)
    if not m:
        return None
    num_s = m.group(1).replace(",", ".")
    # "1.50" es 1.5 pero "1.500" es 1500
    parts = num_s.split(".")
    if len(parts) == 2 and len(parts[1]) == 3:
        num_s = parts[0] + parts[1]  # "1.500" -> "1500"
    num = float(num_s)
    suf = (m.group(2) or "").lower()
    if suf == "m":
        num *= 1_000_000
    elif suf == "k":
        num *= 1_000
    return int(num)


def _translate_pos(pos: str) -> str:
    if not pos:
        return ""
    pl = pos.lower().strip()
    for en, es in POS_MAP.items():
        if en in pl:
            return es
    return pos


def _norm(name: str) -> str:
    return unidecode(str(name).lower().strip()) if name else ""


# ============================================================
# PASO 1: Obtener equipos de una liga
# ============================================================

def get_teams(league_name: str, session=None) -> List[Dict]:
    """
    Obtiene lista de equipos con su verein_id y slug desde la pagina de liga.
    Retorna: [{"name": "...", "slug": "...", "verein_id": "..."}]
    """
    if league_name not in LEAGUES:
        return []

    cfg = LEAGUES[league_name]
    url = f"{BASE}/{cfg['slug']}/startseite/wettbewerb/{cfg['code']}"

    if session is None:
        session = _session()

    try:
        r = session.get(url, timeout=30)
        if r.status_code != 200:
            print(f"    [ERROR] HTTP {r.status_code} al obtener equipos")
            return []

        soup = BeautifulSoup(r.content, "lxml")
        teams = []
        seen = set()

        # Buscar links a equipos: /SLUG/startseite/verein/ID o /SLUG/kader/verein/ID
        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = re.search(r"/([^/]+)/(?:startseite|kader)/verein/(\d+)", href)
            if m:
                slug = m.group(1)
                vid = m.group(2)
                if vid not in seen:
                    seen.add(vid)
                    name = a.get("title", "") or a.get_text(strip=True) or slug.replace("-", " ").title()
                    # Buscar escudo del equipo (imagen cercana al link)
                    logo_url = ""
                    parent = a.find_parent("td")
                    if parent:
                        img = parent.find("img")
                        if img:
                            logo_url = img.get("src", "") or img.get("data-src", "")
                    teams.append({"name": name, "slug": slug, "verein_id": vid, "logo_url": logo_url})

        return teams

    except Exception as e:
        print(f"    [ERROR] {e}")
        return []


# ============================================================
# PASO 2: Scrape plantilla de un equipo (valores de mercado)
# ============================================================

def scrape_team_values(slug: str, verein_id: str, session=None) -> pd.DataFrame:
    """
    Scrapea /SLUG/kader/verein/ID/plus/1
    Retorna: nombre, posicion, edad, nacionalidad, valor_mercado, pie, altura
    """
    url = f"{BASE}/{slug}/kader/verein/{verein_id}/plus/1"

    if session is None:
        session = _session()

    players = []
    try:
        r = session.get(url, timeout=30)
        if r.status_code != 200:
            return pd.DataFrame()

        soup = BeautifulSoup(r.content, "lxml")
        table = soup.find("table", {"class": "items"})
        if not table:
            return pd.DataFrame()

        rows = table.find_all("tr", {"class": ["odd", "even"]})
        for row in rows:
            try:
                # Nombre
                inline = row.find("table", {"class": "inline-table"})
                if not inline:
                    continue
                name_td = inline.find("td", {"class": "hauptlink"})
                if not name_td:
                    continue
                name_a = name_td.find("a")
                nombre = name_a.get_text(strip=True) if name_a else ""
                if not nombre:
                    continue

                # Posicion (segunda fila del inline-table)
                pos_rows = inline.find_all("tr")
                posicion = pos_rows[-1].get_text(strip=True) if len(pos_rows) > 1 else ""
                posicion = _translate_pos(posicion)

                # Nacionalidad + bandera URL
                flag = row.find("img", {"class": "flaggenrahmen"})
                nac = flag.get("title", "") if flag else ""
                flag_url = flag.get("src", "") if flag else ""

                # Foto del jugador (imagen en bilderrahmen o inline-table img)
                foto_url = ""
                img_player = row.find("img", {"class": "bilderrahmen-fixed"})
                if not img_player:
                    img_player = row.find("img", {"data-src": re.compile(r"img\.a\.transfermarkt")})
                if not img_player:
                    # Buscar cualquier img dentro del inline-table que no sea bandera
                    for img_candidate in row.find_all("img"):
                        src = img_candidate.get("data-src", "") or img_candidate.get("src", "")
                        cls = " ".join(img_candidate.get("class", []))
                        if "flaggenrahmen" not in cls and ("header" in src or "portrait" in src or "player" in src.lower()):
                            img_player = img_candidate
                            break
                if img_player:
                    foto_url = img_player.get("data-src", "") or img_player.get("src", "")

                # Edad, pie, altura desde celdas zentriert
                zc = row.find_all("td", {"class": "zentriert"})
                edad = 0
                fecha_nac = ""
                pie = ""
                altura = 0
                for cell in zc:
                    txt = cell.get_text(strip=True)
                    # Fecha nacimiento tipo "Jan 1, 2000 (25)"
                    if re.search(r"\(\d+\)", txt):
                        m_age = re.search(r"\((\d+)\)", txt)
                        if m_age:
                            edad = int(m_age.group(1))
                        fecha_nac = re.sub(r"\s*\(\d+\)", "", txt).strip()
                    # Altura tipo "1,85 m"
                    elif "m" in txt and "," in txt:
                        try:
                            altura = int(float(txt.replace("m", "").replace(",", ".").strip()) * 100)
                        except:
                            pass
                    # Pie
                    elif txt.lower() in ("right", "left", "both", "derecho", "izquierdo", "ambidiestro"):
                        pie_map = {"right": "Derecho", "left": "Izquierdo", "both": "Ambidiestro",
                                   "derecho": "Derecho", "izquierdo": "Izquierdo", "ambidiestro": "Ambidiestro"}
                        pie = pie_map.get(txt.lower(), txt)

                # Valor de mercado (celda rechts hauptlink)
                val_td = row.find("td", {"class": "rechts hauptlink"})
                valor = _parse_value(val_td.get_text(strip=True)) if val_td else None

                players.append({
                    "nombre": nombre,
                    "posicion": posicion,
                    "edad": edad,
                    "nacionalidad": nac,
                    "fecha_nacimiento": fecha_nac,
                    "pie": pie or "Derecho",
                    "altura_cm": altura or 180,
                    "valor_mercado": valor,
                    "foto_url": foto_url,
                    "flag_url": flag_url,
                })

            except Exception:
                continue

    except Exception:
        pass

    return pd.DataFrame(players)


# ============================================================
# PASO 3: Scrape stats de rendimiento de un equipo
# ============================================================

def scrape_team_stats(slug: str, verein_id: str, session=None) -> pd.DataFrame:
    """
    Scrapea /SLUG/leistungsdaten/verein/ID/plus/1
    Estructura real de columnas (18 celdas por fila):
      Col 5: Edad | Col 7: Convocatorias | Col 8: Partidos
      Col 9: Goles | Col 10: Asistencias | Col 11: Tarj. amarillas
      Col 12: Segunda amarilla | Col 13: Tarj. rojas | Col 17: Minutos
    """
    url = f"{BASE}/{slug}/leistungsdaten/verein/{verein_id}/plus/1"

    if session is None:
        session = _session()

    players = []
    try:
        r = session.get(url, timeout=30)
        if r.status_code != 200:
            url2 = f"{BASE}/{slug}/leistungsdaten/verein/{verein_id}"
            r = session.get(url2, timeout=30)
            if r.status_code != 200:
                return pd.DataFrame()

        soup = BeautifulSoup(r.content, "lxml")
        table = soup.find("table", {"class": "items"})
        if not table:
            return pd.DataFrame()

        rows = table.find_all("tr", {"class": ["odd", "even"]})
        for row in rows:
            try:
                cells = row.find_all("td")
                if len(cells) < 15:
                    continue

                # Nombre del jugador
                nombre = ""
                # Metodo 1: hauptlink td > a
                hl_td = row.find("td", {"class": "hauptlink"})
                if hl_td:
                    hl_a = hl_td.find("a")
                    if hl_a:
                        nombre = hl_a.get_text(strip=True)
                # Metodo 2: link con /spieler/ en href
                if not nombre:
                    for a_tag in row.find_all("a", href=True):
                        if "/spieler/" in a_tag["href"] or "/profil/spieler/" in a_tag["href"]:
                            txt = a_tag.get_text(strip=True)
                            if txt and len(txt) > 2:
                                nombre = txt
                                break
                if not nombre:
                    continue

                def _cell_int(idx):
                    """Extrae entero de una celda por indice."""
                    if idx >= len(cells):
                        return 0
                    txt = cells[idx].get_text(strip=True)
                    txt = txt.replace(".", "").replace("'", "").replace(",", "").strip()
                    if txt in ("-", "", "Not used during this season"):
                        return 0
                    try:
                        return int(txt)
                    except ValueError:
                        return 0

                def _cell_minutes():
                    """Extrae minutos de la ultima celda (rechts)."""
                    last = cells[-1]
                    txt = last.get_text(strip=True)
                    txt = txt.replace(".", "").replace("'", "").replace(",", "").strip()
                    if txt in ("-", ""):
                        return 0
                    try:
                        return int(txt)
                    except ValueError:
                        return 0

                partidos = _cell_int(8)
                goles = _cell_int(9)
                asistencias = _cell_int(10)
                tarj_am = _cell_int(11)
                tarj_roja = _cell_int(13)
                minutos = _cell_minutes()

                players.append({
                    "nombre": nombre,
                    "partidos": partidos,
                    "goles": goles,
                    "asistencias": asistencias,
                    "tarjetas_amarillas": tarj_am,
                    "tarjetas_rojas": tarj_roja,
                    "minutos": minutos,
                })

            except Exception:
                continue

    except Exception:
        pass

    return pd.DataFrame(players)


# ============================================================
# PASO 4: Scrape completo de un equipo (merge values + stats)
# ============================================================

def scrape_team(slug: str, verein_id: str, team_name: str,
                league: str, country: str, logo_url: str = "", session=None) -> pd.DataFrame:
    """Scrapea un equipo completo: valores + stats, merge por nombre."""
    if session is None:
        session = _session()

    # Valores de mercado + info basica
    df_val = scrape_team_values(slug, verein_id, session)
    _wait(1, 2)

    # Stats de rendimiento
    df_stats = scrape_team_stats(slug, verein_id, session)

    if df_val.empty and df_stats.empty:
        return pd.DataFrame()

    # Si solo tenemos valores
    if df_stats.empty:
        df_val["equipo"] = team_name
        df_val["liga"] = league
        df_val["pais"] = country
        df_val["escudo_url"] = logo_url
        df_val["partidos"] = 0
        df_val["goles"] = 0
        df_val["asistencias"] = 0
        df_val["tarjetas_amarillas"] = 0
        df_val["tarjetas_rojas"] = 0
        df_val["minutos"] = 0
        return df_val

    # Si solo tenemos stats
    if df_val.empty:
        df_stats["equipo"] = team_name
        df_stats["liga"] = league
        df_stats["pais"] = country
        df_stats["escudo_url"] = logo_url
        df_stats["valor_mercado"] = None
        return df_stats

    # Merge por nombre normalizado
    df_val["_n"] = df_val["nombre"].apply(_norm)
    df_stats["_n"] = df_stats["nombre"].apply(_norm)

    merged = df_val.merge(df_stats[["_n", "partidos", "goles", "asistencias",
                                     "tarjetas_amarillas", "tarjetas_rojas", "minutos"]],
                          on="_n", how="left")
    merged = merged.drop(columns=["_n"])

    # Rellenar NaN en stats
    for col in ["partidos", "goles", "asistencias", "tarjetas_amarillas", "tarjetas_rojas", "minutos"]:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0).astype(int)

    merged["equipo"] = team_name
    merged["liga"] = league
    merged["pais"] = country
    merged["escudo_url"] = logo_url

    return merged


# ============================================================
# PASO 5: Scrape completo de todas las ligas
# ============================================================

def scrape_all(
    leagues: List[str] = None,
    output_path: str = None,
    max_teams: int = 50,
) -> pd.DataFrame:
    """
    Pipeline completo: para cada liga, obtiene equipos y scrapea uno a uno.
    """
    if leagues is None:
        leagues = list(LEAGUES.keys())

    print("=" * 60)
    print("TRANSFERMARKT - SCRAPING EQUIPO POR EQUIPO")
    print(f"Ligas: {len(leagues)}")
    print("=" * 60)

    session = _session()
    all_data = []
    total_players = 0

    for league_name in leagues:
        if league_name not in LEAGUES:
            print(f"\n  [SKIP] {league_name} no configurada")
            continue

        cfg = LEAGUES[league_name]
        print(f"\n{'='*60}")
        print(f"  {league_name} ({cfg['country']})")
        print(f"{'='*60}")

        # Obtener equipos
        teams = get_teams(league_name, session)
        _wait(1, 2)

        if not teams:
            print(f"  No se encontraron equipos")
            continue

        teams = teams[:max_teams]
        print(f"  {len(teams)} equipos encontrados")

        for i, team in enumerate(teams):
            name = team["name"]
            slug = team["slug"]
            vid = team["verein_id"]
            print(f"  [{i+1}/{len(teams)}] {name}...", end=" ", flush=True)

            df_team = scrape_team(slug, vid, name, league_name, cfg["country"],
                                  team.get("logo_url", ""), session)

            if not df_team.empty:
                all_data.append(df_team)
                total_players += len(df_team)
                stats_count = (df_team["partidos"] > 0).sum() if "partidos" in df_team.columns else 0
                val_count = df_team["valor_mercado"].notna().sum() if "valor_mercado" in df_team.columns else 0
                print(f"{len(df_team)} jug ({stats_count} con stats, {val_count} con valor)")
            else:
                print("sin datos")

            _wait(2, 4)

    if not all_data:
        print("\n[ERROR] No se obtuvieron datos de ninguna liga")
        return pd.DataFrame()

    # Concatenar todo
    result = pd.concat(all_data, ignore_index=True)

    # Calcular metricas derivadas
    result["participaciones_gol"] = result["goles"].fillna(0).astype(int) + result["asistencias"].fillna(0).astype(int)
    result["goles_por_90"] = result.apply(
        lambda r: round(r["goles"] / (r["minutos"] / 90), 2) if r["minutos"] > 0 else 0.0, axis=1
    )
    result["asistencias_por_90"] = result.apply(
        lambda r: round(r["asistencias"] / (r["minutos"] / 90), 2) if r["minutos"] > 0 else 0.0, axis=1
    )

    # Campos faltantes
    result["temporada"] = "2025/26"
    result["grupo"] = ""
    result["rating"] = 0.0
    result["id"] = range(1, len(result) + 1)

    for col in ["pie", "altura_cm", "fecha_nacimiento", "posicion", "nacionalidad",
                "foto_url", "flag_url", "escudo_url"]:
        if col not in result.columns:
            result[col] = "" if col != "altura_cm" else 180

    # Eliminar duplicados
    result = result.drop_duplicates(subset=["nombre", "equipo", "liga"], keep="first")

    # Resumen
    with_stats = (result["partidos"] > 0).sum()
    with_value = result["valor_mercado"].notna().sum()

    print(f"\n{'='*60}")
    print(f"RESULTADO FINAL")
    print(f"  Jugadores totales:    {len(result)}")
    print(f"  Con stats rendimiento: {with_stats} ({with_stats/len(result)*100:.1f}%)")
    print(f"  Con valor de mercado:  {with_value} ({with_value/len(result)*100:.1f}%)")
    print(f"  Ligas:                {result['liga'].nunique()}")
    print(f"{'='*60}")
    print(result["liga"].value_counts().to_string())

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result.to_csv(output_path, index=False, encoding="utf-8")
        print(f"\nGuardado: {output_path}")

    return result


# Aliases para compatibilidad con app.py
TRANSFERMARKT_LEAGUES = LEAGUES

def scrape_all_leagues(leagues=None, output_path=None, **kw):
    return scrape_all(leagues=leagues, output_path=output_path)

def get_available_leagues():
    return LEAGUES.copy()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ligas", nargs="+", default=None, help="Ligas a scrapear")
    parser.add_argument("--top5", action="store_true", help="Solo top 5 ligas europeas")
    args = parser.parse_args()

    if args.top5:
        ligas = ["Premier League", "LaLiga", "Bundesliga", "Serie A", "Ligue 1"]
    else:
        ligas = args.ligas

    output = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "processed", "jugadores.csv",
    )
    df = scrape_all(leagues=ligas, output_path=output)
    if not df.empty:
        print(f"\nCompletado: {len(df)} jugadores reales")

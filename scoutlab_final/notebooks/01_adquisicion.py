"""
01 - Adquisicion de Datos
=========================
Script de web scraping para obtener datos de jugadores de las principales
ligas europeas desde Transfermarkt (valores de mercado y estadisticas).

Fuentes:
- Transfermarkt: https://www.transfermarkt.es

Ligas incluidas:
- Premier League, LaLiga, Serie A, Bundesliga, Ligue 1,
  Eredivisie, Super Lig, Liga Portugal

NOTA: Respetar los terminos de uso del sitio web.
Usar delays entre peticiones para no sobrecargar los servidores.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import json

# Configuracion
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}
DELAY = 3  # segundos entre peticiones
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

# Ligas europeas con sus IDs de Transfermarkt
LEAGUES = {
    "Premier League": {"country": "Inglaterra", "id": "GB1"},
    "LaLiga": {"country": "Espana", "id": "ES1"},
    "Serie A": {"country": "Italia", "id": "IT1"},
    "Bundesliga": {"country": "Alemania", "id": "L1"},
    "Ligue 1": {"country": "Francia", "id": "FR1"},
    "Eredivisie": {"country": "Paises Bajos", "id": "NL1"},
    "Super Lig": {"country": "Turquia", "id": "TR1"},
    "Liga Portugal": {"country": "Portugal", "id": "PO1"},
}


def scrape_transfermarkt_team(team_url: str) -> list:
    """
    Extrae los datos basicos y valores de mercado de una plantilla
    desde Transfermarkt.
    """
    try:
        response = requests.get(team_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Error al acceder a " + team_url + ": " + str(e))
        return []

    soup = BeautifulSoup(response.text, "lxml")
    players = []

    # Buscar la tabla de jugadores
    table = soup.find("table", class_="items")
    if not table:
        print("No se encontro tabla de jugadores en: " + team_url)
        return []

    rows = table.find_all("tr", class_=["odd", "even"])
    for row in rows:
        try:
            # Nombre
            name_cell = row.find("td", class_="hauptlink")
            if not name_cell:
                continue
            name_link = name_cell.find("a")
            nombre = name_link.text.strip() if name_link else ""

            # Posicion
            pos_cells = row.find_all("td")
            posicion = ""
            for td in pos_cells:
                if td.text.strip() in [
                    "Portero", "Defensa central", "Lateral derecho",
                    "Lateral izquierdo", "Pivote", "Mediocentro",
                    "Mediapunta", "Extremo derecho", "Extremo izquierdo",
                    "Delantero centro",
                ]:
                    posicion = td.text.strip()
                    break

            # Edad y nacionalidad
            edad = ""
            nacionalidad = ""
            for td in pos_cells:
                text = td.text.strip()
                if text.isdigit() and 15 <= int(text) <= 45:
                    edad = int(text)
                    break

            flag = row.find("img", class_="flaggenrahmen")
            if flag:
                nacionalidad = flag.get("title", "")

            # Valor de mercado
            valor_cell = row.find("td", class_="rechts hauptlink")
            valor_mercado = 0
            if valor_cell:
                valor_text = valor_cell.text.strip()
                valor_mercado = _parse_market_value(valor_text)

            players.append({
                "nombre": nombre,
                "posicion": posicion,
                "edad": edad,
                "nacionalidad": nacionalidad,
                "valor_mercado": valor_mercado,
            })

        except Exception as e:
            print("Error procesando fila: " + str(e))
            continue

    return players


def scrape_team_stats(team_url: str) -> list:
    """
    Extrae las estadisticas de rendimiento (partidos, goles, asistencias,
    tarjetas, minutos) de una plantilla desde Transfermarkt.

    URL: /leistungsdaten/verein/ID/plus/1
    Columnas: Col 8=partidos, Col 9=goles, Col 10=asistencias,
              Col 11=tarjetas amarillas, Col 13=tarjetas rojas, Col 17=minutos
    """
    try:
        response = requests.get(team_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Error al acceder a stats: " + str(e))
        return []

    soup = BeautifulSoup(response.text, "lxml")
    stats = []

    table = soup.find("table", class_="items")
    if not table:
        return []

    rows = table.find_all("tr", class_=["odd", "even"])
    for row in rows:
        try:
            cells = row.find_all("td")
            name_cell = row.find("td", class_="hauptlink")
            if not name_cell:
                continue

            nombre = name_cell.find("a").text.strip()

            stats.append({
                "nombre": nombre,
                "partidos": _safe_int(cells, 8),
                "goles": _safe_int(cells, 9),
                "asistencias": _safe_int(cells, 10),
                "tarjetas_amarillas": _safe_int(cells, 11),
                "tarjetas_rojas": _safe_int(cells, 13),
                "minutos": _parse_minutes(cells, 17),
            })
        except Exception:
            continue

    return stats


def _safe_int(cells, idx):
    """Extrae un entero de una celda de forma segura."""
    try:
        return int(cells[idx].text.strip().replace("-", "0"))
    except (IndexError, ValueError):
        return 0


def _parse_minutes(cells, idx):
    """Parsea minutos jugados (formato: 1.234')."""
    try:
        text = cells[idx].text.strip().replace(".", "").replace("'", "")
        return int(text) if text and text != "-" else 0
    except (IndexError, ValueError):
        return 0


def _parse_market_value(text: str) -> int:
    """Convierte texto de valor de mercado a entero."""
    text = text.replace("\xa0", "").strip()
    if not text or text == "-":
        return 0
    try:
        text = text.replace(".", "").replace(",", ".")
        if "mill" in text.lower():
            num = float(text.lower().replace("mill.", "").replace("\xe2\x82\xac", "").strip())
            return int(num * 1_000_000)
        elif "mil" in text.lower():
            num = float(text.lower().replace("mil", "").replace("\xe2\x82\xac", "").strip())
            return int(num * 1_000)
        else:
            return int(float(text.replace("\xe2\x82\xac", "").strip()))
    except (ValueError, AttributeError):
        return 0


def run_full_scraping():
    """
    Ejecuta el scraping completo de todas las ligas europeas desde Transfermarkt.
    Para cada equipo se scrapean los valores de mercado (/kader/verein/ID/plus/1)
    y las estadisticas de rendimiento (/leistungsdaten/verein/ID/plus/1).
    Guarda los datos crudos en data/raw/.
    """
    os.makedirs(RAW_DIR, exist_ok=True)

    all_players = []

    for liga_name, liga_info in LEAGUES.items():
        print("\n" + "=" * 50)
        print("Scraping " + liga_name + " (" + liga_info["country"] + ")...")
        print("=" * 50)

        base_url = "https://www.transfermarkt.es"
        liga_url = base_url + "/x/startseite/wettbewerb/" + liga_info["id"]

        try:
            response = requests.get(liga_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(response.text, "lxml")
            team_links = soup.select("td.hauptlink a[href*='/verein/']")

            for link in team_links:
                team_name = link.text.strip()
                team_href = link.get("href", "")
                if not team_href or not team_name:
                    continue

                team_id = team_href.split("/verein/")[1].split("/")[0] if "/verein/" in team_href else ""
                if not team_id:
                    continue

                # URL de valores de mercado
                values_url = base_url + "/x/kader/verein/" + team_id + "/plus/1"
                # URL de estadisticas
                stats_url = base_url + "/x/leistungsdaten/verein/" + team_id + "/plus/1"

                print("  " + team_name + "...")

                # Scrape valores
                players = scrape_transfermarkt_team(values_url)
                # Scrape stats
                player_stats = scrape_team_stats(stats_url)

                # Merge por nombre
                stats_dict = {s["nombre"]: s for s in player_stats}
                for p in players:
                    p["equipo"] = team_name
                    p["liga"] = liga_name
                    p["pais"] = liga_info["country"]
                    if p["nombre"] in stats_dict:
                        p.update(stats_dict[p["nombre"]])

                all_players.extend(players)
                time.sleep(DELAY)

        except Exception as e:
            print("Error scraping " + liga_name + ": " + str(e))
            continue

    if all_players:
        df = pd.DataFrame(all_players)
        output_path = os.path.join(RAW_DIR, "transfermarkt_raw.csv")
        df.to_csv(output_path, index=False)
        print("\nGuardados " + str(len(df)) + " jugadores en " + output_path)
    else:
        print("\nNo se obtuvieron datos de Transfermarkt")


if __name__ == "__main__":
    run_full_scraping()

"""
01 - Adquisicion de Datos
=========================
Script de web scraping para obtener datos de jugadores de 1a RFEF
desde Transfermarkt (valores de mercado) y BeSoccer (estadisticas).

Fuentes:
- Transfermarkt: https://www.transfermarkt.es
- BeSoccer: https://es.besoccer.com

NOTA: Respetar los terminos de uso de cada sitio web.
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


def scrape_besoccer_stats(competition_url: str) -> list:
    """
    Extrae estadisticas de jugadores desde BeSoccer.
    """
    try:
        response = requests.get(competition_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Error al acceder a BeSoccer: " + str(e))
        return []

    soup = BeautifulSoup(response.text, "lxml")
    stats = []

    # La estructura de BeSoccer varia, este es un esquema base
    # que debe adaptarse segun la estructura actual del sitio
    ranking_tables = soup.find_all("table")
    for table in ranking_tables:
        rows = table.find_all("tr")
        for row in rows[1:]:  # Saltar cabecera
            cells = row.find_all("td")
            if len(cells) >= 4:
                try:
                    nombre = cells[1].text.strip()
                    equipo = cells[2].text.strip() if len(cells) > 2 else ""
                    valor = cells[3].text.strip() if len(cells) > 3 else "0"
                    stats.append({
                        "nombre": nombre,
                        "equipo": equipo,
                        "valor": valor,
                    })
                except Exception:
                    continue

    return stats


def run_full_scraping():
    """
    Ejecuta el scraping completo de todas las fuentes.
    Guarda los datos crudos en data/raw/.
    """
    os.makedirs(RAW_DIR, exist_ok=True)

    # URLs de equipos de 1a RFEF en Transfermarkt
    # Estos son ejemplos - hay que completar con todos los equipos
    TEAM_URLS = {
        "Racing Ferrol": "https://www.transfermarkt.es/racing-club-de-ferrol/kader/verein/1176",
        "SD Ponferradina": "https://www.transfermarkt.es/sd-ponferradina/kader/verein/3160",
        "Hercules CF": "https://www.transfermarkt.es/hercules-cf/kader/verein/2286",
        # Agregar el resto de equipos aqui
    }

    all_players = []
    for team_name, url in TEAM_URLS.items():
        print("Scraping " + team_name + "...")
        players = scrape_transfermarkt_team(url)
        for p in players:
            p["equipo"] = team_name
        all_players.extend(players)
        time.sleep(DELAY)

    if all_players:
        df = pd.DataFrame(all_players)
        output_path = os.path.join(RAW_DIR, "transfermarkt_raw.csv")
        df.to_csv(output_path, index=False)
        print("Guardados " + str(len(df)) + " jugadores en " + output_path)
    else:
        print("No se obtuvieron datos de Transfermarkt")

    # BeSoccer rankings
    BESOCCER_URLS = {
        "goleadores": "https://es.besoccer.com/competicion/rankings/primera_division_rfef/2025",
    }

    for stat_type, url in BESOCCER_URLS.items():
        print("Scraping BeSoccer " + stat_type + "...")
        stats = scrape_besoccer_stats(url)
        if stats:
            df_stats = pd.DataFrame(stats)
            output_path = os.path.join(RAW_DIR, "besoccer_" + stat_type + ".csv")
            df_stats.to_csv(output_path, index=False)
            print("Guardados " + str(len(df_stats)) + " registros")
        time.sleep(DELAY)


if __name__ == "__main__":
    run_full_scraping()

"""
ScoutLab - Módulo de importación de datos
Permite importar datos desde CSV, HTML de WhoScored o actualizar desde Transfermarkt
"""

import streamlit as st
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
import time
import random
import re
from typing import Optional, List
from io import StringIO


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def get_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def parse_market_value(value_str: str) -> Optional[int]:
    """Convierte string de valor de mercado a número."""
    if not value_str or value_str == "-":
        return None
    
    value_str = value_str.replace("€", "").replace(" ", "").replace("\xa0", "")
    
    multipliers = {"m": 1_000_000, "k": 1_000}
    
    match = re.search(r"([\d.,]+)\s*([mk])?", value_str, re.IGNORECASE)
    if match:
        num = float(match.group(1).replace(",", "."))
        suffix = match.group(2)
        if suffix:
            num *= multipliers.get(suffix.lower(), 1)
        return int(num)
    
    try:
        return int(float(value_str.replace(",", "")))
    except:
        return None


def scrape_transfermarkt_players_from_league(league_url: str, max_teams: int = 5) -> pd.DataFrame:
    """Scrapea jugadores de equipos de una liga."""
    all_players = []
    
    try:
        session = get_session()
        
        # Obtener equipos
        resp = session.get(league_url, timeout=30)
        if resp.status_code != 200:
            return pd.DataFrame()
        
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Buscar enlaces de equipos
        team_urls = set()
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "/verein/" in href and "startseite" in href:
                full_url = "https://www.transfermarkt.us" + href
                team_urls.add(full_url)
        
        team_urls = list(team_urls)[:max_teams]
        
        for i, team_url in enumerate(team_urls):
            print(f"Scraping equipo {i+1}/{len(team_urls)}")
            
            resp = session.get(team_url, timeout=30)
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.content, "html.parser")
            table = soup.find("table", {"class": "items"})
            
            if not table:
                continue
            
            # Obtener nombre del equipo
            team_name = soup.find("h1")
            team_name = team_name.get_text(strip=True) if team_name else "Unknown"
            
            rows = table.find_all("tr", {"class": ["odd", "even"]})
            
            for row in rows:
                try:
                    name_col = row.find("td", {"class": "hauptlink"})
                    value_col = row.find("td", {"class": "rechts"})
                    
                    if not name_col or not value_col:
                        continue
                    
                    name_tag = name_col.find("a")
                    name = name_tag.get_text(strip=True) if name_tag else ""
                    
                    if not name or "Total" in name:
                        continue
                    
                    value_text = value_col.get_text(strip=True)
                    value = parse_market_value(value_text)
                    
                    # Posición
                    pos_col = row.find("td", {"class": "pos_leiste"})
                    posicion = pos_col.get_text(strip=True) if pos_col else ""
                    
                    # Nacionalidad
                    nation = row.find("td", {"class": "zentriert"})
                    pais = nation.get_text(strip=True) if nation else ""
                    
                    # Edad
                    age = row.find("td", {"class": re.compile(".*alter.*")})
                    edad = age.get_text(strip=True) if age else ""
                    
                    all_players.append({
                        "nombre": name,
                        "equipo": team_name,
                        "posicion": posicion,
                        "edad": edad,
                        "nacionalidad": pais,
                        "valor_mercado": value,
                    })
                    
                except Exception:
                    continue
            
            time.sleep(random.uniform(2, 4))
    
    except Exception as e:
        print(f"Error: {e}")
    
    return pd.DataFrame(all_players)


def scrape_all_leagues_full() -> pd.DataFrame:
    """Scrapea La Liga y Segunda División."""
    leagues = [
        ("La Liga", "https://www.transfermarkt.us/laliga/startseite/Wettbewerb/ES1"),
        ("Segunda División", "https://www.transfermarkt.us/segunda-division/startseite/Wettbewerb/ES2"),
    ]
    
    all_data = []
    
    for league_name, league_url in leagues:
        print(f"\n=== {league_name} ===")
        df = scrape_transfermarkt_players_from_league(league_url, max_teams=8)
        if not df.empty:
            df["liga"] = league_name
            all_data.append(df)
            print(f"  {len(df)} jugadores")
        time.sleep(3)
    
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


def import_from_csv(uploaded_file) -> pd.DataFrame:
    """Importa datos desde un archivo CSV."""
    try:
        df = pd.read_csv(uploaded_file)
        
        # Normalizar nombres de columnas
        df.columns = df.columns.str.lower().str.strip()
        
        # Mapear columnas comunes
        column_mapping = {
            'player': 'nombre',
            'jugador': 'nombre',
            'name': 'nombre',
            'team': 'equipo',
            'club': 'equipo',
            'position': 'posicion',
            'posicion': 'posicion',
            'age': 'edad',
            'edad': 'edad',
            'nationality': 'nacionalidad',
            'nacionalidad': 'nacionalidad',
            'games': 'partidos',
            'partidos': 'partidos',
            'minutes': 'minutos',
            'minutos': 'minutos',
            'goals': 'goles',
            'goles': 'goles',
            'assists': 'asistencias',
            'asistencias': 'asistencias',
            'market_value': 'valor_mercado',
            'value': 'valor_mercado',
            'valor': 'valor_mercado',
        }
        
        df = df.rename(columns=column_mapping)
        
        return df
        
    except Exception as e:
        print(f"Error importing CSV: {e}")
        return pd.DataFrame()


def merge_data(df_existing: pd.DataFrame, df_new: pd.DataFrame) -> pd.DataFrame:
    """Fusiona datos existentes con nuevos."""
    if df_new.empty:
        return df_existing
    
    # Normalizar nombres
    df_new["nombre_norm"] = df_new["nombre"].str.lower().str.strip()
    df_existing["nombre_norm"] = df_existing["nombre"].str.lower().str.strip()
    
    # Merge valores de mercado
    if "valor_mercado" in df_new.columns:
        market_values = df_new[["nombre_norm", "valor_mercado"]].drop_duplicates()
        df_existing = df_existing.merge(
            market_values, on="nombre_norm", how="left", suffixes=("", "_new")
        )
        df_existing["valor_mercado"] = df_existing["valor_mercado_new"].fillna(df_existing["valor_mercado"])
        df_existing = df_existing.drop(columns=[c for c in df_existing.columns if c.endswith("_new")])
    
    df_existing = df_existing.drop(columns=["nombre_norm"], errors="ignore")
    
    return df_existing


LEAGUE_MAPPING = {
    "england-premier-league": "Premier League",
    "premier-league": "Premier League",
    "spain-laliga": "LaLiga",
    "laliga": "LaLiga",
    "germany-bundesliga": "Bundesliga",
    "bundesliga": "Bundesliga",
    "italy-serie-a": "Serie A",
    "serie-a": "Serie A",
    "france-ligue-1": "Ligue 1",
    "ligue-1": "Ligue 1",
    "portugal-primeira-liga": "Liga Portugal",
    "liga-portugal": "Liga Portugal",
    "netherlands-eredivisie": "Eredivisie",
    "eredivisie": "Eredivisie",
    "turkey-super-lig": "Super Lig",
    "super-lig": "Super Lig",
    "belgium-jupiler-league": "Jupiler League",
    "jupiler-league": "Jupiler League",
    "england-championship": "Championship",
    "championship": "Championship",
    "usa-mls": "MLS",
    "mls": "MLS",
    "spain-primera-division-rfef": "1a RFEF",
    "primera-division-rfef": "1a RFEF",
    "segunda-division-rfef": "2a RFEF",
    "tercera-division-rfef": "3a RFEF",
}


def detect_league_from_html(soup: BeautifulSoup) -> str:
    """Detecta la liga desde el HTML de WhoScored."""
    title = soup.find("title")
    if title:
        title_text = title.get_text().lower()
        for key, league in LEAGUE_MAPPING.items():
            if key in title_text:
                return league
    
    for link in soup.find_all("a", href=True):
        href = link.get("href", "").lower()
        for key, league in LEAGUE_MAPPING.items():
            if key in href:
                return league
    
    return "Desconocida"


def parse_whoscored_html(html_content: str) -> pd.DataFrame:
    """Parsea HTML de WhoScored y extrae estadísticas de jugadores."""
    players = []
    
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        
        league_name = detect_league_from_html(soup)
        
        tables = soup.find_all("table", {"class": "grid"})
        
        if not tables:
            tables = soup.find_all("table")
        
        for table in tables:
            rows = table.find_all("tr")
            
            header_row = None
            for row in rows:
                th = row.find("th")
                if th and "player" in th.get_text().lower():
                    header_row = row
                    break
            
            if not header_row:
                continue
            
            headers = [th.get_text(strip=True).lower() for th in header_row.find_all(["th", "td"])]
            
            col_map = {}
            for i, h in enumerate(headers):
                if "name" in h or "player" in h:
                    col_map["nombre"] = i
                elif "team" in h or "club" in h:
                    col_map["equipo"] = i
                elif "pos" in h:
                    col_map["posicion"] = i
                elif "goals" in h or "goal" in h:
                    col_map["goles"] = i
                elif "assist" in h:
                    col_map["asistencias"] = i
                elif "appear" in h or "game" in h:
                    col_map["partidos"] = i
                elif "minute" in h:
                    col_map["minutos"] = i
                elif "rating" in h:
                    col_map["rating"] = i
                elif "age" in h:
                    col_map["edad"] = i
                elif "yellow" in h:
                    col_map["tarjetas_amarillas"] = i
                elif "red" in h:
                    col_map["tarjetas_rojas"] = i
            
            for row in rows:
                if row.find("th"):
                    continue
                
                cells = row.find_all(["td", "th"])
                if len(cells) < 3:
                    continue
                
                player_data = {"liga": league_name}
                
                if "nombre" in col_map:
                    idx = col_map["nombre"]
                    if idx < len(cells):
                        name_tag = cells[idx].find("a")
                        name = name_tag.get_text(strip=True) if name_tag else cells[idx].get_text(strip=True)
                        player_data["nombre"] = name
                
                if "equipo" in col_map:
                    idx = col_map["equipo"]
                    if idx < len(cells):
                        player_data["equipo"] = cells[idx].get_text(strip=True)
                
                if "posicion" in col_map:
                    idx = col_map["posicion"]
                    if idx < len(cells):
                        player_data["posicion"] = cells[idx].get_text(strip=True)
                
                if "goles" in col_map:
                    idx = col_map["goles"]
                    if idx < len(cells):
                        try:
                            player_data["goles"] = int(cells[idx].get_text(strip=True))
                        except:
                            player_data["goles"] = 0
                
                if "asistencias" in col_map:
                    idx = col_map["asistencias"]
                    if idx < len(cells):
                        try:
                            player_data["asistencias"] = int(cells[idx].get_text(strip=True))
                        except:
                            player_data["asistencias"] = 0
                
                if "partidos" in col_map:
                    idx = col_map["partidos"]
                    if idx < len(cells):
                        try:
                            player_data["partidos"] = int(cells[idx].get_text(strip=True))
                        except:
                            player_data["partidos"] = 0
                
                if "minutos" in col_map:
                    idx = col_map["minutos"]
                    if idx < len(cells):
                        try:
                            player_data["minutos"] = int(cells[idx].get_text(strip=True).replace(",", ""))
                        except:
                            player_data["minutos"] = 0
                
                if "rating" in col_map:
                    idx = col_map["rating"]
                    if idx < len(cells):
                        try:
                            player_data["rating"] = float(cells[idx].get_text(strip=True))
                        except:
                            player_data["rating"] = 0.0
                
                if "edad" in col_map:
                    idx = col_map["edad"]
                    if idx < len(cells):
                        try:
                            player_data["edad"] = int(cells[idx].get_text(strip=True))
                        except:
                            player_data["edad"] = 25
                
                if "tarjetas_amarillas" in col_map:
                    idx = col_map["tarjetas_amarillas"]
                    if idx < len(cells):
                        try:
                            player_data["tarjetas_amarillas"] = int(cells[idx].get_text(strip=True))
                        except:
                            player_data["tarjetas_amarillas"] = 0
                
                if "tarjetas_rojas" in col_map:
                    idx = col_map["tarjetas_rojas"]
                    if idx < len(cells):
                        try:
                            player_data["tarjetas_rojas"] = int(cells[idx].get_text(strip=True))
                        except:
                            player_data["tarjetas_rojas"] = 0
                
                if "nombre" in player_data and player_data["nombre"]:
                    players.append(player_data)
        
        if not players:
            script_tags = soup.find_all("script")
            for script in script_tags:
                if script.string and "playerName" in script.string:
                    player_data = {"liga": league_name}
                    player_data["nombre"] = "Unknown"
                    players.append(player_data)
    
    except Exception as e:
        print(f"Error parsing WhoScored HTML: {e}")
    
    df = pd.DataFrame(players)
    
    if not df.empty:
        defaults = {
            "partidos": 0,
            "minutos": 0,
            "goles": 0,
            "asistencias": 0,
            "tarjetas_amarillas": 0,
            "tarjetas_rojas": 0,
            "rating": 0.0,
            "edad": 25,
            "valor_mercado": 0,
            "pie": "Derecho",
            "altura_cm": 180,
            "temporada": "2024/25",
            "participaciones_gol": 0,
            "goles_por_90": 0.0,
            "asistencias_por_90": 0.0,
            "pais": "",
            "grupo": "",
            "fecha_nacimiento": "",
        }
        
        for col, val in defaults.items():
            if col not in df.columns:
                df[col] = val
        
        df["participaciones_gol"] = df.get("goles", 0) + df.get("asistencias", 0)
        
        if "minutos" in df.columns and "goles" in df.columns:
            df["goles_por_90"] = df.apply(
                lambda x: round(x.get("goles", 0) / (x.get("minutos", 1) / 90), 2) if x.get("minutos", 0) > 0 else 0.0,
                axis=1
            )
        
        if "minutos" in df.columns and "asistencias" in df.columns:
            df["asistencias_por_90"] = df.apply(
                lambda x: round(x.get("asistencias", 0) / (x.get("minutos", 1) / 90), 2) if x.get("minutos", 0) > 0 else 0.0,
                axis=1
            )
    
    return df


def import_whoscored_html(uploaded_file) -> pd.DataFrame:
    """Importa datos desde archivo HTML de WhoScored."""
    try:
        if hasattr(uploaded_file, 'getvalue'):
            content = uploaded_file.getvalue()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")
        else:
            with open(uploaded_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        return parse_whoscored_html(content)
    except Exception as e:
        print(f"Error importing WhoScored HTML: {e}")
        return pd.DataFrame()


def import_whoscored_from_directory(directory_path: str) -> pd.DataFrame:
    """Importa todos los archivos HTML de WhoScored en un directorio."""
    all_players = []
    
    if not os.path.exists(directory_path):
        print(f"Directorio no encontrado: {directory_path}")
        return pd.DataFrame()
    
    html_files = [f for f in os.listdir(directory_path) if f.endswith(".html") or f.endswith(".htm")]
    
    print(f"Encontrados {len(html_files)} archivos HTML")
    
    for html_file in html_files:
        filepath = os.path.join(directory_path, html_file)
        print(f"Procesando: {html_file}")
        
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            df = parse_whoscored_html(content)
            if not df.empty:
                all_players.append(df)
                print(f"  -> {len(df)} jugadores extraídos")
        
        except Exception as e:
            print(f"  Error: {e}")
    
    if all_players:
        return pd.concat(all_players, ignore_index=True)
    return pd.DataFrame()

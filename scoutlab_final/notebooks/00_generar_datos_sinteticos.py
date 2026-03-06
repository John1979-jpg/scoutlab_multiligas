"""
Generador de datos sinteticos completo.
Estructura correcta:
  1a RFEF: 2 grupos x 20 equipos = 40 equipos
  2a RFEF: 5 grupos x 18 equipos = 90 equipos
  3a RFEF: 18 grupos x 18 equipos = 324 equipos
Total: 454 equipos
"""
import pandas as pd
import numpy as np
import os
from datetime import date, timedelta

np.random.seed(42)

# ==========================================================
# 1a RFEF - 2 grupos x 20 equipos
# ==========================================================
RFEF1 = {
    "Grupo 1": [
        "Unionistas de Salamanca","SD Ponferradina","Zamora CF","CF Talavera",
        "Racing de Ferrol","Cultural Leonesa","CE Sabadell","Gimnastic de Tarragona",
        "CD Teruel","SD Amorebieta","Barakaldo CF","UD Logrones",
        "CD Lugo","Real Union de Irun","Sestao River","Celta Fortuna",
        "Atletico de Madrid B","UD San Sebastian de los Reyes","SD Eibar B","Deportivo Fabril"
    ],
    "Grupo 2": [
        "Recreativo de Huelva","Cordoba CF","AD Ceuta","Algeciras CF",
        "Marbella FC","Linares Deportivo","UCAM Murcia","Sevilla Atletico",
        "Real Betis Deportivo","CD Badajoz","UD Merida","Atletico Sanluqueno",
        "Yeclano Deportivo","San Fernando CD","Antequera CF","CF Intercity",
        "Hercules CF","CD El Ejido","Cadiz CF B","FC Cartagena B"
    ],
}

# ==========================================================
# 2a RFEF - 5 grupos x 18 equipos
# ==========================================================
RFEF2 = {
    "Grupo 1": [
        "Pontevedra CF B","Compostela","CD Barco","Alondras CF","Arosa SC",
        "Coruxo FC","Racing Villalbes","Bergantiños CF","Silva SD","Somozas CF",
        "UP Langreo","Real Aviles","Marino de Luanco","Gijon Industrial",
        "Racing de Santander B","Gimnastica de Torrelavega","CD Guijuelo","Salamanca UDS"
    ],
    "Grupo 2": [
        "SD Leioa","Arenas de Getxo","Barakaldo CF B","Gernika Club","CD Vitoria",
        "Sestao River B","Real Sociedad C","CD Basconia","Athletic Club B","CD Laudio",
        "UD Logrones B","CD Calahorra","SD Logrones","Izarra CF",
        "SD Ejea","CD Ebro","UD Barbastro","Real Zaragoza B"
    ],
    "Grupo 3": [
        "CE L Hospitalet","UE Olot","CF Badalona Futur","UE Cornella","CE Europa",
        "Girona FC B","UE Sant Andreu","CF Reus Deportiu","UE Lleida",
        "FC Barcelona C","CE Manresa","CF Igualada","Atletico Baleares",
        "CD Ferreries","UD Poblense","CE Constancia","CF Gandia","Atletico Saguntino"
    ],
    "Grupo 4": [
        "Xerez CD","Xerez Deportivo","CD Utrera","Conil CF","CD Gerena",
        "Sevilla FC C","UD Tomares","Ecija Balompie","Atletico Malagueño",
        "CF Villanovense","CD Don Benito","CD Extremadura","Cacereno","UD Melilla",
        "Recreativo Granada","UCAM Murcia B","Orihuela CF","Aguilas FC"
    ],
    "Grupo 5": [
        "Real Madrid C","Getafe CF B","CF Fuenlabrada","AD Alcorcon","RSD Alcala",
        "Mostoles CF","Rayo Vallecano B","CD Leganes B","Atletico Pinto",
        "Las Palmas Atletico","CD Tenerife B","UD Tamaraceite","CD Toledo",
        "CP Villarrobledo","CD Manchego","CD Quintanar del Rey","UD Socuellamos","CD Coria"
    ],
}

# ==========================================================
# 3a RFEF - 18 grupos x 18 equipos (generados por region)
# ==========================================================

def gen_3rfef_teams():
    """Genera equipos realistas para los 18 grupos de 3a RFEF."""
    groups = {}

    # Grupo I - Galicia
    groups["Grupo 1"] = [
        "Arzua SD","CD Barco B","Alondras CF B","Racing Villalbes B","CF Beluso",
        "Pontevedra CF C","Arosa SC B","SD Teucro","CD Ribadumia","UD Ourense",
        "CF Canelas","Polvorin FC","Deportivo Fabril B","Celta de Vigo C",
        "CD Lugo B","Viveiro CF","Moeche CF","CSD Arzua"
    ]
    # Grupo II - Asturias
    groups["Grupo 2"] = [
        "TSK Roces","CD Covadonga","UC Ceares","CD Llanes","Urraca CF",
        "CF Navia","UP Langreo B","Vetusta CF","Real Oviedo B","CD Mosconia",
        "CD Praviano","Gijon Industrial B","Sporting de Gijon B","Colunga CF",
        "SD Lenense","CD Caudal","Tuilla CF","Condal Club"
    ]
    # Grupo III - Cantabria
    groups["Grupo 3"] = [
        "Gimnastica Torrelavega B","Racing Santander C","CD Bezana","UD Somorrostro",
        "SD Noja","CD Cabezon","CF Vimenor","CD Colindres","UD Solares",
        "SD Torina","Castro FC","CD Guarnizo","Textil Escudo","SD Santoña",
        "CD Tropezon","UC Cartes","CD Laredo","Cultural Guarnizo B"
    ]
    # Grupo IV - Pais Vasco
    groups["Grupo 4"] = [
        "CD Lagun Onak","SD Beasain","Tolosa CF","SD Amorebieta B","CD Basconia B",
        "Deportivo Alaves B","Arenas Club B","CD Aurrera Vitoria","CD Laudio B",
        "Antiguoko","Deusto CF","Sodupe SD","SD Lemona","Bermeo",
        "Portugalete CF","Mungia","Llodio","Eibar B"
    ]
    # Grupo V - Cataluna
    groups["Grupo 5"] = [
        "UE Figueres","CF Mollet","CF Amposta","CF Montblanc","CF Balaguer",
        "UE Vilassar de Mar","FC Santboia","UE Rapitenca","CF Tortosa",
        "CE Constancia B","CD Binissalem","UD Poblense B","CE Alaior",
        "UE Sants","CF Peralada","EC Granollers","CE Jupiter","CE Manresa B"
    ]
    # Grupo VI - Valencia
    groups["Grupo 6"] = [
        "CD Bunol","UD Alzira","CF Gandia B","Atletico Levante","CF Torre Levante",
        "CD Acero","UD Castellonense","CD Onda","CD Alcoyano B","CF Eldense B",
        "CF La Nucia B","UD Horadada","CD Roda","Villarreal CF C",
        "Valencia CF Mestalla B","CD Javea","CF Burriana","CD Segorbe"
    ]
    # Grupo VII - Madrid
    groups["Grupo 7"] = [
        "Atletico de Madrid C","Real Madrid D","CF Trival Valderas","ED Moratalaz",
        "CD Canillas","AD Parla","AD Alcorcon B","CDA Navalcarnero",
        "CF Pozuelo","UD San Sebastian Reyes B","UD Colonia Moscardo",
        "Getafe CF C","Rayo Vallecano C","CD Leganes C","RSD Alcala B",
        "CD Mostoles URJC B","Flat Earth FC","AD Torrejon CF"
    ]
    # Grupo VIII - Castilla y Leon
    groups["Grupo 8"] = [
        "CD Numancia","Arandina CF","CD Mirandés B","UD Santa Marta",
        "Atletico Tordesillas","Gimnastica Segoviana","CF Salmantino",
        "CD Guijuelo B","Zamora CF B","SD Ponferradina B","Cultural Leonesa B",
        "CD Palencia Cristo Atletico","Real Valladolid Promesas B",
        "Burgos CF Promesas","Bembibre","CD Bupolsa","UD Salamanca B","CF La Bañeza"
    ]
    # Grupo IX - Aragon
    groups["Grupo 9"] = [
        "CD Teruel B","SD Huesca B","Cuarte Industrial","Atletico Monzon",
        "CD Binefar","Calamocha CF","CD Brea","CF Epila",
        "Villanueva CF","Tamarite","Caspe","Borja","Sabiñanigo",
        "Utebo","Barbastro B","Ejea B","Tauste","Almudévar"
    ]
    # Grupo X - Navarra
    groups["Grupo 10"] = [
        "CA Osasuna B","Pena Sport FC","CD Tudelano","UD Mutilvera",
        "Peña Azagresa","CD Fontellas","CD Burladés","San Juan",
        "Cortes CF","Murchante","Txantrea","CD Iruña","Subiza",
        "Itaroa","CD Oberena","Lourdes","Ardoi","Pamplona"
    ]
    # Grupo XI - Extremadura
    groups["Grupo 11"] = [
        "CD Cacereño B","UP Plasencia","Moralo CP","CD Diocesano",
        "Montijo CF","CF Villanovense B","Jerez CF","Trujillo CF",
        "Miajadas","CD Don Alvaro","Azuaga","Arroyo CP","Calamonte",
        "CP Valdivia","Olivenza","Almendralejo B","Badajoz B","Zafra Atletico"
    ]
    # Grupo XII - Andalucia Oriental (Granada, Almeria, Jaen)
    groups["Grupo 12"] = [
        "CF Motril","Huetor Tajar","Alhama CF","CD El Ejido 2012",
        "Almeria B","Poli Almeria","Huetor Vega","Atarfe Industrial",
        "Guadix CF","Baza","CD Torredonjimeno","Linares B",
        "Real Jaen B","Mancha Real","Martos","CD Huescar",
        "Maracena","CD Loja"
    ]
    # Grupo XIII - Andalucia Occidental (Sevilla, Cadiz, Huelva, Cordoba)
    groups["Grupo 13"] = [
        "Utrera B","Lebrijana","Coria CF","CD Cabecense",
        "Gerena B","Sevilla FC D","Betis Deportivo C","San Roque de Lepe",
        "Isla Cristina","Ayamonte","Cartaya","CD Puerto Real",
        "Sanlucar","Chiclana CF","Pozoblanco","Cordoba CF B",
        "Montilla","Palma del Rio"
    ]
    # Grupo XIV - Murcia
    groups["Grupo 14"] = [
        "Real Murcia B","FC Cartagena C","Mar Menor FC","Lorca FC",
        "Lorca Deportiva","CF Aguilas B","Cieza","Jumilla",
        "Caravaca","Mazarron","Muleño","Bullense",
        "Yeclano B","Churra","CF Molina","Santomera",
        "El Palmar","Beniel"
    ]
    # Grupo XV - Canarias
    groups["Grupo 15"] = [
        "UD Las Palmas C","CD Tenerife C","UD Tamaraceite B","Lanzarote",
        "Fuerteventura","San Fernando","CD Mensajero","Tenisca",
        "Ibarra","Panaderia Pulido","Juventud Maritima","CD Santa Ursula",
        "Herbania","San Bartolome","Buzanada","CD Union Sur Yaiza",
        "Guia","Arucas CF"
    ]
    # Grupo XVI - La Rioja
    groups["Grupo 16"] = [
        "CD Alfaro","Casalarreina","River Ebro","UD Logrones C",
        "CD Varea","CD Arnedo","CF Pradejón","CD Calahorra B",
        "Agoncillo","CD Nájera","SD Oyonesa","CD Nanclares",
        "CD Aurrera Ondarroa","SD Eibar C","CF Mondragón","CD Tolosa B",
        "Anaitasuna","Eusko Taldea"
    ]
    # Grupo XVII - Baleares
    groups["Grupo 17"] = [
        "CD Atlético Baleares B","RCD Mallorca B","CE Andratx","CD Manacor",
        "Pena Deportiva","CF Soller","UD Ibiza B","SC Peña Sant Jordi",
        "CD Binissalem B","CF Platges de Calvia","CD Serverense","Collerense",
        "Felanitx","UD Arenal","CE Son Sardina","Portmany","San Rafael","Formentera"
    ]
    # Grupo XVIII - Castilla-La Mancha
    groups["Grupo 18"] = [
        "CD Manchego B","CD Toledo B","CF La Solana","CP Villarrobledo B",
        "CD Quintanar B","UD Almansa B","CD Guadalajara","Illescas CF",
        "CD Azuqueca","Tarancón","Villacañas","Manzanares","CF Puertollano",
        "Calvo Sotelo Puertollano","Socuellamos B","Tomelloso","Ciudad Real CF","Herencia"
    ]
    return groups

RFEF3 = gen_3rfef_teams()

# ==========================================================
# Factores de valor por liga
# ==========================================================
FACTOR_VALOR = {"1a RFEF": 1.0, "2a RFEF": 0.45, "3a RFEF": 0.18}

# ==========================================================
# Distribución de posiciones por equipo (24 jugadores)
# ==========================================================
POSICIONES = {
    "Portero": 2, "Defensa Central": 4, "Lateral Derecho": 2,
    "Lateral Izquierdo": 2, "Mediocentro Defensivo": 2, "Mediocentro": 3,
    "Mediapunta": 2, "Extremo Derecho": 2, "Extremo Izquierdo": 2,
    "Delantero Centro": 3,
}

NACS = [
    ("Espana",0.72),("Argentina",0.05),("Colombia",0.04),("Brasil",0.03),
    ("Francia",0.03),("Marruecos",0.02),("Portugal",0.02),("Senegal",0.02),
    ("Venezuela",0.01),("Ecuador",0.01),("Paraguay",0.01),("Nigeria",0.01),
    ("Ghana",0.01),("Camerun",0.01),("Uruguay",0.01),
]
NOMBRES = [
    "Adrian","Alejandro","Alvaro","Andres","Antonio","Carlos","Daniel","David",
    "Diego","Eduardo","Fernando","Francisco","Gabriel","Gonzalo","Hugo","Ivan",
    "Javier","Jorge","Jose","Juan","Luis","Manuel","Marco","Mario","Miguel",
    "Nicolas","Oscar","Pablo","Pedro","Rafael","Raul","Roberto","Ruben",
    "Samuel","Santiago","Sergio","Victor","Iker","Unai","Aitor","Mikel","Lucas",
]
APELLIDOS = [
    "Garcia","Martinez","Lopez","Sanchez","Gonzalez","Rodriguez","Fernandez",
    "Perez","Gomez","Martin","Jimenez","Ruiz","Hernandez","Diaz","Moreno",
    "Alvarez","Romero","Torres","Navarro","Dominguez","Gil","Serrano","Blanco","Molina",
]

GOL_R = {"Portero":0.0,"Defensa Central":0.08,"Lateral Derecho":0.05,"Lateral Izquierdo":0.05,"Mediocentro Defensivo":0.06,"Mediocentro":0.12,"Mediapunta":0.2,"Extremo Derecho":0.22,"Extremo Izquierdo":0.2,"Delantero Centro":0.35}
AST_R = {"Portero":0.0,"Defensa Central":0.06,"Lateral Derecho":0.15,"Lateral Izquierdo":0.15,"Mediocentro Defensivo":0.08,"Mediocentro":0.18,"Mediapunta":0.25,"Extremo Derecho":0.2,"Extremo Izquierdo":0.2,"Delantero Centro":0.1}
ALT_M = {"Portero":(187,4),"Defensa Central":(183,5),"Lateral Derecho":(176,5),"Lateral Izquierdo":(176,5),"Mediocentro Defensivo":(180,5),"Mediocentro":(177,5),"Mediapunta":(175,5),"Extremo Derecho":(174,5),"Extremo Izquierdo":(174,5),"Delantero Centro":(181,6)}
FP = {"Portero":0.6,"Defensa Central":0.8,"Lateral Derecho":0.85,"Lateral Izquierdo":0.85,"Mediocentro Defensivo":0.9,"Mediocentro":1.0,"Mediapunta":1.1,"Extremo Derecho":1.15,"Extremo Izquierdo":1.1,"Delantero Centro":1.2}


def main():
    nac_n, nac_p = zip(*NACS)
    registros = []
    id_g = 1

    all_leagues = [
        ("1a RFEF", RFEF1),
        ("2a RFEF", RFEF2),
        ("3a RFEF", RFEF3),
    ]

    for liga, grupos in all_leagues:
        factor = FACTOR_VALOR[liga]
        for grupo, equipos in grupos.items():
            for equipo in equipos:
                for posicion, cantidad in POSICIONES.items():
                    for _ in range(cantidad):
                        edad = int(np.random.triangular(18, 25, 37))
                        minutos = int(np.random.uniform(200, 3200))
                        partidos = max(1, minutos // 85)
                        goles = int(np.random.poisson(GOL_R.get(posicion, 0.1) * partidos))
                        asistencias = int(np.random.poisson(AST_R.get(posicion, 0.1) * partidos))
                        g90 = round(goles / (minutos / 90), 2) if minutos > 0 else 0.0
                        a90 = round(asistencias / (minutos / 90), 2) if minutos > 0 else 0.0

                        base = (goles * 3 + asistencias * 2 + partidos * 0.5) * 50000
                        if edad < 21:
                            fe = 0.8 + (edad - 18) * 0.1
                        elif 21 <= edad <= 28:
                            fe = 1.0 + (25 - abs(edad - 25)) * 0.05
                        elif 28 < edad <= 32:
                            fe = 1.0 - (edad - 28) * 0.1
                        else:
                            fe = max(0.2, 0.5 - (edad - 32) * 0.05)

                        valor = base * fe * FP.get(posicion, 1.0) * factor * np.random.uniform(0.7, 1.4)
                        valor = round(max(5000, int(valor)) / 5000) * 5000

                        mu, sigma = ALT_M.get(posicion, (178, 5))

                        registros.append({
                            "id": id_g,
                            "nombre": np.random.choice(NOMBRES) + " " + np.random.choice(APELLIDOS) + " " + np.random.choice(APELLIDOS),
                            "edad": edad,
                            "nacionalidad": np.random.choice(nac_n, p=nac_p),
                            "posicion": posicion,
                            "pie": np.random.choice(["Derecho", "Izquierdo", "Ambidiestro"], p=[0.65, 0.25, 0.10]),
                            "altura_cm": int(np.random.normal(mu, sigma)),
                            "equipo": equipo,
                            "grupo": grupo,
                            "liga": liga,
                            "valor_mercado": valor,
                            "temporada": "2024/25",
                            "fecha_nacimiento": (date(2025-edad, 1, 1) + timedelta(days=int(np.random.randint(1,365)))).isoformat(),
                            "partidos": partidos,
                            "minutos": minutos,
                            "goles": goles,
                            "asistencias": asistencias,
                            "participaciones_gol": goles + asistencias,
                            "tarjetas_amarillas": int(np.random.poisson(0.15 * partidos)),
                            "tarjetas_rojas": 1 if np.random.random() < 0.05 else 0,
                            "goles_por_90": g90,
                            "asistencias_por_90": a90,
                        })
                        id_g += 1

    df = pd.DataFrame(registros)
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/jugadores.csv", index=False)

    print("=== RESUMEN ===")
    for liga_name in ["1a RFEF", "2a RFEF", "3a RFEF"]:
        sub = df[df["liga"] == liga_name]
        n_grupos = sub["grupo"].nunique()
        n_equipos = sub["equipo"].nunique()
        print(f"{liga_name}: {n_grupos} grupos, {n_equipos} equipos, {len(sub)} jugadores, valor medio {sub['valor_mercado'].mean():,.0f} EUR")
    print(f"TOTAL: {len(df)} jugadores, {df['equipo'].nunique()} equipos")


if __name__ == "__main__":
    main()

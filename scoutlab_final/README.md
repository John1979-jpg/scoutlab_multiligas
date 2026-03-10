# ScoutLab

Plataforma de scouting y analisis de rendimiento para jugadores de futbol profesional en multiples ligas europeas.

## Descripcion

ScoutLab es una herramienta de analisis de datos deportivos que permite a departamentos de scouting de clubes de futbol analizar el rendimiento y valor de mercado de jugadores en las principales ligas europeas (Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, Eredivisie, Super Lig, Liga Portugal). La plataforma integra datos de Transfermarkt y utiliza Machine Learning para identificar jugadores infravalorados y sobrevalorados.

## Funcionalidades

- **Control de acceso** con sistema de login y roles de usuario
- **Dashboard interactivo** con KPIs del mercado, heatmaps y scatter plots
- **Filtros avanzados** por pais, liga, equipo, posicion, edad, valor de mercado, fecha de nacimiento y mas (selectbox, text_input, date_input, checkbox, slider)
- **Analisis individual** de jugadores con graficos radar y comparativa por posicion
- **Comparador multijugador** con radar superpuesto y percentiles
- **Buscador de jugadores similares** basado en distancia euclidiana normalizada
- **Watchlist** con sistema de seguimiento, notas de scouting y alertas configurables
- **Modelo de ML** para prediccion de valor de mercado (Gradient Boosting Regressor)
- **Exportacion a PDF** de informes individuales y de equipo con fpdf2
- **Importacion de datos** desde CSV

## Estructura del proyecto

```
scoutlab_final/
    app.py                       Punto de entrada Streamlit
    requirements.txt             Dependencias
    .streamlit/config.toml       Configuracion de Streamlit
    views/
        home.py                  Pagina de inicio / Dashboard
        stats.py                 Estadisticas y jugadores similares
        comparator.py            Comparador de jugadores
        watchlist.py             Watchlist y alertas
    backend/
        auth.py                  Autenticacion y login
        data_loader.py           Carga de datos
        data_import.py           Importacion desde CSV
        filters.py               Logica de filtros
        pdf_export.py            Generacion de PDFs
        ml_model.py              Modelo de Machine Learning
        scraper.py               Web scraping de datos
    notebooks/
        01_adquisicion.py                Web scraping de datos
        02_limpieza_eda.py               Limpieza y EDA
        03_modelo_ml.py                  Entrenamiento del modelo
        pipeline_datos.py                Pipeline de actualizacion
    data/
        processed/               Datos procesados (jugadores.csv)
    models/                      Modelos entrenados (.pkl)
```

## Instalacion

```bash
pip install -r requirements.txt
```

## Ejecucion local

```bash
streamlit run app.py
```

Credenciales de prueba: `demo / demo`

## Despliegue en Streamlit Cloud

1. Sube el repositorio a GitHub
2. Accede a [share.streamlit.io](https://share.streamlit.io)
3. Conecta el repositorio y selecciona `app.py` como punto de entrada
4. Despliega

## Fuentes de datos

- **Transfermarkt**: Valores de mercado, estadisticas de rendimiento (goles, asistencias, minutos, tarjetas), datos contractuales e informacion personal

## Tecnologias

- Python 3.10+
- Streamlit
- Plotly
- Scikit-learn (Gradient Boosting Regressor)
- BeautifulSoup4 (Web Scraping)
- fpdf2 (Generacion de PDFs)
- Pandas / NumPy

## Modelo de Machine Learning

El modelo utiliza un Gradient Boosting Regressor con las siguientes caracteristicas:

- **Features**: edad, partidos, minutos, goles, asistencias, participaciones_gol, tarjetas, goles_por_90, asistencias_por_90, altura_cm, posicion_encoded, liga_encoded
- **Target**: valor_mercado
- **R2 (test)**: ~0.93
- **Features mas importantes**: liga_encoded, participaciones_gol

## Autor

John Triguero - Proyecto Final de Master (TFM) - Master en Python Avanzado Aplicado al Deporte (MPAD)
Sports Data Campus / UCAM



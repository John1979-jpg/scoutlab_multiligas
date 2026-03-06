"""
03 - Entrenamiento del Modelo de Machine Learning
==================================================
Entrena un modelo Gradient Boosting para predecir el valor
de mercado de jugadores basandose en sus estadisticas.
"""

import os
import sys
import pandas as pd

# Agregar el directorio raiz del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.ml_model import train_model
from backend.data_loader import load_players


def main():
    print("Cargando datos de jugadores...")
    df = load_players()
    print("Total de jugadores: " + str(len(df)))

    print("\nEntrenando modelo de prediccion de valor de mercado...")
    metrics = train_model(df)

    print("\n=== RESULTADOS DEL ENTRENAMIENTO ===")
    print("Muestras utilizadas: " + str(metrics["n_samples"]))
    print("Features utilizadas: " + str(metrics["n_features"]))
    print("\nMetricas en conjunto de entrenamiento:")
    print("  MAE: {:,.0f} EUR".format(metrics["mae_train"]))
    print("  R2:  {:.4f}".format(metrics["r2_train"]))
    print("\nMetricas en conjunto de test:")
    print("  MAE: {:,.0f} EUR".format(metrics["mae_test"]))
    print("  R2:  {:.4f}".format(metrics["r2_test"]))
    print("\nValidacion cruzada (5 folds):")
    print("  MAE medio: {:,.0f} EUR (+/- {:,.0f})".format(
        metrics["cv_mae_mean"], metrics["cv_mae_std"]))

    print("\nImportancia de variables:")
    fi = metrics.get("feature_importance", {})
    for var, imp in fi.items():
        bar = "#" * int(imp * 50)
        print("  {:<25s} {:.4f} {}".format(var, imp, bar))

    print("\nModelo guardado correctamente.")


if __name__ == "__main__":
    main()

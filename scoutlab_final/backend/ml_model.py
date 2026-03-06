"""
Modulo de Machine Learning.
Entrena y aplica un modelo de prediccion de valor de mercado
basado en estadisticas de rendimiento del jugador.
"""

import os
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
MODEL_PATH = os.path.join(MODELS_DIR, "model_valor.pkl")
ENCODERS_PATH = os.path.join(MODELS_DIR, "encoders.pkl")

FEATURE_COLUMNS = [
    "edad", "partidos", "minutos", "goles", "asistencias",
    "participaciones_gol", "tarjetas_amarillas", "tarjetas_rojas",
    "goles_por_90", "asistencias_por_90", "altura_cm",
    "posicion_encoded", "liga_encoded",
]


def _prepare_features(df, encoders=None, fit=False):
    """Prepara las features para el modelo."""
    df_ml = df.copy()
    if encoders is None:
        encoders = {}

    if fit:
        le_pos = LabelEncoder()
        df_ml["posicion_encoded"] = le_pos.fit_transform(df_ml["posicion"].astype(str))
        encoders["posicion"] = le_pos
    else:
        le_pos = encoders.get("posicion")
        if le_pos:
            known = set(le_pos.classes_)
            df_ml["posicion_encoded"] = df_ml["posicion"].apply(
                lambda x: le_pos.transform([x])[0] if x in known else -1
            )
        else:
            df_ml["posicion_encoded"] = 0

    if fit:
        le_pie = LabelEncoder()
        df_ml["pie_encoded"] = le_pie.fit_transform(df_ml["pie"].astype(str))
        encoders["pie"] = le_pie
    else:
        le_pie = encoders.get("pie")
        if le_pie:
            known = set(le_pie.classes_)
            df_ml["pie_encoded"] = df_ml["pie"].apply(
                lambda x: le_pie.transform([x])[0] if x in known else -1
            )
        else:
            df_ml["pie_encoded"] = 0

    if fit:
        le_liga = LabelEncoder()
        df_ml["liga_encoded"] = le_liga.fit_transform(df_ml["liga"].astype(str))
        encoders["liga"] = le_liga
    else:
        le_liga = encoders.get("liga")
        if le_liga:
            known_l = set(le_liga.classes_)
            df_ml["liga_encoded"] = df_ml["liga"].apply(
                lambda x: le_liga.transform([x])[0] if x in known_l else -1
            )
        else:
            df_ml["liga_encoded"] = 0

    for col in FEATURE_COLUMNS:
        if col not in df_ml.columns:
            df_ml[col] = 0

    return df_ml[FEATURE_COLUMNS], encoders


def train_model(df):
    """Entrena el modelo de prediccion de valor de mercado."""
    df_valid = df.dropna(subset=["valor_mercado"])
    df_valid = df_valid[df_valid["valor_mercado"] > 0]
    df_valid = df_valid[df_valid["minutos"] > 0]

    X, encoders = _prepare_features(df_valid, fit=True)
    y = df_valid["valor_mercado"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = GradientBoostingRegressor(
        n_estimators=200, max_depth=5, learning_rate=0.1,
        min_samples_split=10, min_samples_leaf=5, subsample=0.8, random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    metrics = {
        "mae_train": mean_absolute_error(y_train, y_pred_train),
        "mae_test": mean_absolute_error(y_test, y_pred_test),
        "r2_train": r2_score(y_train, y_pred_train),
        "r2_test": r2_score(y_test, y_pred_test),
        "n_samples": len(df_valid),
        "n_features": len(FEATURE_COLUMNS),
    }

    cv_scores = cross_val_score(model, X, y, cv=5, scoring="neg_mean_absolute_error")
    metrics["cv_mae_mean"] = -cv_scores.mean()
    metrics["cv_mae_std"] = cv_scores.std()

    importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_))
    metrics["feature_importance"] = dict(
        sorted(importances.items(), key=lambda x: x[1], reverse=True)
    )

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(encoders, ENCODERS_PATH)
    return metrics


def load_model():
    """Carga el modelo entrenado y los encoders."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODERS_PATH):
        return None, None
    return joblib.load(MODEL_PATH), joblib.load(ENCODERS_PATH)


def predict_value(df):
    """Predice el valor de mercado para los jugadores."""
    model, encoders = load_model()
    if model is None:
        train_model(df)
        model, encoders = load_model()
    if model is None:
        df["valor_predicho"] = np.nan
        df["diferencia_valor"] = np.nan
        return df

    df_result = df.copy()
    valid_mask = (df_result["minutos"] > 0) & (df_result["valor_mercado"] > 0)

    if valid_mask.sum() > 0:
        X, _ = _prepare_features(df_result[valid_mask], encoders=encoders, fit=False)
        predictions = model.predict(X)
        predictions = np.round(predictions / 5000) * 5000
        predictions = np.maximum(predictions, 10000)
        df_result.loc[valid_mask, "valor_predicho"] = predictions
        df_result.loc[valid_mask, "diferencia_valor"] = (
            df_result.loc[valid_mask, "valor_predicho"]
            - df_result.loc[valid_mask, "valor_mercado"]
        )
    else:
        df_result["valor_predicho"] = np.nan
        df_result["diferencia_valor"] = np.nan

    return df_result


def get_undervalued_players(df, top_n=20):
    """Identifica los jugadores mas infravalorados."""
    df_pred = predict_value(df)
    df_valid = df_pred.dropna(subset=["diferencia_valor"])
    df_valid = df_valid[df_valid["diferencia_valor"] > 0]
    return df_valid.sort_values("diferencia_valor", ascending=False).head(top_n)


def get_overvalued_players(df, top_n=20):
    """Identifica los jugadores mas sobrevalorados."""
    df_pred = predict_value(df)
    df_valid = df_pred.dropna(subset=["diferencia_valor"])
    df_valid = df_valid[df_valid["diferencia_valor"] < 0]
    return df_valid.sort_values("diferencia_valor", ascending=True).head(top_n)

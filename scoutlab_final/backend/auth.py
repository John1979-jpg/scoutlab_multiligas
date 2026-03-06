"""
Modulo de autenticacion y control de acceso.
Gestiona el login de usuarios para la aplicacion ScoutLab.
"""

import hashlib
import streamlit as st

USERS_DB = {
    "admin": {
        "password_hash": hashlib.sha256("scoutlab2025".encode()).hexdigest(),
        "nombre": "Administrador",
        "rol": "admin",
    },
    "scout": {
        "password_hash": hashlib.sha256("scout2025".encode()).hexdigest(),
        "nombre": "Analista Scout",
        "rol": "analista",
    },
    "demo": {
        "password_hash": hashlib.sha256("demo".encode()).hexdigest(),
        "nombre": "Usuario Demo",
        "rol": "viewer",
    },
}


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username: str, password: str):
    user = USERS_DB.get(username)
    if user and user["password_hash"] == _hash_password(password):
        return {"username": username, "nombre": user["nombre"], "rol": user["rol"]}
    return None


def login_form() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.markdown(
        """
        <style>
        .login-logo { font-size: 44px; text-align: center; margin-bottom: 2px; }
        .login-title {
            font-size: 30px; font-weight: 700; color: #1B4332;
            text-align: center; margin-bottom: 4px; letter-spacing: -0.5px;
        }
        .login-subtitle {
            font-size: 14px; color: #6B7280; text-align: center;
            margin-bottom: 24px; line-height: 1.5;
        }
        .login-hint {
            text-align: center; margin-top: 16px; font-size: 12px;
            color: #9CA3AF; background: #F9FAFB; padding: 8px 12px;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            '<div class="login-logo">&#9917;</div>'
            '<div class="login-title">ScoutLab</div>'
            '<div class="login-subtitle">'
            "Plataforma de Scouting Profesional<br>"
            "Analisis multiligas de rendimiento y valor"
            "</div>",
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Introduce tu usuario")
            password = st.text_input(
                "Password", type="password", placeholder="Introduce tu password"
            )
            submitted = st.form_submit_button("Acceder", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Introduce usuario y password.")
                    return False
                user_data = authenticate(username, password)
                if user_data:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user_data
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")
                    return False

        st.markdown(
            '<div class="login-hint">'
            "Credenciales de prueba: <b>demo / demo</b>"
            "</div>",
            unsafe_allow_html=True,
        )

    return False


def logout():
    for key in ["authenticated", "user"]:
        st.session_state.pop(key, None)
    st.rerun()


def get_current_user():
    return st.session_state.get("user")

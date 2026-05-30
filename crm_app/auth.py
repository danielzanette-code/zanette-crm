from __future__ import annotations

import hashlib
import streamlit as st

# ── CSS da tela de login ───────────────────────────────────────────────────────
LOGIN_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

    .stApp {
        background: #1c1c1e !important;
        font-family: 'Inter', sans-serif !important;
    }

    #MainMenu, footer, header { visibility: hidden; }

    .login-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 92vh;
    }

    .login-card {
        background: #2c2c2e;
        border: 1px solid rgba(78,205,196,0.2);
        border-radius: 24px;
        padding: 48px 44px 40px;
        width: 100%;
        max-width: 420px;
        box-shadow: 0 32px 80px rgba(0,0,0,0.6);
    }

    .login-logo {
        font-size: 36px;
        text-align: center;
        margin-bottom: 6px;
    }

    .login-title {
        color: #f2f2f7;
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.03em;
        text-align: center;
        margin: 0 0 4px 0;
        text-transform: uppercase;
    }

    .login-sub {
        color: #6c6c70;
        font-size: 13px;
        text-align: center;
        margin: 0 0 32px 0;
    }

    .login-label {
        color: #aeaeb2;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 6px;
        display: block;
    }

    .login-error {
        background: rgba(255,59,48,0.12);
        border: 1px solid rgba(255,59,48,0.3);
        border-radius: 12px;
        color: #ff6b6b;
        font-size: 13px;
        font-weight: 600;
        padding: 12px 16px;
        text-align: center;
        margin-bottom: 16px;
    }

    .login-footer {
        color: #48484a;
        font-size: 11px;
        text-align: center;
        margin-top: 24px;
    }

    /* inputs */
    [data-testid="stTextInput"] input {
        background: #1c1c1e !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        color: #f2f2f7 !important;
        font-size: 15px !important;
        padding: 12px 16px !important;
        height: 48px !important;
    }

    [data-testid="stTextInput"] input:focus {
        border-color: #4ecdc4 !important;
        box-shadow: 0 0 0 3px rgba(78,205,196,0.15) !important;
    }

    [data-testid="stTextInput"] label {
        color: #aeaeb2 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
    }

    /* botão login */
    div.stButton > button {
        background: #4ecdc4 !important;
        border: none !important;
        border-radius: 12px !important;
        color: #1c1c1e !important;
        font-size: 14px !important;
        font-weight: 800 !important;
        height: 48px !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        width: 100% !important;
        margin-top: 8px !important;
        transition: all 160ms ease !important;
    }

    div.stButton > button:hover {
        background: #38b2aa !important;
        box-shadow: 0 4px 20px rgba(78,205,196,0.35) !important;
        transform: translateY(-1px) !important;
    }

    /* esconde elementos desnecessários */
    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
</style>
"""


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _get_credentials() -> dict[str, str]:
    """Busca credenciais do st.secrets ou usa padrão local."""
    try:
        users = st.secrets["users"]
        return {k: v for k, v in users.items()}
    except Exception:
        # fallback local para desenvolvimento
        return {
            "danielzanette": _hash("D4niel.2025@#"),
        }


def render_login() -> bool:
    """
    Renderiza a tela de login.
    Retorna True se o usuário estiver autenticado.
    """
    if st.session_state.get("authenticated"):
        return True

    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    # centraliza o card
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown(
            """
            <div style="padding-top: 60px">
                <div class="login-logo">📊</div>
                <div class="login-title">360 Inteligência</div>
                <div class="login-sub">Mercado Cerâmico · Acesso restrito</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.get("login_error"):
            st.markdown(
                '<div class="login-error">⚠️ Usuário ou senha incorretos</div>',
                unsafe_allow_html=True,
            )

        with st.form("login_form", clear_on_submit=False):
            usuario = st.text_input("Usuário", placeholder="seu usuário")
            senha   = st.text_input("Senha", type="password", placeholder="••••••••")
            entrar  = st.form_submit_button("Entrar", use_container_width=True)

        if entrar:
            credentials = _get_credentials()
            hashed = _hash(senha)
            if usuario in credentials and credentials[usuario] == hashed:
                st.session_state["authenticated"] = True
                st.session_state["usuario"] = usuario
                st.session_state.pop("login_error", None)
                st.rerun()
            else:
                st.session_state["login_error"] = True
                st.rerun()

        st.markdown(
            '<div class="login-footer">© 2026 · 360 Inteligência de Mercado</div>',
            unsafe_allow_html=True,
        )

    return False


def logout() -> None:
    st.session_state.pop("authenticated", None)
    st.session_state.pop("usuario", None)
    st.rerun()

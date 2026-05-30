from __future__ import annotations

import hashlib
import streamlit as st

LOGIN_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
    }

    #MainMenu, footer, header { visibility: hidden; }

    /* ── fundo geométrico SVG ── */
    .stApp {
        background-color: #111112 !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100%25' height='100%25'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%23111112'/%3E%3Cstop offset='1' stop-color='%231c1c1e'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect fill='url(%23g)' width='100%25' height='100%25'/%3E%3Cpolygon fill='%23ffffff' fill-opacity='0.02' points='0,0 400,0 200,300'/%3E%3Cpolygon fill='%234ecdc4' fill-opacity='0.04' points='400,0 800,0 600,400'/%3E%3Cpolygon fill='%23ffffff' fill-opacity='0.015' points='0,300 300,600 0,600'/%3E%3Cpolygon fill='%234ecdc4' fill-opacity='0.03' points='800,200 1200,0 1200,400'/%3E%3Cpolygon fill='%23ffffff' fill-opacity='0.02' points='600,400 900,200 1100,500 800,700'/%3E%3Cpolygon fill='%234ecdc4' fill-opacity='0.025' points='0,500 400,400 300,800 0,800'/%3E%3Cpolygon fill='%23ffffff' fill-opacity='0.015' points='700,600 1200,500 1200,900 900,1000'/%3E%3Cpolygon fill='%234ecdc4' fill-opacity='0.02' points='200,700 600,600 500,1000 100,1000'/%3E%3C/svg%3E") !important;
        background-size: cover !important;
        background-attachment: fixed !important;
    }

    .main .block-container {
        max-width: 190px !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin: 0 auto !important;
    }

    /* ── texto 360 de fundo ── */
    .login-bg-text {
        position: fixed;
        bottom: -40px;
        left: 50%;
        transform: translateX(-50%);
        font-size: clamp(120px, 20vw, 220px);
        font-weight: 900;
        color: rgba(255,255,255,0.025);
        letter-spacing: -0.06em;
        pointer-events: none;
        user-select: none;
        white-space: nowrap;
        font-family: 'Inter', sans-serif;
        z-index: 0;
    }

    /* ── header ── */
    .login-header {
        text-align: center;
        padding: 52px 0 24px;
        position: relative;
        z-index: 1;
    }

    .login-dot {
        width: 8px;
        height: 8px;
        background: #4ecdc4;
        border-radius: 50%;
        display: inline-block;
        margin-bottom: 14px;
        box-shadow: 0 0 14px rgba(78,205,196,0.7);
    }

    .login-title {
        color: #f2f2f7;
        font-size: 28px;
        font-weight: 900;
        letter-spacing: -0.04em;
        text-transform: uppercase;
        margin: 0;
        line-height: 1;
    }

    .login-title span { color: #4ecdc4; }

    .login-sub {
        color: #48484a;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-top: 8px;
    }

    /* ── card ── */
    .login-card-wrap {
        position: relative;
        z-index: 1;
    }

    /* ── error ── */
    .login-error {
        background: rgba(255,69,58,0.08);
        border-left: 3px solid #ff453a;
        border-radius: 8px;
        color: #ff6961;
        font-size: 12px;
        font-weight: 600;
        padding: 10px 14px;
        margin-bottom: 16px;
        letter-spacing: 0.02em;
    }

    /* ── inputs ── */
    [data-testid="stTextInput"] {
        position: relative;
    }

    /* reduz espaço entre widgets */
    [data-testid="stVerticalBlock"] > div { margin-bottom: -8px !important; }
    div[data-testid="element-container"] { margin-bottom: 0 !important; }

    [data-testid="stTextInput"] input {
        background: rgba(22,22,24,0.95) !important;
        border: 1px solid rgba(255,255,255,0.09) !important;
        border-radius: 8px !important;
        color: #f2f2f7 !important;
        font-size: 14px !important;
        font-family: 'Inter', sans-serif !important;
        padding: 10px 14px !important;
        height: 46px !important;
        transition: all 180ms ease !important;
    }

    [data-testid="stTextInput"] input:focus {
        border-color: #4ecdc4 !important;
        box-shadow: 0 0 0 3px rgba(78,205,196,0.12), 0 4px 16px rgba(0,0,0,0.3) !important;
        background: rgba(28,28,30,1) !important;
    }

    [data-testid="stTextInput"] input::placeholder {
        color: rgba(255,255,255,0.35) !important;
        font-weight: 400 !important;
    }

    /* esconde os labels USUÁRIO / SENHA */
    [data-testid="stTextInput"] label {
        display: none !important;
    }

    /* remove espaço do label escondido */
    [data-testid="stTextInput"] > div:first-child {
        display: none !important;
    }

    /* ── botão ── */
    div.stButton > button {
        background: linear-gradient(135deg, #4ecdc4, #38b2aa) !important;
        border: none !important;
        border-radius: 8px !important;
        color: #111112 !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        height: 46px !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        width: 100% !important;
        margin-top: 4px !important;
        font-family: 'Inter', sans-serif !important;
        box-shadow: 0 4px 20px rgba(78,205,196,0.22) !important;
        transition: all 180ms ease !important;
    }

    div.stButton > button:hover {
        box-shadow: 0 8px 32px rgba(78,205,196,0.4) !important;
        transform: translateY(-2px) !important;
        filter: brightness(1.05) !important;
    }

    div.stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ── form sem borda ── */
    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* ── footer ── */
    .login-footer {
        color: #2c2c2e;
        font-size: 11px;
        text-align: center;
        padding: 18px 0 32px;
        letter-spacing: 0.04em;
        position: relative;
        z-index: 1;
    }

    .login-footer b {
        color: #3a3a3c;
    }
</style>
"""


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _get_credentials() -> dict[str, str]:
    try:
        users = st.secrets["users"]
        return {k: v for k, v in users.items()}
    except Exception:
        return {
            "danielzanette": _hash("D4niel.2025@#"),
        }


def render_login() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    # fundo geométrico + marca d'água 360
    st.markdown(
        """
        <div id="login-bg">
            <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" style="position:absolute;inset:0">
                <polygon points="0,0 500,0 250,320"        fill="rgba(255,255,255,0.06)"/>
                <polygon points="500,0 1100,0 800,380"     fill="rgba(78,205,196,0.07)"/>
                <polygon points="0,320 320,580 0,700"      fill="rgba(255,255,255,0.045)"/>
                <polygon points="900,180 1400,0 1400,450"  fill="rgba(78,205,196,0.06)"/>
                <polygon points="650,380 980,180 1200,520 880,720" fill="rgba(255,255,255,0.05)"/>
                <polygon points="0,550 420,420 320,820 0,900"      fill="rgba(78,205,196,0.055)"/>
                <polygon points="750,620 1400,520 1400,950 1000,1000" fill="rgba(255,255,255,0.04)"/>
                <polygon points="200,750 650,640 550,1000 120,1000"   fill="rgba(78,205,196,0.05)"/>
                <polygon points="300,200 700,100 600,500 200,550"     fill="rgba(255,255,255,0.035)"/>
                <polygon points="100,80 420,30 380,280 60,260"        fill="rgba(255,255,255,0.03)"/>
            </svg>
            <div id="login-watermark">360</div>
        </div>
        <style>
            #login-bg {
                position: fixed;
                inset: 0;
                background: #111112;
                z-index: -1;
                overflow: hidden;
                pointer-events: none;
            }
            #login-watermark {
                position: absolute;
                bottom: -60px;
                left: 50%;
                transform: translateX(-50%);
                font-family: 'Inter', sans-serif;
                font-size: clamp(160px, 22vw, 280px);
                font-weight: 900;
                letter-spacing: -0.06em;
                color: transparent;
                -webkit-text-stroke: 1px rgba(255,255,255,0.04);
                white-space: nowrap;
                pointer-events: none;
                user-select: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # header
    st.markdown(
        """
        <div class="login-header">
            <div class="login-dot"></div>
            <div class="login-title"><span>360</span> Inteligência</div>
            <div class="login-sub">Mercado Cerâmico · Acesso restrito</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # erro
    if st.session_state.get("login_error"):
        st.markdown(
            '<div class="login-error">Usuário ou senha incorretos. Tente novamente.</div>',
            unsafe_allow_html=True,
        )

    # formulário
    st.markdown('<div class="login-card-wrap">', unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
        senha   = st.text_input("Senha", type="password", placeholder="••••••••••••")
        entrar  = st.form_submit_button("Entrar →", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if entrar:
        credentials = _get_credentials()
        if usuario in credentials and credentials[usuario] == _hash(senha):
            st.session_state["authenticated"] = True
            st.session_state["usuario"] = usuario
            st.session_state.pop("login_error", None)
            st.rerun()
        else:
            st.session_state["login_error"] = True
            st.rerun()

    st.markdown(
        '<div class="login-footer">© 2026 · <b>360 Inteligência de Mercado</b></div>',
        unsafe_allow_html=True,
    )

    return False


def logout() -> None:
    st.session_state.pop("authenticated", None)
    st.session_state.pop("usuario", None)
    st.rerun()

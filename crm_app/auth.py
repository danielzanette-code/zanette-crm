from __future__ import annotations

import hashlib
import hmac
import streamlit as st

LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background: #111112 !important;
}

#MainMenu, footer, header { visibility: hidden; }

[data-testid="stMainBlockContainer"],
.main .block-container,
.block-container {
    max-width: 420px !important;
    padding: 0 20px !important;
    margin: 0 auto !important;
}

[data-testid="stVerticalBlock"],
[data-testid="stLayoutWrapper"],
[data-testid="stForm"] {
    max-width: 380px !important;
    width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* fundo poligonal fixo */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    z-index: 0;
    background: #111112;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1440' height='900'%3E%3Cpolygon points='0,0 520,0 260,330' fill='rgba(255,255,255,0.055)'/%3E%3Cpolygon points='520,0 1100,0 810,370' fill='rgba(78,205,196,0.065)'/%3E%3Cpolygon points='0,330 340,570 0,720' fill='rgba(255,255,255,0.04)'/%3E%3Cpolygon points='920,160 1440,0 1440,460' fill='rgba(78,205,196,0.055)'/%3E%3Cpolygon points='660,370 990,170 1210,530 880,730' fill='rgba(255,255,255,0.045)'/%3E%3Cpolygon points='0,560 430,420 330,830 0,900' fill='rgba(78,205,196,0.05)'/%3E%3Cpolygon points='760,630 1440,530 1440,900 1010,900' fill='rgba(255,255,255,0.035)'/%3E%3Cpolygon points='210,760 660,640 560,900 130,900' fill='rgba(78,205,196,0.045)'/%3E%3C/svg%3E");
    background-size: cover;
    pointer-events: none;
}

/* marca d'agua 360 */
.stApp::after {
    content: "360";
    position: fixed;
    bottom: -80px;
    left: 50%;
    transform: translateX(-50%);
    font-family: 'Inter', sans-serif;
    font-size: 280px;
    font-weight: 900;
    letter-spacing: -0.06em;
    color: transparent;
    -webkit-text-stroke: 1px rgba(255,255,255,0.045);
    pointer-events: none;
    z-index: 0;
    white-space: nowrap;
}

/* conteúdo acima do fundo */
.main { position: relative; z-index: 1; }

/* header */
.lg-header {
    text-align: center;
    padding: 64px 0 28px;
}
.lg-dot {
    width: 8px; height: 8px;
    background: #4ecdc4;
    border-radius: 50%;
    display: inline-block;
    margin-bottom: 16px;
    box-shadow: 0 0 12px rgba(78,205,196,0.8);
}
.lg-title {
    color: #f2f2f7;
    font-size: 26px;
    font-weight: 900;
    letter-spacing: -0.04em;
    text-transform: uppercase;
    line-height: 1;
    margin: 0;
}
.lg-title span { color: #4ecdc4; }
.lg-sub {
    color: #48484a;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-top: 8px;
}

/* erro */
.lg-error {
    background: rgba(255,69,58,0.1);
    border-left: 3px solid #ff453a;
    border-radius: 8px;
    color: #ff6961;
    font-size: 12px;
    font-weight: 600;
    padding: 10px 14px;
    margin-bottom: 12px;
}

/* card de vidro ao redor do form */
[data-testid="stForm"] {
    background: rgba(24,24,26,0.75) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 16px !important;
    padding: 24px 20px 20px !important;
    box-shadow: 0 32px 64px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06) !important;
}

/* inputs */
[data-testid="stTextInput"] label { display: none !important; }

[data-testid="stTextInput"] input {
    background: #161618 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    color: #f2f2f7 !important;
    -webkit-text-fill-color: #f2f2f7 !important;
    font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
    height: 46px !important;
    padding: 0 14px !important;
    transition: border-color 180ms ease !important;
    box-shadow: none !important;
    outline: none !important;
    -webkit-box-shadow: 0 0 0px 1000px #161618 inset !important;
}

[data-testid="stTextInput"] input::placeholder {
    color: rgba(255,255,255,0.3) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.3) !important;
}

[data-testid="stTextInput"] input:focus {
    border-color: #4ecdc4 !important;
    -webkit-box-shadow: 0 0 0px 1000px #161618 inset, 0 0 0 3px rgba(78,205,196,0.12) !important;
}

/* fix autofill azul/branco do browser */
[data-testid="stTextInput"] input:-webkit-autofill,
[data-testid="stTextInput"] input:-webkit-autofill:hover,
[data-testid="stTextInput"] input:-webkit-autofill:focus,
[data-testid="stTextInput"] input:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0px 1000px #161618 inset !important;
    -webkit-text-fill-color: #f2f2f7 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    transition: background-color 9999s ease-in-out 0s !important;
}

/* remove qualquer borda/fundo extra em todos os wrappers */
[data-testid="stTextInput"] > div,
[data-testid="stTextInput"] > div > div,
[data-testid="stTextInput"] > div > div > div {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    gap: 0 !important;
    padding: 0 !important;
}

/* força os dois campos com o mesmo visual exato */
[data-testid="stTextInput"] > div > div > div > input,
[data-testid="stTextInput"] > div > div > div > div > input {
    background: #161618 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    color: #f2f2f7 !important;
    -webkit-text-fill-color: #f2f2f7 !important;
    font-size: 14px !important;
    height: 46px !important;
    padding: 0 14px !important;
    width: 100% !important;
    box-shadow: none !important;
    outline: none !important;
    -webkit-box-shadow: 0 0 0px 1000px #161618 inset !important;
}

/* olho fora do campo */
[data-testid="stTextInput"] button {
    position: absolute !important;
    right: -28px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    opacity: 0.2 !important;
    transition: opacity 200ms !important;
    color: white !important;
}
[data-testid="stTextInput"] button:hover {
    opacity: 0.5 !important;
    background: transparent !important;
    transform: translateY(-50%) !important;
}

/* botão entrar */
[data-testid="stFormSubmitButton"] button,
[data-testid="stBaseButton-secondaryFormSubmit"],
div.stButton > button {
    background: linear-gradient(135deg, #4ecdc4 0%, #38b2aa 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    color: #111112 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    height: 48px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 4px 20px rgba(78,205,196,0.25) !important;
    transition: all 180ms ease !important;
    margin-top: 4px !important;
}
[data-testid="stFormSubmitButton"] button:hover,
[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
div.stButton > button:hover {
    box-shadow: 0 6px 28px rgba(78,205,196,0.4) !important;
    transform: translateY(-1px) !important;
    filter: brightness(1.05) !important;
}

/* footer */
.lg-footer {
    color: #2c2c2e;
    font-size: 11px;
    text-align: center;
    padding: 20px 0 40px;
    letter-spacing: 0.04em;
}
.lg-footer b { color: #3a3a3c; }
</style>
"""


from crm_app.security import (
    esta_bloqueado,
    gerar_csrf_token,
    registrar_tentativa_falha,
    resetar_tentativas,
    sanitize_input,
    tentativas_restantes,
    validar_usuario,
)


def _hash(p: str) -> str:
    salt = "360IM@zanette#crm"
    return hashlib.sha256(f"{salt}{p}".encode()).hexdigest()


def _legacy_hash(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()


def _password_matches(password: str, stored_hash: str) -> bool:
    """Aceita hash novo com salt e hash legado para não bloquear usuários existentes."""
    if not stored_hash:
        return False
    return hmac.compare_digest(stored_hash, _hash(password)) or hmac.compare_digest(
        stored_hash, _legacy_hash(password)
    )


def _get_credentials() -> dict[str, str]:
    try:
        return {k: v for k, v in st.secrets["users"].items()}
    except Exception:
        return {"danielzanette": _hash("D4niel.2025@#")}


def render_login() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    # gera token CSRF da sessão
    gerar_csrf_token()

    st.markdown(
        """
        <div class="lg-header">
            <div class="lg-dot"></div>
            <div class="lg-title"><span>360</span> Inteligência</div>
            <div class="lg-sub">Mercado Cerâmico · Acesso restrito</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── verifica bloqueio por rate limiting ───────────────────────────────
    bloqueado, segundos = esta_bloqueado()
    if bloqueado:
        minutos = segundos // 60
        segundos_r = segundos % 60
        st.markdown(
            f'<div class="lg-error">🔒 Muitas tentativas. Aguarde {minutos}m {segundos_r}s para tentar novamente.</div>',
            unsafe_allow_html=True,
        )
        st.stop()
        return False

    # ── mensagem de erro ──────────────────────────────────────────────────
    if st.session_state.get("login_error"):
        restantes = tentativas_restantes()
        msg = "Usuário ou senha incorretos."
        if restantes <= 2:
            msg += f" {restantes} tentativa(s) restante(s)."
        st.markdown(f'<div class="lg-error">{msg}</div>', unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        usuario = st.text_input("u", placeholder="Usuário", label_visibility="collapsed")
        senha   = st.text_input("s", type="password", placeholder="Senha", label_visibility="collapsed")
        entrar  = st.form_submit_button("Entrar →", use_container_width=True)

    if entrar:
        # sanitiza inputs antes de qualquer verificação
        usuario_clean = sanitize_input(usuario)

        # valida formato do usuário
        if not validar_usuario(usuario_clean):
            st.session_state["login_error"] = True
            registrar_tentativa_falha(usuario_clean)
            st.rerun()

        creds = _get_credentials()
        if usuario_clean in creds and _password_matches(senha, creds[usuario_clean]):
            st.session_state["authenticated"] = True
            st.session_state["usuario"] = usuario_clean
            st.session_state.pop("login_error", None)
            resetar_tentativas()
            st.rerun()
        else:
            st.session_state["login_error"] = True
            registrar_tentativa_falha(usuario_clean)
            st.rerun()

    st.markdown(
        '<div class="lg-footer">© 2026 · <b>360 Inteligência de Mercado</b></div>',
        unsafe_allow_html=True,
    )

    return False


def logout() -> None:
    from crm_app.security import resetar_tentativas
    resetar_tentativas()
    for key in ["authenticated", "usuario", "_last_active", "_csrf", "login_error"]:
        st.session_state.pop(key, None)
    st.rerun()

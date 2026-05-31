"""
Camadas de segurança do 360 Inteligência de Mercado.

Proteções implementadas:
- Rate limiting: bloqueia IP após N tentativas falhas
- Session timeout: expira sessão por inatividade
- Sanitização de inputs: previne XSS e injeção
- Logging de eventos: registra tentativas suspeitas
- CSRF básico via token de sessão
"""
from __future__ import annotations

import html
import logging
import secrets
import time
from typing import Any
from urllib.parse import urlparse

import streamlit as st

# ── configuração de logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SECURITY] %(levelname)s: %(message)s",
)
_log = logging.getLogger("security")

# ── constantes ────────────────────────────────────────────────────────────────
MAX_TENTATIVAS      = 5       # tentativas antes de bloquear
BLOQUEIO_SEGUNDOS   = 300     # 5 minutos de bloqueio
SESSION_TIMEOUT_S   = 3600    # 1 hora de inatividade expira sessão
MAX_INPUT_LEN       = 128     # tamanho máximo de qualquer input


# ── rate limiting (em memória por sessão) ─────────────────────────────────────

def _get_rate_state() -> dict:
    if "_rate" not in st.session_state:
        st.session_state["_rate"] = {"tentativas": 0, "bloqueado_ate": 0.0}
    return st.session_state["_rate"]


def registrar_tentativa_falha(usuario: str) -> None:
    state = _get_rate_state()
    state["tentativas"] += 1
    _log.warning("Tentativa falha #%s para usuário '%s'", state["tentativas"], _sanitize(usuario))
    if state["tentativas"] >= MAX_TENTATIVAS:
        state["bloqueado_ate"] = time.time() + BLOQUEIO_SEGUNDOS
        _log.warning("IP/sessão bloqueado por %ss após %s tentativas", BLOQUEIO_SEGUNDOS, MAX_TENTATIVAS)


def resetar_tentativas() -> None:
    st.session_state["_rate"] = {"tentativas": 0, "bloqueado_ate": 0.0}


def esta_bloqueado() -> tuple[bool, int]:
    """Retorna (bloqueado, segundos_restantes)."""
    state = _get_rate_state()
    agora = time.time()
    if state["bloqueado_ate"] > agora:
        restante = int(state["bloqueado_ate"] - agora)
        return True, restante
    if state["bloqueado_ate"] > 0 and agora >= state["bloqueado_ate"]:
        # desbloqueio automático
        state["tentativas"] = 0
        state["bloqueado_ate"] = 0.0
    return False, 0


def tentativas_restantes() -> int:
    state = _get_rate_state()
    return max(0, MAX_TENTATIVAS - state["tentativas"])


# ── session timeout ───────────────────────────────────────────────────────────

def atualizar_atividade() -> None:
    st.session_state["_last_active"] = time.time()


def verificar_timeout() -> bool:
    """Retorna True se a sessão expirou por inatividade."""
    last = st.session_state.get("_last_active")
    if last is None:
        return False
    if time.time() - last > SESSION_TIMEOUT_S:
        _log.info("Sessão expirada por inatividade")
        return True
    return False


def encerrar_sessao_expirada() -> None:
    usuario = st.session_state.get("usuario", "desconhecido")
    _log.info("Sessão encerrada: usuário '%s'", usuario)
    for key in ["authenticated", "usuario", "_last_active"]:
        st.session_state.pop(key, None)


# ── sanitização de inputs ─────────────────────────────────────────────────────

def _sanitize(value: Any) -> str:
    """Escapa HTML e limita tamanho — previne XSS."""
    if value is None:
        return ""
    text = str(value).strip()
    text = text[:MAX_INPUT_LEN]
    return html.escape(text)


def sanitize_input(value: Any) -> str:
    return _sanitize(value)


def safe_html(value: Any) -> str:
    return _sanitize(value)


def safe_url(value: Any) -> str:
    text = str(value or "").strip()
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return html.escape(text, quote=True)
    return "#"


def validar_usuario(usuario: str) -> bool:
    """Aceita apenas letras, números, ponto, hífen e underscore."""
    if not usuario:
        return False
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    return all(c in allowed for c in usuario) and len(usuario) <= 64


# ── CSRF token simples ────────────────────────────────────────────────────────

def gerar_csrf_token() -> str:
    if "_csrf" not in st.session_state:
        st.session_state["_csrf"] = secrets.token_urlsafe(32)
    return st.session_state["_csrf"]


def verificar_csrf(token: str) -> bool:
    return token == st.session_state.get("_csrf", "")


# ── verificação completa na entrada ──────────────────────────────────────────

def checar_seguranca() -> None:
    """
    Chamado no início de cada rerender do app autenticado.
    Verifica timeout e registra atividade.
    """
    if not st.session_state.get("authenticated"):
        return

    if verificar_timeout():
        encerrar_sessao_expirada()
        st.warning("⏱️ Sua sessão expirou por inatividade. Faça login novamente.")
        st.rerun()

    atualizar_atividade()

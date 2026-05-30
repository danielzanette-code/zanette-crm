from __future__ import annotations

import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import quote_plus

import requests
import streamlit as st

_YF_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}
_TIMEOUT = 6  # segundos por requisição


# ── helpers individuais (rápidos, sem cache — cache fica no fetch_radar) ──────

def _yahoo(symbol: str) -> tuple[str, float | None, float | None]:
    """Retorna (symbol, preço, variação%)."""
    try:
        r = requests.get(
            f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
            "?interval=1d&range=5d",
            headers=_YF_HEADERS,
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        meta  = r.json()["chart"]["result"][0]["meta"]
        price = float(meta.get("regularMarketPrice") or 0) or None
        prev  = float(
            meta.get("chartPreviousClose") or meta.get("previousClose") or 0
        ) or None
        pct   = round((price - prev) / prev * 100, 2) if price and prev else None
        return symbol, price, pct
    except Exception:
        return symbol, None, None


def _bcb(series: str) -> tuple[str, float | None]:
    """Retorna (series, último valor) do Banco Central."""
    try:
        r = requests.get(
            f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series}"
            "/dados/ultimos/1?formato=json",
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if data:
            return series, float(data[-1].get("valor", "0").replace(",", ".")) or None
    except Exception:
        pass
    return series, None


def _awesome() -> dict:
    try:
        r = requests.get(
            "https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL",
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


# ── fetch principal — TUDO em paralelo ────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_radar_economico() -> dict[str, object]:
    snap: dict[str, object] = {
        "usd_brl": None, "usd_brl_change": None,
        "eur_brl": None, "eur_brl_change": None,
        "wti_usd": None,    "wti_change": None,
        "brent_usd": None,  "brent_change": None,
        "gas_usd": None,    "gas_change": None,
        "copper_usd": None, "copper_change": None,
        "bdi": None,        "bdi_change": None,
        "incc_pct": None,
        "selic_pct": None,
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

    yahoo_symbols = {
        "CL=F": ("wti_usd",    "wti_change"),
        "BZ=F": ("brent_usd",  "brent_change"),
        "NG=F": ("gas_usd",    "gas_change"),
        "HG=F": ("copper_usd", "copper_change"),
        "^BDI": ("bdi",        "bdi_change"),
    }
    bcb_series = {
        "192": "incc_pct",
        "432": "selic_pct",
    }

    # ── dispara TUDO em paralelo ──────────────────────────────────────
    futures = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures["fx"] = pool.submit(_awesome)
        for sym in yahoo_symbols:
            futures[sym] = pool.submit(_yahoo, sym)
        for sid in bcb_series:
            futures[f"bcb_{sid}"] = pool.submit(_bcb, sid)

        # coleta resultados conforme chegam
        for key, fut in futures.items():
            try:
                result = fut.result()
            except Exception:
                continue

            if key == "fx":
                data = result
                for snap_key, pair in [("usd_brl", "USDBRL"), ("eur_brl", "EURBRL")]:
                    d = data.get(pair, {})
                    if d:
                        snap[snap_key]              = float(d.get("bid") or 0) or None
                        snap[f"{snap_key}_change"]  = float(d.get("pctChange") or 0)

            elif key in yahoo_symbols:
                _, price, pct = result
                pk, ck = yahoo_symbols[key]
                snap[pk] = price
                snap[ck] = pct

            elif key.startswith("bcb_"):
                sid = key[4:]
                _, val = result
                snap[bcb_series[sid]] = val

    return snap


@st.cache_data(ttl=900, show_spinner=False)
def fetch_news_categoria(query: str, limit: int = 5) -> list[dict[str, str]]:
    url = (
        f"https://news.google.com/rss/search?q={quote_plus(query)}"
        "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    )
    try:
        resp = requests.get(url, timeout=_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = []
        for item in root.findall(".//item")[:limit]:
            items.append({
                "title":    (item.findtext("title")   or "").strip(),
                "link":     (item.findtext("link")    or "").strip(),
                "pub_date": (item.findtext("pubDate") or "").strip(),
                "source":   (item.findtext("source")  or "").strip(),
            })
        return items
    except Exception:
        return []

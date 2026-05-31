from __future__ import annotations

import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
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
_TIMEOUT = 10  # segundos por requisição


# ── helpers individuais (rápidos, sem cache — cache fica no fetch_radar) ──────

def _yahoo(symbol: str) -> tuple[str, float | None, float | None]:
    """Retorna (symbol, último fechamento/preço disponível, variação%)."""
    encoded_symbol = quote_plus(symbol)

    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        try:
            r = requests.get(
                f"https://{host}/v8/finance/chart/{encoded_symbol}",
                params={"interval": "1d", "range": "10d"},
                headers=_YF_HEADERS,
                timeout=_TIMEOUT,
            )
            r.raise_for_status()
            result = r.json()["chart"]["result"][0]
            meta = result["meta"]
            closes = [
                float(value)
                for value in result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                if value is not None
            ]
            price = float(meta.get("regularMarketPrice") or 0) or (closes[-1] if closes else None)
            prev = (
                float(meta.get("chartPreviousClose") or meta.get("previousClose") or 0)
                or (closes[-2] if len(closes) >= 2 else None)
            )
            pct = round((price - prev) / prev * 100, 2) if price and prev else None
            return symbol, price, pct
        except Exception:
            continue

    return symbol, None, None


def _bcb(series: str) -> tuple[str, float | None]:
    """Retorna (series, último valor) do Banco Central."""
    for _ in range(2):
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
            continue
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


def _awesome_daily(pair: str) -> tuple[str, float | None, float | None]:
    """Retorna último fechamento disponível de câmbio, útil em fins de semana."""
    try:
        r = requests.get(
            f"https://economia.awesomeapi.com.br/json/daily/{pair}/7",
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return pair, None, None

        latest = rows[0]
        previous = rows[1] if len(rows) > 1 else {}
        price = float(latest.get("bid") or latest.get("ask") or latest.get("high") or 0) or None
        prev = float(previous.get("bid") or previous.get("ask") or previous.get("high") or 0) or None
        pct = round((price - prev) / prev * 100, 2) if price and prev else None
        return pair, price, pct
    except Exception:
        return pair, None, None


def _oilpriceapi() -> dict[str, tuple[float | None, float | None]]:
    """Retorna WTI e Brent pelo último fechamento público disponível."""
    data: dict[str, tuple[float | None, float | None]] = {}
    try:
        r = requests.get(
            "https://api.oilpriceapi.com/v1/demo/prices/latest",
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        rows = r.json().get("data", {}).get("prices", [])
        for item in rows:
            code = item.get("code")
            if code not in {"WTI_USD", "BRENT_CRUDE_USD"}:
                continue
            price = float(item.get("price") or 0) or None
            change = item.get("change_24h")
            pct = float(change) if change not in (None, "") else None
            data[code] = (price, pct)
    except Exception:
        pass

    if "WTI_USD" not in data:
        _, price, pct = _yahoo("CL=F")
        data["WTI_USD"] = (price, pct)
    if "BRENT_CRUDE_USD" not in data:
        _, price, pct = _yahoo("BZ=F")
        data["BRENT_CRUDE_USD"] = (price, pct)
    return data


# ── fetch principal — TUDO em paralelo ────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_radar_economico() -> dict[str, object]:
    snap: dict[str, object] = {
        "usd_brl": None, "usd_brl_change": None,
        "eur_brl": None, "eur_brl_change": None,
        "wti_usd": None,    "wti_change": None,
        "brent_usd": None,  "brent_change": None,
        "incc_pct": None,
        "selic_pct": None,
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

    bcb_series = {
        "192": "incc_pct",
        "432": "selic_pct",
    }

    # ── dispara TUDO em paralelo ──────────────────────────────────────
    futures = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures["fx"] = pool.submit(_awesome)
        futures["fx_daily_usd"] = pool.submit(_awesome_daily, "USD-BRL")
        futures["fx_daily_eur"] = pool.submit(_awesome_daily, "EUR-BRL")
        futures["oil"] = pool.submit(_oilpriceapi)
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

            elif key.startswith("fx_daily_"):
                pair, price, pct = result
                if pair == "USD-BRL":
                    snap["usd_brl"] = price or snap["usd_brl"]
                    snap["usd_brl_change"] = pct if pct is not None else snap["usd_brl_change"]
                elif pair == "EUR-BRL":
                    snap["eur_brl"] = price or snap["eur_brl"]
                    snap["eur_brl_change"] = pct if pct is not None else snap["eur_brl_change"]

            elif key == "oil":
                data = result
                snap["wti_usd"], snap["wti_change"] = data.get("WTI_USD", (None, None))
                snap["brent_usd"], snap["brent_change"] = data.get("BRENT_CRUDE_USD", (None, None))

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

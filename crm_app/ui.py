from __future__ import annotations

from datetime import date, datetime
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

from crm_app.helpers import (
    CHART_COLORS,
    clean_text,
    format_br_number,
    format_brl,
    format_quantity,
    format_usd,
    kpi_card,
    parse_br_number,
    section_title,
    style_chart,
    render_static_donut,
)
from crm_app.inteligencia_mercado.ui import render_inteligencia_mercado
from crm_app.inteligencia_mercado.data import fetch_news_categoria, fetch_radar_economico
from crm_app.security import safe_html, safe_url
from crm_app.database import (
    PRIORIDADES,
    STATUS_CLIENTE,
    TIPOS_INTERACAO,
    TIPOLOGIAS,
    add_interacao,
    add_produto_cliente,
    add_tecnico,
    delete_empresa,
    delete_produto_cliente,
    ensure_schema,
    get_empresa,
    list_empresas,
    list_interacoes,
    list_produtos_cliente,
    list_tecnicos,
    metrics,
    save_empresa,
    tecnico_options,
    update_produto_cliente,
)


CSS = """
<style>
    /* ── tokens ─────────────────────────────────────────────────────── */
    :root {
        --bg:         #1c1c1e;
        --bg-surface: #242426;
        --bg-card:    #2c2c2e;
        --bg-card-2:  #323234;
        --ink:        #f2f2f7;
        --ink-mid:    #aeaeb2;
        --muted:      #6c6c70;
        --accent:     #4ecdc4;
        --accent-dark:#38b2aa;
        --accent-soft:rgba(78,205,196,0.12);
        --border:     rgba(255,255,255,0.07);
        --border-mid: rgba(255,255,255,0.13);
        --shadow-sm:  0 1px 3px rgba(0,0,0,0.5), 0 4px 12px rgba(0,0,0,0.3);
        --shadow-md:  0 4px 16px rgba(0,0,0,0.55), 0 12px 36px rgba(0,0,0,0.35);
        --shadow-lg:  0 8px 32px rgba(0,0,0,0.6), 0 24px 64px rgba(0,0,0,0.4);
        --radius-sm:  8px;
        --radius-md:  14px;
        --radius-lg:  20px;
        --radius-xl:  26px;
        --font-sans:  "Inter", "Aptos", "Helvetica Neue", "Segoe UI", sans-serif;
        --font-serif: "Georgia", "Times New Roman", serif;
        --transition: 160ms cubic-bezier(.4,0,.2,1);
    }

    /* ── base ────────────────────────────────────────────────────────── */
    html, body, [class*="css"], .stApp {
        font-family: var(--font-sans);
        font-feature-settings: "tnum", "cv02", "cv03";
        -webkit-font-smoothing: antialiased;
        color: var(--ink);
    }

    .stApp {
        background: var(--bg);
        color: var(--ink);
    }

    .main .block-container {
        max-width: 1560px;
        padding-top: 1.2rem;
        padding-bottom: 4rem;
    }

    #MainMenu,
    footer,
    header,
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stToolbarActions"],
    [data-testid="stDecoration"],
    [data-testid="stDeployButton"],
    [data-testid="stStatusWidget"],
    [data-testid="stMainMenu"],
    iframe[title*="Streamlit Cloud"],
    iframe[title*="Status"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* ── expander / icon guard ───────────────────────────────────────── */
    i, svg,
    [data-testid="stExpanderToggleIcon"],
    [data-baseweb="icon"],
    .material-symbols-rounded,
    .material-icons,
    span[class*="material-symbol"] {
        text-transform: none !important;
        font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
        font-style: normal !important; font-weight: normal !important;
        letter-spacing: normal !important; line-height: 1 !important;
        white-space: nowrap !important; direction: ltr !important;
        -webkit-font-feature-settings: "liga";
        -webkit-font-smoothing: antialiased;
        font-feature-settings: "liga";
    }

    [data-testid="stExpander"],
    [data-testid="stExpander"] * {
        text-transform: none !important;
        font-family: var(--font-sans) !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderToggleIcon"],
    [data-testid="stExpander"] .material-symbols-rounded {
        font-family: "Material Symbols Rounded", "Material Icons" !important;
    }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] button {
        font-weight: 600;
    }

    /* ── hero ────────────────────────────────────────────────────────── */
    .crm-hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, #1c1c1e 0%, #2c2c2e 60%, #323234 100%);
        border: 1px solid rgba(78,205,196,0.2);
        color: #fff;
        border-radius: var(--radius-xl);
        padding: 28px 36px 26px;
        box-shadow: var(--shadow-lg);
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 32px;
    }

    .crm-hero-text { flex: 1; min-width: 0; }

    .crm-hero::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            radial-gradient(ellipse 50% 80% at 100% 50%, rgba(78,205,196,0.08) 0%, transparent 60%);
        pointer-events: none;
    }

    .crm-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(78,205,196,0.12);
        border: 1px solid rgba(78,205,196,0.3);
        border-radius: 999px;
        padding: 4px 12px;
        color: #4ecdc4;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .crm-hero h1 {
        margin: 0;
        font-family: var(--font-sans) !important;
        font-size: clamp(28px, 3vw, 48px);
        line-height: 1.0;
        font-weight: 800;
        letter-spacing: -0.04em;
        text-transform: uppercase !important;
        color: #fff;
    }

    .crm-hero p {
        color: rgba(255,255,255,0.45);
        margin: 10px 0 0;
        max-width: 680px;
        font-size: 13px;
        line-height: 1.6;
        font-weight: 400;
    }

    .crm-hero-stats {
        display: flex;
        gap: 0;
        flex-shrink: 0;
        background: rgba(255,255,255,0.04);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 4px 0;
    }

    .crm-hero-stat {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 12px 24px;
        border-left: 1px solid var(--border);
    }

    .crm-hero-stat:first-child { border-left: none; }

    .crm-hero-stat-val {
        font-size: clamp(24px, 2vw, 36px);
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #fff;
        line-height: 1;
    }

    .crm-hero-stat-lbl {
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.35);
        margin-top: 5px;
        white-space: nowrap;
    }

    /* ── metric cards (topo) ─────────────────────────────────────────── */
    .crm-metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 18px 20px 16px;
        box-shadow: var(--shadow-sm);
        min-height: 100px;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: space-between;
        transition: box-shadow var(--transition), transform var(--transition), border-color var(--transition);
    }

    .crm-metric-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
        border-color: var(--border-mid);
    }

    .crm-metric-label {
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0;
        font-family: var(--font-sans) !important;
    }

    .crm-metric-value {
        color: var(--ink);
        font-size: clamp(22px, 2vw, 34px);
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.04em;
        white-space: nowrap;
        margin-top: 10px;
    }

    .crm-metric-note {
        color: var(--muted);
        font-size: 11px;
        margin-top: 6px;
        font-weight: 500;
    }

    .crm-metric-accent {
        display: inline-block;
        width: 28px;
        height: 2px;
        border-radius: 99px;
        background: var(--accent);
        margin-bottom: 10px;
    }

    /* ── tabs ────────────────────────────────────────────────────────── */
    [data-testid="stTabs"] {
        background: var(--bg-surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 8px 10px 20px;
        box-shadow: var(--shadow-sm);
    }

    [data-testid="stTabs"] [role="tablist"] {
        gap: 4px;
        background: var(--bg);
        border-radius: var(--radius-md);
        padding: 5px;
        margin-bottom: 16px;
        border: 1px solid var(--border);
    }

    [data-testid="stTabs"] [role="tab"] {
        border-radius: var(--radius-sm);
        padding: 9px 20px;
        color: var(--muted);
        font-weight: 600;
        font-size: 13px;
        transition: all var(--transition);
        letter-spacing: 0.01em;
    }

    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: var(--bg-card);
        color: var(--ink);
        box-shadow: var(--shadow-sm);
        font-weight: 700;
        border: 1px solid var(--border-mid);
    }

    /* ── section headings ────────────────────────────────────────────── */
    h1, h2, h3, h4 {
        font-family: var(--font-sans) !important;
        letter-spacing: -0.02em;
        text-transform: uppercase !important;
        color: var(--ink);
    }

    .crm-section-title {
        font-family: var(--font-sans) !important;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 0.04em;
        color: var(--ink);
        margin: 8px 0 4px;
        text-align: left;
        text-transform: uppercase !important;
    }

    .crm-section-caption {
        color: var(--muted);
        font-size: 13px;
        font-weight: 400;
        line-height: 1.5;
        margin: 0 0 16px;
        text-align: left;
        text-transform: none !important;
    }

    /* ── divider ─────────────────────────────────────────────────────── */
    .crm-subtle-divider {
        width: 100%;
        height: 1px;
        border-radius: 99px;
        margin: 12px 0 18px;
        background: var(--border);
    }

    /* ── kpi card ────────────────────────────────────────────────────── */
    .bi-kpi {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 16px 18px;
        min-height: 88px;
        box-shadow: var(--shadow-sm);
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: space-between;
        transition: box-shadow var(--transition), transform var(--transition), border-color var(--transition);
    }

    .bi-kpi:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
        border-color: var(--border-mid);
    }

    .bi-kpi-label {
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        line-height: 1.3;
        margin-bottom: 0;
        font-family: var(--font-sans) !important;
    }

    .bi-kpi-value {
        color: var(--ink);
        font-size: clamp(18px, 1.6vw, 28px);
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.03em;
        margin-top: 8px;
        white-space: nowrap;
    }

    /* ── donut / chart titles ────────────────────────────────────────── */
    .donut-title {
        color: var(--ink-mid);
        font-size: 14px;
        font-weight: 700;
        letter-spacing: -0.01em;
        margin: 8px 0;
        text-align: center;
        text-transform: uppercase;
        font-family: var(--font-sans) !important;
    }

    .chart-heading { text-align: left; margin: 2px 0 8px; }

    .chart-heading-title {
        color: var(--ink);
        font-size: 16px;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        font-family: var(--font-sans) !important;
        text-transform: none !important;
    }

    .chart-heading-metric {
        display: inline-flex;
        align-items: center;
        margin-top: 6px;
        padding: 4px 10px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.01em;
    }

    /* ── charts ──────────────────────────────────────────────────────── */
    [data-testid="stPlotlyChart"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 6px 6px 0;
        box-shadow: var(--shadow-sm);
        overflow: hidden;
        min-height: 400px;
    }

    .static-donut-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        min-height: 400px;
        padding: 8px 8px 10px;
        overflow: hidden;
        user-select: none;
        pointer-events: none;
    }

    .static-donut-plot {
        position: relative;
        width: min(100%, 320px);
        aspect-ratio: 1;
        margin: 18px auto 0;
    }

    .static-donut-ring {
        position: absolute;
        inset: 22px;
        border-radius: 50%;
        background: #1c1c1e;
        box-shadow: inset 0 0 0 2px #1c1c1e;
    }

    .static-donut-hole {
        position: absolute;
        inset: 27%;
        border-radius: 50%;
        background: var(--bg-card);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 0 2px #1c1c1e;
    }

    .static-donut-center {
        color: #f2f2f7;
        font-size: 16px;
        font-weight: 500;
        line-height: 1.25;
        text-align: center;
    }

    .static-donut-center span {
        display: block;
    }

    .static-donut-pct {
        position: absolute;
        color: #f2f2f7;
        background: rgba(17,17,18,0.50);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 999px;
        padding: 2px 5px;
        font-size: 12px;
        font-weight: 800;
        line-height: 1;
        transform: translate(-50%, -50%);
        text-shadow: 0 1px 3px rgba(0,0,0,0.95);
        box-shadow: 0 2px 8px rgba(0,0,0,0.30);
    }

    .static-donut-legend {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px 18px;
        min-height: 42px;
        margin-top: -12px;
        color: var(--ink-mid);
        font-size: 12px;
        font-weight: 600;
    }

    .static-donut-legend-item {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        white-space: nowrap;
    }

    .static-donut-swatch {
        width: 11px;
        height: 11px;
        border: 2px solid #1c1c1e;
        border-radius: 2px;
        box-shadow: 0 0 0 1px rgba(255,255,255,0.18);
    }

    /* ── filter strip ────────────────────────────────────────────────── */
    .bi-filter-title {
        color: var(--muted);
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        margin-bottom: 4px;
        font-family: var(--font-sans) !important;
    }

    .bi-filter-help {
        color: var(--muted);
        font-size: 11px;
        margin: 0 0 6px;
    }

    /* ── news panel ──────────────────────────────────────────────────── */
    .news-panel-title {
        color: var(--ink);
        font-size: 14px;
        font-weight: 700;
        letter-spacing: -0.01em;
        margin: 0 0 10px;
    }

    .news-item {
        padding: 9px 0;
        border-top: 1px solid var(--border);
    }
    .news-item:first-of-type { border-top: none; padding-top: 0; }

    .news-link {
        display: block;
        color: #ffffff !important;
        font-size: 13px;
        font-weight: 600;
        line-height: 1.4;
        text-decoration: none;
        margin-bottom: 3px;
    }
    .news-link:hover { text-decoration: underline; }

    .news-meta { color: var(--muted); font-size: 11px; }

    /* ── forms / inputs ──────────────────────────────────────────────── */
    [data-testid="stForm"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 20px;
        box-shadow: var(--shadow-sm);
    }

    [data-testid="stExpander"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        overflow: hidden;
    }

    [data-testid="stDataFrame"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        overflow: hidden;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        border-radius: var(--radius-sm);
        border-color: var(--border-mid) !important;
        background: var(--bg-surface) !important;
        color: var(--ink) !important;
        font-size: 14px;
    }

    [data-testid="stRadio"] {
        background: var(--bg-surface);
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 6px 14px;
    }

    label, [data-testid="stWidgetLabel"] p {
        color: var(--ink-mid) !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        letter-spacing: 0.03em !important;
    }

    /* ── alerts / info / success ────────────────────────────────────── */
    div[data-testid="stAlert"] {
        border-radius: var(--radius-md);
        background: var(--bg-card) !important;
        border: 1px solid var(--border-mid) !important;
        color: var(--ink-mid) !important;
    }
    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] span {
        color: var(--ink-mid) !important;
    }
    div[data-testid="stAlert"] svg { color: var(--muted) !important; }

    /* ── dataframe dark ─────────────────────────────────────────────── */
    [data-testid="stDataFrame"] iframe,
    .stDataFrame { background: var(--bg-card) !important; }

    [data-testid="stDataFrameResizable"] {
        background: var(--bg-card) !important;
    }

    /* ── buttons ─────────────────────────────────────────────────────── */
    div.stButton > button {
        border-radius: 999px;
        min-height: 36px;
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        box-shadow: none;
        transition: all var(--transition);
    }

    div.stButton > button[kind="primary"] {
        background: #4ecdc4;
        border: none;
        color: #1c1c1e;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #38b2aa;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(78,205,196,0.3);
    }

    div.stButton > button[kind="secondary"] {
        background: var(--bg-card);
        border: 1px solid var(--border-mid);
        color: var(--ink-mid);
    }
    div.stButton > button[kind="secondary"]:hover {
        border-color: rgba(255,255,255,0.4);
        color: #ffffff;
        transform: translateY(-1px);
    }

    /* ── misc helpers ────────────────────────────────────────────────── */
    .stMarkdown p, .stCaption {
        color: var(--muted) !important;
    }

    .crm-subtle-divider {
        background: var(--border);
    }

    .bi-filter-title {
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 4px;
        font-family: var(--font-sans) !important;
    }

    .donut-title {
        color: var(--ink-mid);
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin: 8px 0;
        text-align: center;
        font-family: var(--font-sans) !important;
    }

    .chart-heading-title {
        color: var(--ink);
        font-size: 15px;
        font-weight: 800;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        margin: 0;
        font-family: var(--font-sans) !important;
    }

    .chart-heading-metric {
        display: inline-flex;
        align-items: center;
        margin-top: 6px;
        padding: 3px 10px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        font-size: 12px;
        font-weight: 700;
    }

    .news-panel-title {
        color: var(--ink);
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 0 0 10px;
        font-family: var(--font-sans) !important;
    }

    .news-item {
        padding: 9px 0;
        border-top: 1px solid var(--border);
    }
    .news-item:first-of-type { border-top: none; padding-top: 0; }

    .news-link {
        display: block;
        color: #ffffff !important;
        font-size: 13px;
        font-weight: 600;
        line-height: 1.4;
        text-decoration: none;
        margin-bottom: 3px;
    }
    .news-link:hover { text-decoration: underline; }
    .news-meta { color: var(--muted); font-size: 11px; }

    /* ── pills / pills active ────────────────────────────────────────── */
    [data-testid="stBaseButton-pillsActive"] {
        background: #4ecdc4 !important;
        border-color: #4ecdc4 !important;
        color: #1c1c1e !important;
    }
    [data-testid="stBaseButton-pills"] {
        background: var(--bg-card) !important;
        border-color: var(--border-mid) !important;
        color: var(--ink-mid) !important;
    }
</style>
"""

def render_header() -> None:
    m = metrics()
    st.markdown(
        f"""
        <div class="crm-hero">
            <div class="crm-hero-text">
                <div class="crm-eyebrow">&#9679; Mercado Cerâmico</div>
                <h1>360 Inteligência de Mercado</h1>
                <p>Clientes, produção, produtos, indicadores e inteligência de mercado em um único painel.</p>
            </div>
            <div class="crm-hero-stats">
                <div class="crm-hero-stat">
                    <div class="crm-hero-stat-val">{m['empresas']}</div>
                    <div class="crm-hero-stat-lbl">Clientes</div>
                </div>
                <div class="crm-hero-stat">
                    <div class="crm-hero-stat-val">{m['produtos']}</div>
                    <div class="crm-hero-stat-lbl">Produtos</div>
                </div>
                <div class="crm-hero-stat">
                    <div class="crm-hero-stat-val">{m['interacoes']}</div>
                    <div class="crm-hero-stat-lbl">Interações</div>
                </div>
                <div class="crm-hero-stat">
                    <div class="crm-hero-stat-val">{m['acoes']}</div>
                    <div class="crm-hero-stat-lbl">Próx. Ações</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: int | str, note: str) -> None:
    st.markdown(
        f"""
        <div class="crm-metric-card">
            <div class="crm-metric-label">{safe_html(label)}</div>
            <div class="crm-metric-value">{safe_html(value)}</div>
            <div class="crm-metric-note">{safe_html(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )





def render_metrics() -> None:
    empresas = list_empresas()
    if empresas.empty:
        total_clientes = 0
        capacidade_total = 0
        producao_total = 0
        polido_total = 0
    else:
        for col in ["capacidade_m2", "producao_m2", "producao_polido_m2"]:
            empresas[col] = pd.to_numeric(empresas[col], errors="coerce").fillna(0)
        total_clientes = len(empresas)
        capacidade_total = empresas["capacidade_m2"].sum()
        producao_total = empresas["producao_m2"].sum()
        polido_total = empresas["producao_polido_m2"].sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Clientes", total_clientes, "Base total de clientes")
    with c2:
        metric_card("Capacidade instalada", f"{format_quantity(capacidade_total)} m²", "Mercado total mapeado")
    with c3:
        metric_card("Produção atual", f"{format_quantity(producao_total)} m²", "Produção total cadastrada")
    with c4:
        metric_card("Produção polido", f"{format_quantity(polido_total)} m²", "Volume polido registrado")



def fetch_market_snapshot() -> dict[str, object]:
    snap = fetch_radar_economico()
    return {
        "usd_brl": snap.get("usd_brl"),
        "usd_brl_change": snap.get("usd_brl_change"),
        "wti_usd": snap.get("wti_usd"),
        "wti_change": snap.get("wti_change"),
        "updated_at": snap.get("updated_at"),
    }


def market_tile(title: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="bi-kpi">
            <div class="bi-kpi-label">{safe_html(title)}</div>
            <div class="bi-kpi-value">{safe_html(value)}</div>
            <div class="crm-metric-note">{safe_html(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_news_block(title: str, query: str) -> None:
    news_items = fetch_news_categoria(query, limit=3)

    st.markdown(f'<div class="news-panel-title">{safe_html(title)}</div>', unsafe_allow_html=True)

    if not news_items:
        st.info("Não foi possível atualizar este bloco agora.")
        return

    for item in news_items:
        source = item["source"] or "Fonte pública"
        st.markdown(
            f"""
            <div class="news-item">
                <a class="news-link" href="{safe_url(item['link'])}" target="_blank" rel="noopener noreferrer">{safe_html(item['title'])}</a>
                <div class="news-meta">{safe_html(source)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def chart_card(title: str, subtitle: str = "", metric: str | None = None) -> None:
    metric_html = f'<div class="chart-heading-metric">{safe_html(metric)}</div>' if metric else ""
    st.markdown(
        f"""
        <div class="chart-heading">
            <div class="chart-heading-title">{safe_html(title)}</div>
            {metric_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def donut_title(title: str) -> None:
    st.markdown(f'<div class="donut-title">{safe_html(title)}</div>', unsafe_allow_html=True)


def reset_bi_filters() -> None:
    st.session_state["bi_regiao_select"] = "Todas as regiões"
    st.session_state["bi_tipologia_select"] = "Todas as tipologias"
    st.session_state["bi_cliente_select"] = "Todos os clientes"
    st.session_state["bi_produto_select"] = "Todos os produtos"


def render_chip_filter(label: str, options: list[str], state_key: str) -> list[str]:
    options = [clean_text(option).strip() for option in options if clean_text(option).strip()]
    selected = st.session_state.get(state_key, options)
    selected = [option for option in selected if option in options]
    if not selected and state_key not in st.session_state:
        selected = options
    st.session_state[state_key] = selected

    st.markdown(f'<div class="bi-filter-title">{label}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="bi-filter-help">Clique para filtrar. {len(selected)} de {len(options)} ativos.</div>',
        unsafe_allow_html=True,
    )

    if not options:
        st.caption("Sem opções cadastradas.")
        return []

    selected = st.pills(
        label,
        options,
        selection_mode="multi",
        default=selected,
        key=f"{state_key}_pills",
        label_visibility="collapsed",
    )
    selected = selected or []
    st.session_state[state_key] = selected

    return selected



def style_bar_labels(fig):
    fig.update_traces(
        textposition="outside",
        textfont=dict(color="#f2f2f7", size=12, family="Inter, Aptos, Helvetica Neue, sans-serif"),
        cliponaxis=False,
        marker_line_width=1,
        marker_line_color="rgba(255,255,255,0.08)",
    )
    fig.update_xaxes(
        automargin=True,
        rangemode="tozero",
        constrain="domain",
        showgrid=False,
        showticklabels=False,
        zeroline=False,
        title="",
    )
    fig.update_yaxes(
        automargin=True,
        tickfont=dict(color="#aeaeb2", size=12),
    )
    fig.update_layout(
        margin=dict(l=8, r=52, t=18, b=18),
        xaxis=dict(domain=[0.0, 0.78]),
    )
    return fig


def empresa_form(prefix: str, empresa=None) -> dict[str, object]:
    tecnico_names, tecnico_map = tecnico_options()
    tecnico_choices = ["Sem responsável"] + tecnico_names
    current_tecnico = "Sem responsável"
    if empresa and empresa["tecnico_id"]:
        for name, tecnico_id in tecnico_map.items():
            if tecnico_id == empresa["tecnico_id"]:
                current_tecnico = name
                break

    c1, c2 = st.columns(2)
    with c1:
        nome = st.text_input("Cliente", value=clean_text(empresa["nome"] if empresa else ""), key=f"{prefix}_nome")
        segmento_atual = clean_text(empresa["segmento"] if empresa else "Ceramica")
        segmento_opcoes = ["Ceramica", "Colorificio", "Outro"]
        segmento = st.selectbox(
            "Seguimento",
            segmento_opcoes,
            index=segmento_opcoes.index(segmento_atual) if segmento_atual in segmento_opcoes else 0,
            key=f"{prefix}_segmento",
        )
        tipologia_atual = clean_text(empresa["tipologia"] if empresa else "Porcelanato")
        tipologia = st.selectbox(
            "Tipologia",
            TIPOLOGIAS,
            index=TIPOLOGIAS.index(tipologia_atual) if tipologia_atual in TIPOLOGIAS else 0,
            key=f"{prefix}_tipologia",
        )
        produtos_pesquisados = st.number_input(
            "Produtos pesquisados",
            min_value=0,
            step=1,
            value=int(empresa["produtos_pesquisados"] or 0) if empresa else 0,
            key=f"{prefix}_produtos_pesquisados",
        )
        regiao = st.text_input("Região", value=clean_text(empresa["regiao"] if empresa else ""), key=f"{prefix}_regiao")
        cidade = st.text_input("Cidade", value=clean_text(empresa["cidade"] if empresa else ""), key=f"{prefix}_cidade")
        estado = st.text_input("Estado", value=clean_text(empresa["estado"] if empresa else ""), key=f"{prefix}_estado")
    with c2:
        status_atual = empresa["status"] if empresa and empresa["status"] in STATUS_CLIENTE else "Prospect"
        prioridade_atual = empresa["prioridade"] if empresa and empresa["prioridade"] in PRIORIDADES else "Media"
        status = st.selectbox("Status", STATUS_CLIENTE, index=STATUS_CLIENTE.index(status_atual), key=f"{prefix}_status")
        prioridade = st.selectbox("Prioridade", PRIORIDADES, index=PRIORIDADES.index(prioridade_atual), key=f"{prefix}_prioridade")
        tecnico_nome = st.selectbox(
            "Técnico responsável",
            tecnico_choices,
            index=tecnico_choices.index(current_tecnico),
            key=f"{prefix}_tecnico",
        )
        contato = st.text_input("Contato principal", value=clean_text(empresa["contato_principal"] if empresa else ""), key=f"{prefix}_contato")
        telefone = st.text_input("Telefone", value=clean_text(empresa["telefone"] if empresa else ""), key=f"{prefix}_telefone")
        email = st.text_input("E-mail", value=clean_text(empresa["email"] if empresa else ""), key=f"{prefix}_email")

    st.markdown("### Informações de produção do cliente")
    p1, p2, p3 = st.columns(3)
    capacidade_text = p1.text_input(
        "Capacidade instalada (m²)",
        value=format_br_number(empresa["capacidade_m2"] if empresa else 0, 2),
        help="Exemplo: 1.500.000,00",
        key=f"{prefix}_capacidade",
    )
    producao_text = p2.text_input(
        "Produção m²",
        value=format_br_number(empresa["producao_m2"] if empresa else 0, 2),
        help="Exemplo: 600.000,00",
        key=f"{prefix}_producao",
    )
    polido_text = p3.text_input(
        "Produção m² polido",
        value=format_br_number(empresa["producao_polido_m2"] if empresa else 0, 2),
        help="Exemplo: 150.000,00",
        key=f"{prefix}_polido",
    )

    observacoes = st.text_area("Observações", value=clean_text(empresa["observacoes"] if empresa else ""), height=120, key=f"{prefix}_obs")
    return {
        "nome": clean_text(nome).strip(),
        "segmento": clean_text(segmento).strip() or None,
        "tipologia": clean_text(tipologia).strip() or None,
        "produtos_pesquisados": produtos_pesquisados,
        "capacidade_m2": parse_br_number(capacidade_text),
        "producao_m2": parse_br_number(producao_text),
        "producao_polido_m2": parse_br_number(polido_text),
        "regiao": clean_text(regiao).strip() or None,
        "cidade": clean_text(cidade).strip() or None,
        "estado": clean_text(estado).strip() or None,
        "status": status,
        "prioridade": prioridade,
        "tecnico_id": tecnico_map.get(tecnico_nome) if tecnico_nome != "Sem responsável" else None,
        "contato_principal": clean_text(contato).strip() or None,
        "telefone": clean_text(telefone).strip() or None,
        "email": clean_text(email).strip() or None,
        "observacoes": clean_text(observacoes).strip() or None,
    }


def render_empresas() -> None:
    section_title("Informações do Cliente", "Cadastro principal do cliente, dados produtivos e atualização comercial em um único fluxo.")
    modo = st.radio("Ação", ["Cadastrar", "Editar"], horizontal=True)

    if modo == "Cadastrar":
        with st.form("empresa_nova_form"):
            payload = empresa_form("nova")
            submitted = st.form_submit_button("Cadastrar cliente", use_container_width=True)
        if submitted:
            try:
                empresa_id = save_empresa(payload)
                st.session_state["selected_empresa_id"] = empresa_id
                st.success("Cliente cadastrado. Ele já ficou selecionado para a aba de produtos.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Já existe um cliente com esse nome.")
            except ValueError as exc:
                st.error(str(exc))
        empresa_id = st.session_state.get("selected_empresa_id")
        if empresa_id:
            empresa = get_empresa(empresa_id)
            if empresa is not None:
                st.divider()
                render_produtos_for_empresa(int(empresa_id), clean_text(empresa["nome"]))
        return

    empresas = list_empresas(search=st.text_input("Buscar empresa"))
    if empresas.empty:
        st.info("Nenhum cliente cadastrado.")
        return

    options = {f"{row['nome']} | {row['status']}": int(row["id"]) for _, row in empresas.iterrows()}
    option_labels = list(options.keys())
    option_ids = list(options.values())
    selected_id = st.session_state.get("selected_empresa_id")
    selected_index = option_ids.index(selected_id) if selected_id in option_ids else 0
    if st.session_state.get("empresa_edit_select") not in option_labels:
        st.session_state["empresa_edit_select"] = option_labels[selected_index]
    selected = st.selectbox("Cliente", option_labels, key="empresa_edit_select")
    empresa_id = options[selected]
    st.session_state["selected_empresa_id"] = empresa_id
    empresa = get_empresa(empresa_id)
    st.caption("As informações do cliente e os produtos agora ficam no mesmo fluxo de cadastro.")
    atualizado_em = clean_text(empresa["atualizado_em"]) if empresa else ""
    if atualizado_em:
        data_formatada = atualizado_em
        try:
            data_formatada = datetime.strptime(atualizado_em, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        except ValueError:
            pass
        st.info(f"Última atualização do cliente: {data_formatada}")
    st.dataframe(empresas, use_container_width=True, hide_index=True, height=260)

    with st.form(f"empresa_editar_{empresa_id}"):
        payload = empresa_form(f"editar_{empresa_id}", empresa)
        save_col, delete_col = st.columns(2)
        submitted = save_col.form_submit_button("Salvar alterações", use_container_width=True)
        delete_submitted = delete_col.form_submit_button("Apagar cliente", use_container_width=True)

    if submitted:
        try:
            saved_id = save_empresa(payload, empresa_id=empresa_id)
            st.session_state["selected_empresa_id"] = saved_id
            st.success("Cliente atualizado e mantido selecionado para produtos.")
            st.rerun()
        except sqlite3.IntegrityError:
            st.error("Já existe outro cliente com esse nome.")

    if delete_submitted:
        st.session_state["delete_client_id"] = empresa_id
        st.session_state["delete_client_name"] = empresa["nome"]
        st.rerun()

    if st.session_state.get("delete_client_id") == empresa_id:
        st.warning(
            f"Tem certeza que deseja apagar `{st.session_state.get('delete_client_name')}`? "
            "Isso também remove produtos e interações desse cliente."
        )
        confirm_col, cancel_col = st.columns(2)
        if confirm_col.button("Confirmar exclusão", use_container_width=True):
            delete_empresa(empresa_id)
            st.session_state.pop("delete_client_id", None)
            st.session_state.pop("delete_client_name", None)
            if st.session_state.get("selected_empresa_id") == empresa_id:
                st.session_state.pop("selected_empresa_id", None)
            st.success("Cliente apagado.")
            st.rerun()
        if cancel_col.button("Cancelar exclusão", use_container_width=True):
            st.session_state.pop("delete_client_id", None)
            st.session_state.pop("delete_client_name", None)
            st.rerun()

    st.divider()
    render_produtos_for_empresa(empresa_id, clean_text(empresa["nome"]))


def get_produtos_opcoes() -> list[str]:
    produtos_banco = list_produtos_cliente()
    if produtos_banco.empty:
        return []
    return sorted(
        {
            clean_text(produto).strip()
            for produto in produtos_banco["produto"].tolist()
            if clean_text(produto).strip()
        }
    )


def render_produtos_for_empresa(empresa_id: int, empresa_nome: str) -> None:
    section_title("Produtos do Cliente", f"Cadastro e edição de produtos vinculados a {empresa_nome}.")

    c1, c2, c3 = st.columns([1, 1, 1])
    if c1.button("Adicionar produto", key=f"add_prod_{empresa_id}", use_container_width=True):
        st.session_state["show_product_form"] = True
    if c2.button("Fechar formulário", key=f"close_prod_{empresa_id}", use_container_width=True):
        st.session_state["show_product_form"] = False

    produtos = list_produtos_cliente(empresa_id=empresa_id)
    produtos_opcoes = get_produtos_opcoes()
    c3.metric("Produtos cadastrados", len(produtos))

    if st.session_state.get("show_product_form", False):
        with st.form(f"produto_cliente_form_{empresa_id}"):
            st.markdown("#### Produto, quantidade e valor")
            p1, p2, p3 = st.columns(3)
            if produtos_opcoes:
                produto_selecionado = p1.selectbox(
                    "Produto",
                    ["Cadastrar novo produto"] + produtos_opcoes,
                    help="Clique e digite para pesquisar produtos já cadastrados, como NANO.",
                    key=f"produto_select_{empresa_id}",
                )
                produto_novo = p1.text_input(
                    "Novo produto",
                    placeholder="Use somente se o produto ainda não estiver na lista",
                    disabled=produto_selecionado != "Cadastrar novo produto",
                    key=f"produto_novo_{empresa_id}",
                )
                produto = produto_novo if produto_selecionado == "Cadastrar novo produto" else produto_selecionado
            else:
                produto = p1.text_input("Produto", placeholder="Ex.: Nano, CMC, Plastificante", key=f"produto_nome_{empresa_id}")
            consumo_text = p2.text_input("Quantidade / consumo (kg)", placeholder="Ex.: 1.000,00", key=f"produto_consumo_{empresa_id}")
            valor_text = p3.text_input("Valor unitário (R$)", placeholder="Ex.: 6,50", key=f"produto_valor_novo_{empresa_id}")
            fornecedor = st.text_input("Fornecedor atual", placeholder="Ex.: fornecedor usado hoje", key=f"produto_fornecedor_novo_{empresa_id}")
            observacoes = st.text_area("Observações", height=90, key=f"produto_obs_novo_{empresa_id}")
            submitted = st.form_submit_button("Salvar produto", use_container_width=True)

        if submitted:
            try:
                consumo = parse_br_number(consumo_text)
                valor = parse_br_number(valor_text)
                add_produto_cliente(
                    {
                        "empresa_id": empresa_id,
                        "produto": produto,
                        "seguimento": None,
                        "tipologia": None,
                        "produtos_pesquisados": None,
                        "consumo_kg": consumo,
                        "preco_medio": valor,
                        "faturamento": consumo * valor,
                        "capacidade_m2": None,
                        "producao_m2": None,
                        "producao_polido_m2": None,
                        "fornecedor_atual": clean_text(fornecedor).strip() or None,
                        "observacoes": clean_text(observacoes).strip() or None,
                    }
                )
                st.session_state["show_product_form"] = False
                st.success("Produto salvo para o cliente.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    if produtos.empty:
        st.info("Nenhum produto cadastrado ainda. Clique em `Adicionar produto` para começar.")
        return

    tabela = produtos.copy()
    tabela["preco_medio"] = tabela["preco_medio"].fillna(0)
    tabela["consumo_kg"] = tabela["consumo_kg"].fillna(0)
    tabela["faturamento"] = tabela["consumo_kg"] * tabela["preco_medio"]
    tabela["consumo_kg"] = tabela["consumo_kg"].map(lambda value: f"{format_quantity(value)} KG")
    tabela["preco_medio"] = tabela["preco_medio"].map(format_brl)
    tabela["faturamento"] = tabela["faturamento"].map(format_brl)
    tabela = tabela.rename(
        columns={
            "produto": "Produto",
            "consumo_kg": "Quantidade",
            "preco_medio": "Valor",
            "faturamento": "Faturamento",
            "fornecedor_atual": "Fornecedor atual",
        }
    )[["Produto", "Quantidade", "Valor", "Faturamento", "Fornecedor atual"]]
    st.dataframe(tabela, use_container_width=True, hide_index=True, height=320)

    edit_state_key = f"edit_products_table_{empresa_id}"
    if edit_state_key not in st.session_state:
        st.session_state[edit_state_key] = False

    edit_col, cancel_col = st.columns(2)
    if edit_col.button("Editar tabela", key=f"edit_table_btn_{empresa_id}", use_container_width=True):
        st.session_state[edit_state_key] = True
    if st.session_state[edit_state_key]:
        if cancel_col.button("Fechar edição", key=f"cancel_table_btn_{empresa_id}", use_container_width=True):
            st.session_state[edit_state_key] = False
            st.rerun()

        st.markdown("### Editar produtos na tabela")
        st.caption("Altere os campos diretamente. Para apagar, marque a coluna `Apagar` e salve.")

        edit_df = produtos.copy()[["id", "produto", "consumo_kg", "preco_medio", "fornecedor_atual", "observacoes"]]
        edit_df = edit_df.rename(
            columns={
                "id": "ID",
                "produto": "Produto",
                "consumo_kg": "Quantidade (KG)",
                "preco_medio": "Valor (R$)",
                "fornecedor_atual": "Fornecedor atual",
                "observacoes": "Observações",
            }
        )
        edit_df["Apagar"] = False

        with st.form(f"editar_tabela_produtos_{empresa_id}"):
            edited_df = st.data_editor(
                edit_df,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                column_config={
                    "ID": st.column_config.NumberColumn("ID", disabled=True),
                    "Produto": st.column_config.TextColumn("Produto", required=True),
                    "Quantidade (KG)": st.column_config.NumberColumn("Quantidade (KG)", format="%.0f", min_value=0.0),
                    "Valor (R$)": st.column_config.NumberColumn("Valor (R$)", format="%.2f", min_value=0.0),
                    "Fornecedor atual": st.column_config.TextColumn("Fornecedor atual"),
                    "Observações": st.column_config.TextColumn("Observações"),
                    "Apagar": st.column_config.CheckboxColumn("Apagar"),
                },
                disabled=["ID"],
                key=f"editor_produtos_{empresa_id}",
            )
            salvar_tabela = st.form_submit_button("Salvar alterações da tabela", use_container_width=True)

        if salvar_tabela:
            try:
                for _, row in edited_df.iterrows():
                    produto_id = int(row["ID"])
                    if bool(row.get("Apagar", False)):
                        delete_produto_cliente(produto_id)
                        continue

                    quantidade = float(row.get("Quantidade (KG)") or 0)
                    valor = float(row.get("Valor (R$)") or 0)
                    update_produto_cliente(
                        produto_id,
                        {
                            "produto": clean_text(row.get("Produto")).strip(),
                            "consumo_kg": quantidade,
                            "preco_medio": valor,
                            "faturamento": quantidade * valor,
                            "fornecedor_atual": clean_text(row.get("Fornecedor atual")).strip() or None,
                            "observacoes": clean_text(row.get("Observações")).strip() or None,
                        },
                    )
                st.success("Tabela de produtos atualizada.")
                st.session_state[edit_state_key] = False
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def render_produtos() -> None:
    st.subheader("Produtos, Quantidades e Produção")
    empresas = list_empresas()
    if empresas.empty:
        st.info("Cadastre um cliente antes de registrar produtos.")
        return

    empresa_map = {row["nome"]: int(row["id"]) for _, row in empresas.iterrows()}
    empresa_names = list(empresa_map.keys())
    selected_id = st.session_state.get("selected_empresa_id")
    selected_name = next((name for name, empresa_id in empresa_map.items() if empresa_id == selected_id), empresa_names[0])
    if st.session_state.get("produtos_cliente_select") != selected_name:
        st.session_state["produtos_cliente_select"] = selected_name
    selected_filter = st.selectbox(
        "Cliente",
        empresa_names,
        key="produtos_cliente_select",
        help="Esse cliente vem automaticamente da aba Informações do Cliente.",
    )
    empresa_id = empresa_map[selected_filter]
    st.session_state["selected_empresa_id"] = empresa_id
    render_produtos_for_empresa(empresa_id, selected_filter)


def render_tecnicos() -> None:
    left, right = st.columns([0.8, 1.2])
    with left:
        st.subheader("Novo técnico")
        with st.form("tecnico_form"):
            nome = st.text_input("Nome")
            email = st.text_input("E-mail")
            telefone = st.text_input("Telefone")
            submitted = st.form_submit_button("Cadastrar técnico", use_container_width=True)
        if submitted:
            try:
                add_tecnico(nome, email, telefone)
                st.success("Técnico cadastrado.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Já existe um técnico com esse nome.")
            except ValueError as exc:
                st.error(str(exc))
    with right:
        st.subheader("Técnicos cadastrados")
        tecnicos = list_tecnicos()
        if tecnicos.empty:
            st.info("Nenhum técnico cadastrado.")
        else:
            st.dataframe(tecnicos, use_container_width=True, hide_index=True, height=360)


def render_interacoes() -> None:
    empresas = list_empresas()
    tecnicos = list_tecnicos()
    if empresas.empty:
        st.info("Cadastre uma empresa antes de registrar interações.")
        return
    if tecnicos.empty:
        st.info("Cadastre um técnico antes de registrar interações.")
        return

    empresa_map = {row["nome"]: int(row["id"]) for _, row in empresas.iterrows()}
    tecnico_map = {row["nome"]: int(row["id"]) for _, row in tecnicos.iterrows()}
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Nova interação")
        with st.form("interacao_form"):
            empresa_nome = st.selectbox("Empresa", list(empresa_map.keys()))
            tecnico_nome = st.selectbox("Técnico", list(tecnico_map.keys()))
            data_interacao = st.date_input("Data", value=date.today())
            tipo = st.selectbox("Tipo", TIPOS_INTERACAO)
            titulo = st.text_input("Título")
            descricao = st.text_area("Descrição", height=120)
            proxima_acao = st.text_input("Próxima ação")
            data_proxima = st.date_input("Data da próxima ação", value=None)
            c1, c2, c3 = st.columns(3)
            capacidade_text = c1.text_input("Capacidade m²", placeholder="Ex.: 1.500.000,00")
            producao_text = c2.text_input("Produção m²", placeholder="Ex.: 600.000,00")
            consumo_text = c3.text_input("Consumo kg", placeholder="Ex.: 1.000,00")
            submitted = st.form_submit_button("Salvar interação", use_container_width=True)
        if submitted:
            try:
                add_interacao(
                    {
                        "empresa_id": empresa_map[empresa_nome],
                        "tecnico_id": tecnico_map[tecnico_nome],
                        "data": str(data_interacao),
                        "tipo": tipo,
                        "titulo": titulo.strip(),
                        "descricao": descricao.strip() or None,
                        "proxima_acao": proxima_acao.strip() or None,
                        "data_proxima_acao": str(data_proxima) if data_proxima else None,
                        "capacidade_m2": parse_br_number(capacidade_text),
                        "producao_m2": parse_br_number(producao_text),
                        "consumo_kg": parse_br_number(consumo_text),
                    }
                )
                st.success("Interação salva.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    with right:
        st.subheader("Histórico")
        interacoes = list_interacoes(limit=50)
        if interacoes.empty:
            st.info("Nenhuma interação cadastrada.")
        else:
            st.dataframe(interacoes, use_container_width=True, hide_index=True, height=520)


def render_bi() -> None:
    section_title("Análise de Mercado", "Leitura executiva da base do CRM com foco em produção, consumo, faturamento e share.")
    bi_kpi_container = st.container()

    empresas = list_empresas()
    produtos = list_produtos_cliente(limit=5000)
    if empresas.empty:
        st.info("Cadastre clientes para liberar os indicadores do BI.")
        return

    empresas = empresas.copy()
    produtos = produtos.copy()
    numeric_empresa_cols = ["capacidade_m2", "producao_m2", "producao_polido_m2", "produtos_pesquisados"]
    for col in numeric_empresa_cols:
        empresas[col] = pd.to_numeric(empresas[col], errors="coerce").fillna(0)

    if not produtos.empty:
        produtos["consumo_kg"] = pd.to_numeric(produtos["consumo_kg"], errors="coerce").fillna(0)
        produtos["preco_medio"] = pd.to_numeric(produtos["preco_medio"], errors="coerce").fillna(0)
        produtos["faturamento"] = produtos["consumo_kg"] * produtos["preco_medio"]

    regioes = sorted([value for value in empresas["regiao"].dropna().unique().tolist() if clean_text(value).strip()])
    tipologias = sorted([value for value in empresas["tipologia"].dropna().unique().tolist() if clean_text(value).strip()])
    clientes = sorted([value for value in empresas["nome"].dropna().unique().tolist() if clean_text(value).strip()])

    regiao_sel = st.session_state.get("bi_regiao_select", "Todas as regiões")
    tipologia_sel = st.session_state.get("bi_tipologia_select", "Todas as tipologias")
    cliente_sel = st.session_state.get("bi_cliente_select", "Todos os clientes")
    produto_sel = st.session_state.get("bi_produto_select", "Todos os produtos")
    produtos_opcoes_topo = sorted(
        {
            clean_text(produto).strip()
            for produto in produtos["produto"].tolist()
            if clean_text(produto).strip()
        }
    ) if not produtos.empty else []

    f1, f2, f3, f4 = st.columns([1, 1, 1.2, 1.2])
    with f1:
        st.markdown('<div class="bi-filter-title">Região</div>', unsafe_allow_html=True)
        regiao_sel = st.selectbox(
            "Região",
            ["Todas as regiões"] + regioes,
            key="bi_regiao_select",
            label_visibility="collapsed",
        )
    with f2:
        st.markdown('<div class="bi-filter-title">Tipologia</div>', unsafe_allow_html=True)
        tipologia_sel = st.selectbox(
            "Tipologia",
            ["Todas as tipologias"] + tipologias,
            key="bi_tipologia_select",
            label_visibility="collapsed",
        )
    with f3:
        st.markdown('<div class="bi-filter-title">Cliente</div>', unsafe_allow_html=True)
        cliente_sel = st.selectbox(
            "Cliente",
            ["Todos os clientes"] + clientes,
            key="bi_cliente_select",
            label_visibility="collapsed",
        )
    with f4:
        st.markdown('<div class="bi-filter-title">Produto</div>', unsafe_allow_html=True)
        produto_sel = st.selectbox(
            "Produto",
            ["Todos os produtos"] + produtos_opcoes_topo,
            key="bi_produto_select",
            label_visibility="collapsed",
        )
    st.button(
        "Resetar filtros",
        key="bi_reset_filters",
        use_container_width=True,
        on_click=reset_bi_filters,
    )

    filtradas_base = empresas.copy()
    if regiao_sel != "Todas as regiões":
        filtradas_base = filtradas_base[filtradas_base["regiao"] == regiao_sel]
    if tipologia_sel != "Todas as tipologias":
        filtradas_base = filtradas_base[filtradas_base["tipologia"] == tipologia_sel]

    produtos_escopo = produtos[produtos["cliente"].isin(filtradas_base["nome"])] if not produtos.empty else produtos
    if produto_sel != "Todos os produtos" and not produtos_escopo.empty:
        produtos_escopo = produtos_escopo[produtos_escopo["produto"] == produto_sel]

    filtradas = filtradas_base.copy()
    if cliente_sel != "Todos os clientes":
        filtradas = filtradas[filtradas["nome"] == cliente_sel]

    produtos_filtrados = produtos_escopo[produtos_escopo["cliente"].isin(filtradas["nome"])] if not produtos_escopo.empty else produtos_escopo

    total_clientes = len(filtradas)
    capacidade_total = filtradas["capacidade_m2"].sum()
    producao_total = filtradas["producao_m2"].sum()
    polido_total = filtradas["producao_polido_m2"].sum()
    consumo_total = produtos_filtrados["consumo_kg"].sum() if not produtos_filtrados.empty else 0
    faturamento_total = produtos_filtrados["faturamento"].sum() if not produtos_filtrados.empty else 0
    ocupacao_pct = producao_total / capacidade_total if capacidade_total else 0

    with bi_kpi_container:
        m1, m2, m3 = st.columns(3)
        with m1:
            kpi_card("% Ocupação", f"{ocupacao_pct:.1%}")
        with m2:
            kpi_card("Capacidade instalada", f"{format_quantity(capacidade_total)} m²")
        with m3:
            kpi_card("Produção atual", f"{format_quantity(producao_total)} m²")

        m4, m5, m6 = st.columns(3)
        with m4:
            kpi_card("Produção polido atual", f"{format_quantity(polido_total)} m²")
        with m5:
            kpi_card("Consumo de produtos", f"{format_quantity(consumo_total)} KG")
        with m6:
            kpi_card("Faturamento de produtos", format_brl(faturamento_total))

    st.markdown('<div class="crm-subtle-divider"></div>', unsafe_allow_html=True)

    col_producao, col_mix, col_fat_regiao, col_share = st.columns([1, 1, 1, 1])
    with col_producao:
        donut_title("Produção por Região")
        total_producao_mercado = filtradas_base["producao_m2"].sum()
        regiao_df = (
            filtradas.assign(regiao=filtradas["regiao"].fillna("Não informado"))
            .groupby("regiao", as_index=False)["producao_m2"]
            .sum()
            .sort_values("producao_m2", ascending=False)
        )
        if regiao_df.empty or regiao_df["producao_m2"].sum() == 0:
            st.info("Sem produção cadastrada para este filtro.")
        else:
            if cliente_sel != "Todos os clientes" and total_producao_mercado > 0:
                producao_cliente = filtradas["producao_m2"].sum()
                comparativo_df = pd.DataFrame(
                    {
                        "grupo": [cliente_sel, "Mercado restante"],
                        "valor": [producao_cliente, max(total_producao_mercado - producao_cliente, 0)],
                    }
                )
                render_static_donut(
                    comparativo_df["grupo"],
                    comparativo_df["valor"],
                    f"{cliente_sel}<br>{(producao_cliente / total_producao_mercado):.1%}",
                )
            else:
                render_static_donut(
                    regiao_df["regiao"],
                    regiao_df["producao_m2"],
                    f"{format_quantity(regiao_df['producao_m2'].sum())}<br>m²",
                )

    with col_mix:
        donut_title("Mix por Tipologia")
        mix_base = filtradas_base.assign(tipologia=filtradas_base["tipologia"].fillna("Não informado"))
        mix_base = mix_base[mix_base["tipologia"].map(lambda value: clean_text(value).strip().lower()) != "colorificio"]
        mix_base["tipologia"] = mix_base["tipologia"].map(
            lambda value: "Outros" if clean_text(value).strip().lower() in {"monoporosa", "gres"} else value
        )
        value_col = "producao_m2" if mix_base["producao_m2"].sum() > 0 else "id"
        agg_func = "sum" if value_col == "producao_m2" else "count"
        mix_df = mix_base.groupby("tipologia", as_index=False).agg(valor=(value_col, agg_func))
        if mix_df.empty or mix_df["valor"].sum() == 0:
            st.info("Sem tipologia cadastrada para este filtro.")
        else:
            if cliente_sel != "Todos os clientes" and not filtradas.empty:
                tipologia_cliente = clean_text(filtradas["tipologia"].iloc[0]).strip() or "Não informado"
                tipologia_total = mix_df.loc[mix_df["tipologia"] == tipologia_cliente, "valor"].sum()
                comparativo_df = pd.DataFrame(
                    {
                        "grupo": [tipologia_cliente, "Demais tipologias"],
                        "valor": [tipologia_total, max(mix_df["valor"].sum() - tipologia_total, 0)],
                    }
                )
                render_static_donut(
                    comparativo_df["grupo"],
                    comparativo_df["valor"],
                    f"{tipologia_cliente}<br>{(tipologia_total / mix_df['valor'].sum()):.1%}",
                )
            else:
                render_static_donut(mix_df["tipologia"], mix_df["valor"], "Mix")

    with col_fat_regiao:
        donut_title("Faturamento por Região")
        if produtos_escopo.empty:
            st.info("Nenhum faturamento cadastrado para este filtro.")
        else:
            regiao_lookup = filtradas_base[["nome", "regiao"]].rename(columns={"nome": "cliente"})
            fat_regiao_base = produtos_escopo.merge(regiao_lookup, on="cliente", how="left")
            fat_regiao_df = (
                fat_regiao_base.assign(regiao=fat_regiao_base["regiao"].fillna("Não informado"))
                .groupby("regiao", as_index=False)["faturamento"]
                .sum()
                .sort_values("faturamento", ascending=False)
            )
            if fat_regiao_df.empty or fat_regiao_df["faturamento"].sum() == 0:
                st.info("Sem faturamento para dividir por região.")
            else:
                if cliente_sel != "Todos os clientes" and not filtradas.empty:
                    regiao_cliente = clean_text(filtradas["regiao"].iloc[0]).strip() or "Não informado"
                    faturamento_regiao = fat_regiao_df.loc[fat_regiao_df["regiao"] == regiao_cliente, "faturamento"].sum()
                    total_fat_mercado = fat_regiao_df["faturamento"].sum()
                    comparativo_df = pd.DataFrame(
                        {
                            "grupo": [regiao_cliente, "Demais regiões"],
                            "valor": [faturamento_regiao, max(total_fat_mercado - faturamento_regiao, 0)],
                        }
                    )
                    render_static_donut(
                        comparativo_df["grupo"],
                        comparativo_df["valor"],
                        f"{regiao_cliente}<br>{(faturamento_regiao / total_fat_mercado):.1%}",
                    )
                else:
                    render_static_donut(
                        fat_regiao_df["regiao"],
                        fat_regiao_df["faturamento"],
                        f"Total<br>{format_brl(fat_regiao_df['faturamento'].sum())}",
                    )

    with col_share:
        donut_title("Share Quimicer")
        if produtos_filtrados.empty or faturamento_total == 0:
            st.info("Sem faturamento cadastrado para calcular share.")
        else:
            share_base = produtos_filtrados.copy()
            if share_base.empty or share_base["faturamento"].sum() == 0:
                st.info("Sem faturamento para este produto.")
            else:
                share_base["Fornecedor"] = share_base["fornecedor_atual"].map(lambda value: clean_text(value).strip() or "Não informado")
                share_df = (
                    share_base.groupby("Fornecedor", as_index=False)["faturamento"]
                    .sum()
                    .sort_values("faturamento", ascending=False)
                )
                total_share = share_df["faturamento"].sum()
                fornecedores_upper = share_df["Fornecedor"].str.upper()
                quimicer_total = share_df.loc[fornecedores_upper.str.contains("QUIMICER", na=False), "faturamento"].sum()
                share_quimicer = quimicer_total / total_share if total_share else 0
                concorrentes_total = share_df.loc[~fornecedores_upper.str.contains("QUIMICER", na=False), "Fornecedor"].nunique()
                top_fornecedores = share_df.head(5).copy()
                outros_total = share_df.iloc[5:]["faturamento"].sum()
                if outros_total > 0:
                    top_fornecedores = pd.concat(
                        [top_fornecedores, pd.DataFrame([{"Fornecedor": "Outros", "faturamento": outros_total}])],
                        ignore_index=True,
                    )
                share_legend_order = ["PG QUIMICA", "Não informado", "QUIMICER", "LAMBRA", "MANCHESTER", "Outros"]
                top_fornecedores["legend_rank"] = top_fornecedores["Fornecedor"].map(
                    lambda value: share_legend_order.index(value) if value in share_legend_order else len(share_legend_order)
                )
                top_fornecedores = top_fornecedores.sort_values(["legend_rank", "Fornecedor"]).drop(columns=["legend_rank"])
                share_colors = {
                    "PG QUIMICA": "#4ecdc4",
                    "Não informado": "#6c6c70",
                    "QUIMICER": "#38b2aa",
                    "LAMBRA": "#8e8e93",
                    "MANCHESTER": "#aeaeb2",
                    "Outros": "#48484a",
                }
                render_static_donut(
                    top_fornecedores["Fornecedor"],
                    top_fornecedores["faturamento"],
                    f"Quimicer<br>{share_quimicer:.1%}",
                    colors=[share_colors.get(label, CHART_COLORS[index % len(CHART_COLORS)]) for index, label in enumerate(top_fornecedores["Fornecedor"])],
                )
                concorrentes_label = "concorrente" if concorrentes_total == 1 else "concorrentes"
                st.caption(f"Total de {int(concorrentes_total)} {concorrentes_label} no filtro atual.")

    left, right = st.columns([1, 1])
    with left:
        chart_card(
            "Consumo por Produto",
            "Ranking dos produtos pela quantidade cadastrada.",
            metric=f"Total {format_quantity(consumo_total)} KG",
        )
        if produtos_filtrados.empty:
            st.info("Nenhum produto cadastrado para os clientes filtrados.")
        else:
            consumo_df = (
                produtos_filtrados.assign(produto=produtos_filtrados["produto"].fillna("Não informado"))
                .groupby("produto", as_index=False)["consumo_kg"]
                .sum()
                .sort_values("consumo_kg", ascending=True)
                .tail(12)
            )
            fig = px.bar(
                consumo_df,
                x="consumo_kg",
                y="produto",
                orientation="h",
                text=consumo_df["consumo_kg"].map(lambda value: f"{format_quantity(value)} KG"),
                color="consumo_kg",
                color_continuous_scale=["#636366", "#38b2aa", "#4ecdc4"],
            )
            style_bar_labels(fig)
            max_value = consumo_df["consumo_kg"].max()
            fig.update_layout(showlegend=False, coloraxis_showscale=False, xaxis_title="", yaxis_title="")
            fig.update_xaxes(range=[0, max_value * 1.28 if max_value else 1])
            st.plotly_chart(style_chart(fig, height=430), use_container_width=True, config={"staticPlot": False, "displayModeBar": False, "scrollZoom": False})

    with right:
        chart_card(
            "Faturamento por Produto",
            "Quantidade x valor unitário dos produtos cadastrados.",
            metric=format_brl(faturamento_total),
        )
        if produtos_filtrados.empty:
            st.info("Nenhum produto cadastrado para os clientes filtrados.")
        else:
            faturamento_df = (
                produtos_filtrados.assign(produto=produtos_filtrados["produto"].fillna("Não informado"))
                .groupby("produto", as_index=False)["faturamento"]
                .sum()
                .sort_values("faturamento", ascending=True)
                .tail(12)
            )
            fig = px.bar(
                faturamento_df,
                x="faturamento",
                y="produto",
                orientation="h",
                text=faturamento_df["faturamento"].map(format_brl),
                color="faturamento",
                color_continuous_scale=["#636366", "#38b2aa", "#4ecdc4"],
            )
            style_bar_labels(fig)
            max_value = faturamento_df["faturamento"].max()
            fig.update_layout(showlegend=False, coloraxis_showscale=False, xaxis_title="", yaxis_title="")
            fig.update_xaxes(range=[0, max_value * 1.30 if max_value else 1])
            st.plotly_chart(style_chart(fig, height=430), use_container_width=True, config={"staticPlot": False, "displayModeBar": False, "scrollZoom": False})

    left, right = st.columns([1, 1])
    with left:
        chart_card("Top Clientes por Produção", "Clientes com maior produção atual cadastrada.")
        top_clientes = filtradas.sort_values("producao_m2", ascending=True).tail(12)
        if top_clientes.empty or top_clientes["producao_m2"].sum() == 0:
            st.info("Sem produção cadastrada para este filtro.")
        else:
            fig = px.bar(
                top_clientes,
                x="producao_m2",
                y="nome",
                orientation="h",
                text=top_clientes["producao_m2"].map(lambda value: f"{format_quantity(value)} m²"),
                color="producao_m2",
                color_continuous_scale=["#636366", "#38b2aa", "#4ecdc4"],
            )
            style_bar_labels(fig)
            max_value = top_clientes["producao_m2"].max()
            fig.update_layout(showlegend=False, coloraxis_showscale=False, xaxis_title="", yaxis_title="")
            fig.update_xaxes(range=[0, max_value * 1.24 if max_value else 1])
            st.plotly_chart(style_chart(fig, height=430), use_container_width=True, config={"staticPlot": False, "displayModeBar": False, "scrollZoom": False})

    with right:
        chart_card("Top Clientes por Faturamento")
        if produtos_filtrados.empty:
            st.info("Nenhum faturamento cadastrado para este filtro.")
        else:
            faturamento_cliente_df = (
                produtos_filtrados.assign(cliente=produtos_filtrados["cliente"].fillna("Não informado"))
                .groupby("cliente", as_index=False)["faturamento"]
                .sum()
                .sort_values("faturamento", ascending=True)
                .tail(12)
            )
            fig = px.bar(
                faturamento_cliente_df,
                x="faturamento",
                y="cliente",
                orientation="h",
                text=faturamento_cliente_df["faturamento"].map(format_brl),
                color="faturamento",
                color_continuous_scale=["#636366", "#38b2aa", "#4ecdc4"],
            )
            style_bar_labels(fig)
            max_value = faturamento_cliente_df["faturamento"].max()
            fig.update_layout(showlegend=False, coloraxis_showscale=False, xaxis_title="", yaxis_title="")
            fig.update_xaxes(range=[0, max_value * 1.30 if max_value else 1])
            st.plotly_chart(style_chart(fig, height=430), use_container_width=True, config={"staticPlot": False, "displayModeBar": False, "scrollZoom": False})



@st.fragment
def render_visao() -> None:
    section_title("Visão Geral", "Consulta rápida da carteira, histórico registrado e base atual do CRM.")
    snapshot = fetch_market_snapshot()

    st.markdown("### Radar Diário")
    t1, t2, t3 = st.columns(3)
    with t1:
        usd_value = format_brl(snapshot["usd_brl"]) if snapshot.get("usd_brl") else "--"
        usd_note = f"Variação {format_br_number(snapshot['usd_brl_change'], 2)}%" if snapshot.get("usd_brl_change") is not None else "Sem atualização"
        market_tile("Dólar comercial", usd_value, usd_note)
    with t2:
        oil_value = format_usd(snapshot["wti_usd"]) if snapshot.get("wti_usd") else "--"
        oil_note = f"Variação {format_br_number(snapshot['wti_change'], 2)}%" if snapshot.get("wti_change") is not None else "Sem atualização"
        market_tile("Petróleo WTI", oil_value, oil_note)
    with t3:
        market_tile("Atualizado em", snapshot.get("updated_at", "--"), "Dados públicos e notícias automáticas")

    n1, n2, n3, n4 = st.columns(4)
    with n1:
        render_news_block("Construção civil", "construcao civil mercado brasil")
    with n2:
        render_news_block("Gás e petróleo", "gas petroleo energia brasil")
    with n3:
        render_news_block("Economia e mercado", "economia brasil mercado financeiro")
    with n4:
        render_news_block("Transporte e logística", "transporte logistica frete brasil")


def _prewarm_cache() -> None:
    """Dispara o fetch do radar em background para que o cache já esteja pronto."""
    import threading
    from crm_app.inteligencia_mercado.data import fetch_radar_economico
    t = threading.Thread(target=fetch_radar_economico, daemon=True)
    t.start()


def run_app() -> None:
    ensure_schema()
    st.markdown(CSS, unsafe_allow_html=True)

    # pré-aquece radar em background sem travar o render inicial
    if "cache_warmed" not in st.session_state:
        st.session_state["cache_warmed"] = True
        _prewarm_cache()

    render_header()
    render_metrics()

    tab1, tab2, tab3 = st.tabs(
        ["Análise de Mercado", "Inteligência de Mercado", "Informações do Cliente"]
    )
    with tab1:
        render_bi()
        st.markdown('<div class="crm-subtle-divider"></div>', unsafe_allow_html=True)
        render_visao()
    with tab2:
        render_inteligencia_mercado()
    with tab3:
        render_empresas()

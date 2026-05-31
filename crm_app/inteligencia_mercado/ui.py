from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from crm_app.database import list_empresas, list_produtos_cliente
from crm_app.helpers import (
    CHART_COLORS,
    clean_text,
    format_br_number,
    format_brl,
    format_quantity,
    kpi_card,
    section_title,
    style_chart,
)
from crm_app.inteligencia_mercado.data import fetch_news_categoria, fetch_radar_economico
from crm_app.security import safe_html, safe_url

CSS_IM = """
<style>
    /* ── radar tiles ─────────────────────────────────────────────────── */
    .im-tile {
        background: var(--bg-card, #131d2e);
        border: 1px solid var(--border, rgba(255,255,255,0.07));
        border-radius: 16px;
        padding: 16px 18px 14px;
        box-shadow: var(--shadow-sm, 0 2px 8px rgba(0,0,0,0.4));
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        min-height: 100px;
        transition: transform 160ms ease, box-shadow 160ms ease;
        position: relative;
        overflow: hidden;
    }
    .im-tile:hover { transform: translateY(-2px); box-shadow: var(--shadow-md, 0 8px 24px rgba(0,0,0,0.5)); }

    .im-tile.up   { border-left: 3px solid #4ecdc4; }
    .im-tile.down { border-left: 3px solid #8e8e93; }
    .im-tile.flat { border-left: 3px solid #48484a; }

    .im-tile-label {
        color: var(--muted, #6b7a96);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .im-tile-value {
        color: var(--ink, #f0f4ff);
        font-size: clamp(18px, 1.6vw, 26px);
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.03em;
    }
    .im-tile-delta {
        font-size: 11px;
        font-weight: 700;
        margin-top: 8px;
        display: inline-flex;
        align-items: center;
        gap: 3px;
        padding: 2px 8px;
        border-radius: 999px;
    }
    .im-tile-delta.up   { background: rgba(78,205,196,0.15); color: #4ecdc4; }
    .im-tile-delta.down { background: rgba(142,142,147,0.15); color: #aeaeb2; }
    .im-tile-delta.flat { background: rgba(72,72,74,0.3);    color: #6c6c70; }

    /* ── nav cards ───────────────────────────────────────────────────── */
    .im-nav-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    .im-nav-wrap {
        position: relative;
    }
    .im-nav-card {
        background: #111111;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 18px 18px 16px;
        display: flex;
        flex-direction: column;
        gap: 7px;
        pointer-events: none;
        transition: all 160ms ease;
    }
    .im-nav-card.active {
        background: rgba(78,205,196,0.08);
        border-color: rgba(78,205,196,0.4);
        box-shadow: 0 4px 20px rgba(78,205,196,0.1);
    }
    .im-nav-icon { font-size: 22px; line-height: 1; }
    .im-nav-title {
        font-size: 12px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .im-nav-desc {
        font-size: 11px;
        color: #666666;
        line-height: 1.4;
        text-transform: none;
    }
    /* botão invisível sobreposto ao card via margin-top negativa */
    .im-nav-btn > div[data-testid="stButton"] > button {
        width: 100% !important;
        height: 110px !important;
        margin-top: -118px !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: transparent !important;
        cursor: pointer !important;
        border-radius: 16px !important;
        position: relative;
        z-index: 10;
    }
    .im-nav-btn > div[data-testid="stButton"] > button:hover {
        background: rgba(255,255,255,0.04) !important;
    }

    /* ── news ────────────────────────────────────────────────────────── */
    .im-news-title {
        color: var(--ink, #f0f4ff);
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.09em;
        margin: 0 0 10px;
        text-transform: uppercase;
    }
    .im-news-item {
        padding: 8px 0;
        border-top: 1px solid var(--border, rgba(255,255,255,0.07));
    }
    .im-news-item:first-of-type { border-top: none; padding-top: 0; }
    .im-news-link {
        display: block;
        color: #ffffff !important;
        font-size: 13px;
        font-weight: 600;
        line-height: 1.4;
        text-decoration: none;
        margin-bottom: 3px;
    }
    .im-news-link:hover { text-decoration: underline; color: #cccccc !important; }
    .im-news-meta { color: var(--muted, #6b7a96); font-size: 11px; }

    /* ── divider ─────────────────────────────────────────────────────── */
    .im-section-divider {
        width: 100%; height: 1px; border-radius: 99px;
        margin: 16px 0 20px;
        background: var(--border, rgba(255,255,255,0.07));
    }
</style>
"""

NEWS_CATEGORIAS = {
    "Ceramica": "ceramica revestimentos pisos porcelanato brasil",
    "Construção civil": "construcao civil mercado brasil",
    "Gas e energia": "gas natural energia petroleo brasil",
    "Quimica industrial": "quimica industrial insumos ceramica brasil",
    "Logistica": "transporte logistica frete brasil",
}


def _delta_html(value: float | None) -> str:
    if value is None:
        return '<span class="im-tile-delta flat">—</span>'
    sign = "▲" if value >= 0 else "▼"
    css = "up" if value >= 0 else "down"
    label = "+" if value >= 0 else ""
    return f'<span class="im-tile-delta {css}">{sign} {label}{format_br_number(value, 2)}%</span>'


def _tile(label: str, value: str, delta: float | None = None, note: str = "") -> None:
    trend = "up" if (delta or 0) > 0 else ("down" if (delta or 0) < 0 else "flat")
    note_html = f'<div style="color:#555;font-size:10px;margin-top:5px;letter-spacing:0.04em;text-transform:none">{safe_html(note)}</div>' if note else ""
    st.markdown(
        f"""
        <div class="im-tile {trend}">
            <div class="im-tile-label">{safe_html(label)}</div>
            <div class="im-tile-value">{safe_html(value)}</div>
            {_delta_html(delta)}
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _news_block(title: str, query: str) -> None:
    items = fetch_news_categoria(query, limit=5)
    st.markdown(f'<div class="im-news-title">{safe_html(title)}</div>', unsafe_allow_html=True)
    if not items:
        st.caption("Sem notícias no momento.")
        return
    for item in items:
        source = item["source"] or "Fonte pública"
        st.markdown(
            f"""
            <div class="im-news-item">
                <a class="im-news-link" href="{safe_url(item['link'])}" target="_blank" rel="noopener noreferrer">{safe_html(item['title'])}</a>
                <div class="im-news-meta">{safe_html(source)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _divider() -> None:
    st.markdown('<div class="im-section-divider"></div>', unsafe_allow_html=True)


# ── Bloco 1: Radar Econômico ──────────────────────────────────────────────────

@st.fragment
def render_radar_economico() -> None:
    section_title("Radar Econômico", "Últimos fechamentos e indicadores que impactam o custo de produção cerâmica.")
    snap = fetch_radar_economico()

    # ── linha 1: câmbio + petróleo ────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        val = f"R$ {format_br_number(snap['usd_brl'], 2)}" if snap.get("usd_brl") else "—"
        _tile("Dólar USD/BRL", val, snap.get("usd_brl_change"), note="Último fechamento disponível")
    with c2:
        val = f"R$ {format_br_number(snap['eur_brl'], 2)}" if snap.get("eur_brl") else "—"
        _tile("Euro EUR/BRL", val, snap.get("eur_brl_change"), note="Último fechamento disponível")
    with c3:
        val = f"US$ {format_br_number(snap['wti_usd'], 2)}" if snap.get("wti_usd") else "—"
        _tile("Petróleo WTI", val, snap.get("wti_change"), note="Barril — último fechamento")
    with c4:
        val = f"US$ {format_br_number(snap['brent_usd'], 2)}" if snap.get("brent_usd") else "—"
        _tile("Petróleo Brent", val, snap.get("brent_change"), note="Referência global — fechamento")

    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)

    # ── linha 2: macro Brasil ─────────────────────────────────────────
    c5, c6 = st.columns(2)
    with c5:
        val = f"{format_br_number(snap['incc_pct'], 2)}%" if snap.get("incc_pct") else "—"
        _tile("INCC Mensal", val, note="Construção civil — BCB")
    with c6:
        val = f"{format_br_number(snap['selic_pct'], 2)}% a.a." if snap.get("selic_pct") else "—"
        _tile("Selic", val, note="Taxa básica de juros")

    st.caption(
        f"Atualizado em: {snap.get('updated_at', '—')} · "
        "Fontes: AwesomeAPI/Frankfurter (câmbio), OilPriceAPI/Yahoo (petróleo), Banco Central do Brasil"
    )


# ── Bloco 2: Notícias por categoria ──────────────────────────────────────────

@st.fragment
def render_noticias() -> None:
    section_title("Monitor de Notícias", "Radar setorial filtrado por categoria. Clique na notícia para abrir a fonte.")

    categorias = list(NEWS_CATEGORIAS.keys())
    filtro = st.pills(
        "Categoria",
        categorias,
        selection_mode="multi",
        default=categorias[:3],
        key="im_news_pills",
    )
    if not filtro:
        st.info("Selecione ao menos uma categoria.")
        return

    cols = st.columns(len(filtro))
    for col, cat in zip(cols, filtro):
        with col:
            _news_block(cat, NEWS_CATEGORIAS[cat])


# ── Bloco 3: Benchmarking de concorrentes ────────────────────────────────────

def render_benchmarking() -> None:
    section_title("Benchmarking de Concorrentes", "Share de mercado por fornecedor com base nos produtos cadastrados no CRM.")

    produtos = list_produtos_cliente(limit=5000)
    if produtos.empty:
        st.info("Cadastre produtos com fornecedor para liberar o benchmarking.")
        return

    produtos = produtos.copy()
    produtos["consumo_kg"] = pd.to_numeric(produtos["consumo_kg"], errors="coerce").fillna(0)
    produtos["preco_medio"] = pd.to_numeric(produtos["preco_medio"], errors="coerce").fillna(0)
    produtos["faturamento"] = produtos["consumo_kg"] * produtos["preco_medio"]
    produtos["Fornecedor"] = produtos["fornecedor_atual"].map(
        lambda v: clean_text(v).strip().upper() or "NÃO INFORMADO"
    )

    # filtro por produto
    prod_opcoes = sorted(
        {clean_text(p).strip() for p in produtos["produto"].tolist() if clean_text(p).strip()}
    )
    filtro_prod = st.selectbox(
        "Filtrar por produto",
        ["Todos os produtos"] + prod_opcoes,
        key="im_bench_produto",
    )
    if filtro_prod != "Todos os produtos":
        produtos = produtos[produtos["produto"] == filtro_prod]

    bench = (
        produtos.groupby("Fornecedor", as_index=False)
        .agg(
            Clientes=("cliente", "nunique"),
            Consumo_KG=("consumo_kg", "sum"),
            Faturamento=("faturamento", "sum"),
        )
        .sort_values("Faturamento", ascending=False)
    )
    total_fat = bench["Faturamento"].sum()
    bench["Share %"] = bench["Faturamento"].map(
        lambda v: f"{(v / total_fat * 100):.1f}%" if total_fat else "—"
    )

    # KPIs
    k1, k2, k3 = st.columns(3)
    with k1:
        kpi_card("Fornecedores mapeados", len(bench))
    with k2:
        kpi_card("Faturamento total mapeado", format_brl(total_fat))
    with k3:
        quimicer_fat = bench.loc[bench["Fornecedor"].str.contains("QUIMICER", na=False), "Faturamento"].sum()
        share_q = quimicer_fat / total_fat if total_fat else 0
        kpi_card("Share Quimicer", f"{share_q:.1%}")

    # gráfico de barras horizontais
    bench_chart = bench.head(10).copy()
    bench_chart["fat_num"] = bench_chart["Faturamento"]
    bench_chart = bench_chart.sort_values("fat_num", ascending=True)
    fig = px.bar(
        bench_chart,
        x="fat_num",
        y="Fornecedor",
        orientation="h",
        text=bench_chart["fat_num"].map(format_brl),
        color="fat_num",
        color_continuous_scale=["#636366", "#38b2aa", "#4ecdc4"],
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(color="#f2f2f7", size=12, family="Inter, Aptos, sans-serif"),
        cliponaxis=False,
        marker_line_width=0,
    )
    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="",
        yaxis_title="",
        margin=dict(l=8, r=36, t=18, b=18),
        xaxis=dict(domain=[0, 0.80], showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(automargin=True),
    )
    st.plotly_chart(style_chart(fig, height=380), use_container_width=True)

    # tabela detalhada
    tabela = bench.copy()
    tabela["Consumo KG"] = tabela["Consumo_KG"].map(lambda v: f"{format_quantity(v)} KG")
    tabela["Faturamento R$"] = tabela["Faturamento"].map(format_brl)
    tabela = tabela[["Fornecedor", "Clientes", "Consumo KG", "Faturamento R$", "Share %"]]
    st.dataframe(tabela, use_container_width=True, hide_index=True)


# ── Bloco 4: Potencial de Mercado ────────────────────────────────────────────

def render_potencial() -> None:
    section_title("Potencial de Mercado", "Identifica clientes com maior gap entre capacidade instalada e consumo atual de produtos.")

    empresas = list_empresas()
    produtos = list_produtos_cliente(limit=5000)

    if empresas.empty:
        st.info("Cadastre clientes para liberar a análise de potencial.")
        return

    empresas = empresas.copy()
    for col in ["capacidade_m2", "producao_m2", "producao_polido_m2"]:
        empresas[col] = pd.to_numeric(empresas[col], errors="coerce").fillna(0)

    if not produtos.empty:
        produtos = produtos.copy()
        produtos["consumo_kg"] = pd.to_numeric(produtos["consumo_kg"], errors="coerce").fillna(0)
        produtos["faturamento"] = (
            pd.to_numeric(produtos["consumo_kg"], errors="coerce").fillna(0)
            * pd.to_numeric(produtos["preco_medio"], errors="coerce").fillna(0)
        )
        consumo_cliente = (
            produtos.groupby("cliente", as_index=False)
            .agg(consumo_total_kg=("consumo_kg", "sum"), faturamento_total=("faturamento", "sum"))
        )
        empresas = empresas.merge(consumo_cliente, left_on="nome", right_on="cliente", how="left")
        empresas["consumo_total_kg"] = empresas["consumo_total_kg"].fillna(0)
        empresas["faturamento_total"] = empresas["faturamento_total"].fillna(0)
    else:
        empresas["consumo_total_kg"] = 0.0
        empresas["faturamento_total"] = 0.0

    # Ocupação (produção / capacidade)
    empresas["ocupacao_pct"] = empresas.apply(
        lambda r: r["producao_m2"] / r["capacidade_m2"] if r["capacidade_m2"] > 0 else 0,
        axis=1,
    )

    # Gap: clientes com alta produção mas baixo consumo de produtos = maior potencial
    max_prod = empresas["producao_m2"].max() or 1
    max_consumo = empresas["consumo_total_kg"].max() or 1
    empresas["score_potencial"] = (
        (empresas["producao_m2"] / max_prod) * 0.6
        - (empresas["consumo_total_kg"] / max_consumo) * 0.4
    ).clip(lower=0)

    top = empresas.nlargest(15, "score_potencial")

    # KPIs
    k1, k2, k3 = st.columns(3)
    with k1:
        kpi_card("Clientes analisados", len(empresas))
    with k2:
        sem_consumo = len(empresas[empresas["consumo_total_kg"] == 0])
        kpi_card("Sem consumo cadastrado", sem_consumo)
    with k3:
        alta_ocupacao = len(empresas[empresas["ocupacao_pct"] >= 0.8])
        kpi_card("Alta ocupação (≥80%)", alta_ocupacao)

    # gráfico bolha: eixo x = produção, eixo y = consumo, tamanho = capacidade
    st.markdown("#### Mapa de Potencial — Produção vs Consumo")
    st.caption("Clientes no canto direito-inferior (alta produção, baixo consumo) têm maior potencial de crescimento.")

    bubble_df = empresas[empresas["capacidade_m2"] > 0].copy()
    if bubble_df.empty:
        st.info("Cadastre capacidade instalada nos clientes para ver o mapa de potencial.")
    else:
        fig = px.scatter(
            bubble_df,
            x="producao_m2",
            y="consumo_total_kg",
            size="capacidade_m2",
            color="status",
            hover_name="nome",
            hover_data={
                "producao_m2": False,
                "consumo_total_kg": False,
                "capacidade_m2": False,
                "status": False,
                "Produção (m²)": bubble_df["producao_m2"].map(format_quantity),
                "Consumo (KG)": bubble_df["consumo_total_kg"].map(format_quantity),
                "Capacidade (m²)": bubble_df["capacidade_m2"].map(format_quantity),
            },
            labels={
                "producao_m2": "Produção atual (m²)",
                "consumo_total_kg": "Consumo de produtos (KG)",
            },
            color_discrete_sequence=CHART_COLORS,
            size_max=52,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#263a40", size=12, family="Aptos, Avenir Next, Helvetica Neue, Segoe UI, sans-serif"),
            margin=dict(l=12, r=12, t=18, b=18),
            legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5, font=dict(size=11)),
        )
        fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False)
        st.plotly_chart(fig, use_container_width=True)

    # Tabela top potencial
    st.markdown("#### Top 15 — Maior Potencial de Crescimento")
    tabela = top[["nome", "status", "regiao", "producao_m2", "consumo_total_kg", "faturamento_total", "ocupacao_pct"]].copy()
    tabela = tabela.rename(columns={
        "nome": "Cliente",
        "status": "Status",
        "regiao": "Região",
        "producao_m2": "Produção m²",
        "consumo_total_kg": "Consumo KG",
        "faturamento_total": "Faturamento R$",
        "ocupacao_pct": "Ocupação %",
    })
    tabela["Produção m²"] = tabela["Produção m²"].map(format_quantity)
    tabela["Consumo KG"] = tabela["Consumo KG"].map(format_quantity)
    tabela["Faturamento R$"] = tabela["Faturamento R$"].map(format_brl)
    tabela["Ocupação %"] = tabela["Ocupação %"].map(lambda v: f"{v:.1%}")
    st.dataframe(tabela, use_container_width=True, hide_index=True)


# ── Entry point ───────────────────────────────────────────────────────────────

_IM_SECTIONS = [
    ("Radar Econômico",      "📈", "Câmbio, petróleo e juros"),
    ("Monitor de Notícias",  "📰", "Notícias por setor com filtro de categoria"),
    ("Benchmarking",         "🏆", "Share de mercado por fornecedor"),
    ("Potencial de Mercado", "🎯", "Clientes com maior gap de crescimento"),
]


def render_inteligencia_mercado() -> None:
    st.markdown(CSS_IM, unsafe_allow_html=True)

    active = st.session_state.get("im_sub", "Radar Econômico")

    cols = st.columns(4)
    for col, (name, icon, desc) in zip(cols, _IM_SECTIONS):
        with col:
            btn_type = "primary" if name == active else "secondary"
            if st.button(f"{icon} {name}", key=f"im_nav_{name}", use_container_width=True, type=btn_type):
                st.session_state["im_sub"] = name
                st.rerun()

    active = st.session_state.get("im_sub", "Radar Econômico")
    _divider()

    if active == "Radar Econômico":
        render_radar_economico()
    elif active == "Monitor de Notícias":
        render_noticias()
    elif active == "Benchmarking":
        render_benchmarking()
    else:
        render_potencial()

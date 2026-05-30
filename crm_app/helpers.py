from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

CHART_COLORS = ["#4ecdc4", "#aeaeb2", "#6c6c70", "#8e8e93", "#636366", "#2c2c2e", "#38b2aa"]


def clean_text(value) -> str:
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except TypeError:
        pass
    return str(value)


def format_br_number(value, decimals: int = 2) -> str:
    number = float(value or 0)
    formatted = f"{number:,.{decimals}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def format_quantity(value) -> str:
    return format_br_number(value, 0)


def format_brl(value) -> str:
    return f"R$ {format_br_number(value, 2)}"


def format_usd(value) -> str:
    return f"US$ {format_br_number(value, 2)}"


def parse_br_number(value) -> float:
    text = clean_text(value).strip()
    if not text:
        return 0.0
    text = text.replace("R$", "").replace("kg", "").replace("m²", "").replace("m2", "").strip()
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif "." in text:
        parts = text.split(".")
        if len(parts) > 1 and all(len(part) == 3 for part in parts[1:]):
            text = "".join(parts)
    return float(text or 0)


def style_chart(fig, height: int = 390):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#aeaeb2", size=12, family="Inter, Aptos, Helvetica Neue, Segoe UI, sans-serif"),
        margin=dict(l=12, r=12, t=18, b=18),
        colorway=CHART_COLORS,
        hoverlabel=dict(bgcolor="#2c2c2e", font_color="#f2f2f7", bordercolor="#4ecdc4", font_size=13),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.05,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#aeaeb2"),
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False, tickfont=dict(color="#6c6c70"))
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False, tickfont=dict(color="#6c6c70"))
    return fig


def kpi_card(label: str, value) -> None:
    st.markdown(
        f"""
        <div class="bi-kpi">
            <div class="bi-kpi-label">{label}</div>
            <div class="bi-kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, caption: str = "") -> None:
    caption_html = f'<div class="crm-section-caption">{caption}</div>' if caption else ""
    st.markdown(
        f'<div class="crm-section-title">{title}</div>{caption_html}',
        unsafe_allow_html=True,
    )


def style_donut(fig, center_text: str, height: int = 360, bottom_margin: int = 60, revision_key: str = "donut-stable"):
    fig = style_chart(fig, height=height)
    fig.update_traces(
        textinfo="percent",
        textposition="inside",
        insidetextorientation="radial",
        textfont=dict(color="#f2f2f7", size=11, family="Inter, Aptos, Helvetica Neue, sans-serif"),
        hoverlabel=dict(font_size=13, bgcolor="#2c2c2e", font_color="#f2f2f7", bordercolor="#4ecdc4"),
        marker=dict(line=dict(color="#1c1c1e", width=2)),
        # desativa animação de entrada
        rotation=0,
    )
    fig.update_layout(
        annotations=[
            dict(
                text=center_text,
                x=0.5,
                y=0.5,
                showarrow=False,
                font_size=15,
                font_color="#ffffff",
                align="center",
            )
        ],
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#aeaeb2"),
            itemsizing="constant",
            traceorder="normal",
        ),
        margin=dict(l=12, r=12, t=18, b=bottom_margin),
        uirevision=revision_key,
        # desativa todas as animações
        transition=dict(duration=0),
        dragmode=False,
    )
    return fig

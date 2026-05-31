from __future__ import annotations

import math

import streamlit as st

from crm_app.security import safe_html

CHART_COLORS = ["#4ecdc4", "#aeaeb2", "#6c6c70", "#8e8e93", "#636366", "#2c2c2e", "#38b2aa"]
_DONUT_RADIUS = 92
_DONUT_STROKE = 42
_DONUT_CENTER = 160


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
    safe_label = safe_html(label)
    safe_value = safe_html(value)
    st.markdown(
        f"""
        <div class="bi-kpi">
            <div class="bi-kpi-label">{safe_label}</div>
            <div class="bi-kpi-value">{safe_value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def section_title(title: str, caption: str = "") -> None:
    caption_html = f'<div class="crm-section-caption">{safe_html(caption)}</div>' if caption else ""
    st.markdown(
        f'<div class="crm-section-title">{safe_html(title)}</div>{caption_html}',
        unsafe_allow_html=True,
    )


def _percent_label(value: float, total: float) -> str:
    pct = value / total * 100 if total else 0
    if pct < 3:
        return f"{pct:.2f}".rstrip("0").rstrip(".") + "%"
    if abs(pct - round(pct)) < 0.05:
        return f"{pct:.0f}%"
    return f"{pct:.1f}%"


def _donut_center_text(center_text: str) -> str:
    lines = [line.strip() for line in clean_text(center_text).replace("<br/>", "<br>").split("<br>")]
    lines = [line for line in lines if line]
    if not lines:
        return ""
    first_y = 154 - ((len(lines) - 1) * 15)
    tspans = []
    for index, line in enumerate(lines[:3]):
        tspans.append(
            f'<tspan x="{_DONUT_CENTER}" y="{first_y + index * 30}">{safe_html(line)}</tspan>'
        )
    return "\n".join(tspans)


def render_static_donut(labels, values, center_text: str, colors: list[str] | None = None) -> None:
    """Renderiza uma rosca estática em SVG, sem eventos de mouse do Plotly."""
    pairs = [
        (clean_text(label).strip() or "Não informado", float(value or 0))
        for label, value in zip(labels, values)
        if float(value or 0) > 0
    ]
    if not pairs:
        st.info("Sem dados para este gráfico.")
        return

    palette = colors or CHART_COLORS
    total = sum(value for _, value in pairs)
    circumference = 2 * math.pi * _DONUT_RADIUS
    cumulative = 0.0
    arcs: list[str] = []
    percent_labels: list[str] = []
    legend_items: list[str] = []

    for index, (label, value) in enumerate(pairs):
        color = palette[index % len(palette)]
        pct = value / total if total else 0
        dash = max(circumference * pct - 1.4, 0)
        gap = circumference - dash
        offset = -(circumference * cumulative)
        arcs.append(
            f"""
            <circle class="static-donut-segment"
                cx="{_DONUT_CENTER}" cy="{_DONUT_CENTER}" r="{_DONUT_RADIUS}"
                fill="none" stroke="{color}" stroke-width="{_DONUT_STROKE}"
                stroke-dasharray="{dash:.3f} {gap:.3f}"
                stroke-dashoffset="{offset:.3f}"
                transform="rotate(-90 {_DONUT_CENTER} {_DONUT_CENTER})" />
            """
        )

        if pct >= 0.02:
            angle = math.radians(-90 + (cumulative + pct / 2) * 360)
            label_radius = _DONUT_RADIUS + 2
            x = _DONUT_CENTER + math.cos(angle) * label_radius
            y = _DONUT_CENTER + math.sin(angle) * label_radius
            percent_labels.append(
                f'<text class="static-donut-pct" x="{x:.1f}" y="{y:.1f}">{_percent_label(value, total)}</text>'
            )

        legend_items.append(
            f"""
            <span class="static-donut-legend-item">
                <span class="static-donut-swatch" style="background:{color}"></span>
                <span>{safe_html(label)}</span>
            </span>
            """
        )
        cumulative += pct

    st.markdown(
        f"""
        <div class="static-donut-card">
            <svg class="static-donut-svg" viewBox="0 0 320 352" role="img" aria-label="Gráfico de rosca estático">
                <circle cx="{_DONUT_CENTER}" cy="{_DONUT_CENTER}" r="{_DONUT_RADIUS}"
                    fill="none" stroke="#1c1c1e" stroke-width="{_DONUT_STROKE}" />
                {''.join(arcs)}
                {''.join(percent_labels)}
                <text class="static-donut-center" text-anchor="middle">
                    {_donut_center_text(center_text)}
                </text>
            </svg>
            <div class="static-donut-legend">
                {''.join(legend_items)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

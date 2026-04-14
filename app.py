from __future__ import annotations

import html
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
COMPETITORS_DIR = BASE_DIR / "data" / "competitors"
NEWS_DIR = BASE_DIR / "data" / "news"
NEWS_PATH = NEWS_DIR / "industry_news.json"

DEFAULT_DATA: dict[str, Any] = {
    "company": {
        "name": "Unknown company",
        "website": "",
        "description": "",
        "headquarters": "",
        "ownership": "",
        "founded": "",
        "key_figures": {
            "revenue": "N/A",
            "ebitda": "N/A",
            "growth": "",
            "countries_served": "N/A",
            "location_count": "",
        },
        "leadership": [],
        "locations": [],
        "partnerships": [],
    },
    "colours": [],
    "products": [],
    "industries": [],
    "innovations": [],
    "sustainability": {
        "strategy": "",
        "focus_areas": [],
        "targets": [],
        "initiatives": [],
        "key_metrics": [],
    },
}


def _listify(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _dictify(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _safe_rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR)).replace("\\", "/")
    except ValueError:
        return str(path)


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    for parser in (date.fromisoformat, lambda v: datetime.fromisoformat(v.replace("Z", "+00:00")).date()):
        try:
            return parser(text)
        except ValueError:
            continue
    return None


def normalize_data(raw: dict[str, Any]) -> dict[str, Any]:
    data = {**DEFAULT_DATA, **(raw if isinstance(raw, dict) else {})}

    company = {**DEFAULT_DATA["company"], **_dictify(data.get("company"))}
    key_figures = {
        **DEFAULT_DATA["company"]["key_figures"],
        **_dictify(company.get("key_figures")),
    }
    company["key_figures"] = key_figures
    company["leadership"] = [
        {
            "name": _text(item.get("name"), "Unknown"),
            "title": _text(item.get("title"), ""),
        }
        for item in _listify(company.get("leadership"))
        if isinstance(item, dict)
    ]
    company["locations"] = [str(item) for item in _listify(company.get("locations"))]
    company["partnerships"] = [str(item) for item in _listify(company.get("partnerships"))]

    sustainability = {
        **DEFAULT_DATA["sustainability"],
        **_dictify(data.get("sustainability")),
    }
    sustainability["focus_areas"] = [str(item) for item in _listify(sustainability.get("focus_areas"))]
    sustainability["targets"] = [str(item) for item in _listify(sustainability.get("targets"))]
    sustainability["initiatives"] = [str(item) for item in _listify(sustainability.get("initiatives"))]
    sustainability["key_metrics"] = [str(item) for item in _listify(sustainability.get("key_metrics"))]

    colours = []
    for item in _listify(data.get("colours")):
        if not isinstance(item, dict):
            continue
        colours.append(
            {
                "name": _text(item.get("name"), "Unknown"),
                "description": _text(item.get("description")),
                "sources": [str(v) for v in _listify(item.get("sources"))],
                "applications": [str(v) for v in _listify(item.get("applications"))],
                "key_properties": [str(v) for v in _listify(item.get("key_properties"))],
                "challenges": [str(v) for v in _listify(item.get("challenges"))],
            }
        )

    products = []
    for item in _listify(data.get("products")):
        if not isinstance(item, dict):
            continue
        products.append(
            {
                "name": _text(item.get("name"), "Unknown"),
                "category": _text(item.get("category")),
                "description": _text(item.get("description")),
                "features": [str(v) for v in _listify(item.get("features"))],
                "benefits": [str(v) for v in _listify(item.get("benefits"))],
                "applications": [str(v) for v in _listify(item.get("applications"))],
                "related_colours": [str(v) for v in _listify(item.get("related_colours"))],
            }
        )

    industries = []
    for item in _listify(data.get("industries")):
        if not isinstance(item, dict):
            continue
        industries.append(
            {
                "name": _text(item.get("name"), "Unknown"),
                "description": _text(item.get("description")),
                "consumer_trends": [str(v) for v in _listify(item.get("consumer_trends"))],
                "needs": [str(v) for v in _listify(item.get("needs"))],
                "solutions": [str(v) for v in _listify(item.get("solutions"))],
                "relevant_colours": [str(v) for v in _listify(item.get("relevant_colours"))],
            }
        )

    innovations = []
    for item in _listify(data.get("innovations")):
        if not isinstance(item, dict):
            continue
        innovations.append(
            {
                "name": _text(item.get("name"), "Unknown"),
                "description": _text(item.get("description")),
                "features": [str(v) for v in _listify(item.get("features"))],
                "benefits": [str(v) for v in _listify(item.get("benefits"))],
                "related_products": [str(v) for v in _listify(item.get("related_products"))],
                "related_colours": [str(v) for v in _listify(item.get("related_colours"))],
            }
        )

    return {
        "company": company,
        "colours": colours,
        "products": products,
        "industries": industries,
        "innovations": innovations,
        "sustainability": sustainability,
    }


@st.cache_data(show_spinner=False)
def load_json_file(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    with path.open("r", encoding="utf-8") as handle:
        return normalize_data(json.load(handle))


@st.cache_data(show_spinner=False)
def scan_competitor_files(directory_text: str) -> list[dict[str, str]]:
    directory = Path(directory_text)
    if not directory.exists():
        return []

    competitors: list[dict[str, str]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (json.JSONDecodeError, OSError):
            continue

        company = _dictify(raw.get("company"))
        name = _text(company.get("name"), path.stem.replace("_", " ").title())
        competitors.append(
            {
                "id": path.stem,
                "name": name,
                "path": str(path),
                "path_label": _safe_rel_path(path),
            }
        )

    competitors.sort(key=lambda item: item["name"].lower())
    return competitors


@st.cache_data(show_spinner=False)
def load_news_items(path_text: str) -> list[dict[str, Any]]:
    path = Path(path_text)
    if not path.exists():
        return []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    if isinstance(raw, list):
        items = raw
        shape = "legacy"
    elif isinstance(raw, dict) and isinstance(raw.get("output"), dict) and isinstance(raw["output"].get("results"), list):
        items = raw["output"]["results"]
        shape = "industry"
    elif isinstance(raw, dict) and isinstance(raw.get("news"), list):
        items = raw["news"]
        shape = "company"
    else:
        items = _listify(raw.get("items") if isinstance(raw, dict) else [])
        shape = "legacy"
    normalized: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        if shape == "industry":
            date_value = item.get("publishedDate")
            competitor = item.get("author") or "Industry news"
            summary = item.get("summary") or item.get("description") or ""
            url = item.get("url")
        elif shape == "company":
            date_value = item.get("date")
            competitor = item.get("type") or "Company news"
            summary = item.get("short_description") or item.get("summary") or ""
            url = item.get("link") or item.get("url")
        else:
            date_value = item.get("date")
            competitor = item.get("competitor")
            summary = item.get("summary")
            url = item.get("url")

        parsed_date = _parse_date(date_value)
        normalized.append(
            {
                "date": _text(date_value),
                "parsed_date": parsed_date,
                "title": _text(item.get("title"), "Untitled news item"),
                "competitor": _text(competitor, "Unknown competitor"),
                "summary": _text(summary),
                "url": _text(url),
            }
        )

    normalized.sort(
        key=lambda item: (item["parsed_date"] is not None, item["parsed_date"] or date.min),
        reverse=True,
    )
    return normalized


@st.cache_data(show_spinner=False)
def load_news_summary(path_text: str) -> str:
    path = Path(path_text)
    if not path.exists():
        return ""

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""

    if isinstance(raw, dict) and isinstance(raw.get("output"), dict):
        return _text(raw["output"].get("content")).strip()
    return ""


def resolve_company_news_path(competitor_id: str) -> Path:
    return NEWS_DIR / f"{competitor_id}_news.json"


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(186, 230, 253, 0.55), transparent 24%),
                linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }
        .eyebrow {
            display: inline-block;
            font-size: 0.85rem;
            color: #475569;
            font-weight: 600;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
        }
        .hero-card, .info-card, .stat-card, .list-card, .competitor-card {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 22px;
            box-shadow: 0 14px 40px rgba(15, 23, 42, 0.08);
        }
        .hero-card {
            padding: 1.6rem 1.7rem;
        }
        .info-card, .list-card, .competitor-card {
            padding: 1.15rem 1.2rem;
            margin-bottom: 1rem;
        }
        .stat-card {
            padding: 1rem 1.1rem;
            min-height: 124px;
        }
        .stat-label {
            color: #64748b;
            font-size: 0.88rem;
            margin-bottom: 0.35rem;
        }
        .stat-value {
            color: #0f172a;
            font-size: 1.15rem;
            font-weight: 700;
            line-height: 1.3;
        }
        .stat-subtitle {
            color: #475569;
            font-size: 0.82rem;
            margin-top: 0.35rem;
        }
        .card-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.65rem;
        }
        .card-body {
            color: #475569;
            font-size: 0.93rem;
            line-height: 1.6;
        }
        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.7rem;
        }
        .chip {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
            background: #f1f5f9;
            color: #334155;
            font-size: 0.78rem;
        }
        .section-space {
            margin-top: 1rem;
        }
        .news-date {
            color: #0f766e;
            font-size: 0.84rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        .news-meta {
            color: #64748b;
            font-size: 0.84rem;
            margin-top: 0.35rem;
        }
        .status-flag {
            display: inline-block;
            margin-top: 1rem;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            background: #dcfce7;
            color: #166534;
            font-size: 0.84rem;
            font-weight: 700;
            border: 1px solid #86efac;
        }
        div[data-testid="stTabs"] button {
            border-radius: 999px;
        }
        div[data-testid="stButton"] > button {
            border-radius: 14px;
            border: 1px solid rgba(15, 23, 42, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def card_html(title: str, body: str = "", chips: list[str] | None = None) -> str:
    chip_markup = ""
    if chips:
        chip_markup = '<div class="chip-row">' + "".join(
            f'<span class="chip">{html.escape(str(item))}</span>' for item in chips
        ) + "</div>"
    return (
        '<div class="info-card">'
        f'<div class="card-title">{html.escape(title)}</div>'
        f'<div class="card-body">{body}</div>'
        f"{chip_markup}"
        "</div>"
    )


def stat_card_html(title: str, value: str, subtitle: str = "") -> str:
    subtitle_markup = f'<div class="stat-subtitle">{html.escape(subtitle)}</div>' if subtitle else ""
    return (
        '<div class="stat-card">'
        f'<div class="stat-label">{html.escape(title)}</div>'
        f'<div class="stat-value">{html.escape(value)}</div>'
        f"{subtitle_markup}"
        "</div>"
    )


def render_chip_list(items: list[str]) -> str:
    if not items:
        return ""
    return '<div class="chip-row">' + "".join(
        f'<span class="chip">{html.escape(item)}</span>' for item in items
    ) + "</div>"


def make_colour_chart(colours: list[dict[str, Any]]) -> go.Figure:
    figure = go.Figure()
    figure.add_bar(
        x=[item["name"] for item in colours],
        y=[len(item["sources"]) for item in colours],
        marker_color="#0f766e",
        hovertemplate="%{x}<br>Sources: %{y}<extra></extra>",
    )
    figure.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Number of sources",
        xaxis_title="",
    )
    figure.update_yaxes(gridcolor="rgba(148,163,184,0.25)", zeroline=False)
    return figure


def make_industry_chart(industries: list[dict[str, Any]]) -> go.Figure:
    labels = [item["name"][:14] + "..." if len(item["name"]) > 14 else item["name"] for item in industries]
    values = [len(item["relevant_colours"]) for item in industries]
    if labels and values:
        labels.append(labels[0])
        values.append(values[0])
    figure = go.Figure()
    figure.add_trace(
        go.Scatterpolar(
            r=values,
            theta=labels,
            fill="toself",
            line_color="#0f766e",
            fillcolor="rgba(15,118,110,0.25)",
            hovertemplate="%{theta}<br>Colours: %{r}<extra></extra>",
        )
    )
    figure.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            radialaxis=dict(showline=False, gridcolor="rgba(148,163,184,0.25)"),
            angularaxis=dict(gridcolor="rgba(148,163,184,0.18)"),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
    )
    return figure


def render_home_header(competitors: list[dict[str, str]], news_items: list[dict[str, Any]]) -> None:
    st.markdown('<div class="eyebrow">Competitor intelligence dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="hero-card">
            <h1 style="margin:0; font-size:2.6rem; line-height:1.02; color:#0f172a;">Competitor Landing Page</h1>
            <p style="margin:1rem 0 0; color:#475569; font-size:1rem; line-height:1.7;">
                Start with the latest dated news, then open a competitor to inspect the full extracted profile.
            </p>
            <div class="chip-row">
                <span class="chip">{len(competitors)} competitors</span>
                <span class="chip">{len(news_items)} news items</span>
                <span class="chip">{html.escape(_safe_rel_path(COMPETITORS_DIR))}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_news_feed(news_items: list[dict[str, Any]]) -> None:
    st.markdown('<div class="card-title">Latest news</div>', unsafe_allow_html=True)
    if not news_items:
        st.info("No news file found or no valid news items available.")
        return

    for item in news_items:
        pretty_date = item["parsed_date"].isoformat() if item["parsed_date"] else (item["date"] or "Unknown date")
        link_markup = (
            f'<div style="margin-top:0.8rem;"><a href="{html.escape(item["url"], quote=True)}" target="_blank">Open article</a></div>'
            if item["url"]
            else ""
        )
        st.markdown(
            f"""
            <div class="list-card">
                <div class="news-date">{html.escape(pretty_date)}</div>
                <div class="card-title" style="margin-top:0.4rem;">{html.escape(item['title'])}</div>
                <div class="news-meta">Competitor: {html.escape(item['competitor'])}</div>
                <div class="card-body">{html.escape(item['summary'] or 'No summary available.')}</div>
                {link_markup}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_news_summary(summary: str) -> None:
    if not summary:
        return
    st.markdown(card_html("Industry summary", html.escape(summary)), unsafe_allow_html=True)


def render_competitor_selector(competitors: list[dict[str, str]]) -> None:
    st.markdown('<div class="card-title">Competitors</div>', unsafe_allow_html=True)
    if not competitors:
        st.warning("No competitor JSON files were found in the scanned folder.")
        return

    for competitor in competitors:
        st.markdown(
            f"""
            <div class="competitor-card">
                <div class="card-title">{html.escape(competitor['name'])}</div>
                <div class="card-body">{html.escape(competitor['path_label'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Open {competitor['name']}", key=f"open_{competitor['id']}", use_container_width=True):
            st.session_state["selected_competitor_id"] = competitor["id"]
            st.rerun()


def render_home_view(competitors: list[dict[str, str]], news_items: list[dict[str, Any]], news_summary: str) -> None:
    render_home_header(competitors, news_items)
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.7, 1], gap="large")
    with left:
        render_news_summary(news_summary)
        render_news_feed(news_items)
    with right:
        render_competitor_selector(competitors)


def render_detail_header(data: dict[str, Any], source_label: str) -> None:
    company = data["company"]
    top_left, top_right = st.columns([3.3, 1.1], gap="large")
    with top_left:
        st.markdown('<div class="eyebrow">Competitor detail</div>', unsafe_allow_html=True)
        badge_markup = render_chip_list(
            [
                item
                for item in [
                    f"HQ: {company['headquarters']}" if company["headquarters"] else "",
                    f"Founded: {company['founded']}" if company["founded"] else "",
                    f"Ownership: {company['ownership']}" if company["ownership"] else "",
                    f"Website: {company['website']}" if company["website"] else "",
                ]
                if item
            ]
        )
        st.markdown(
            f"""
            <div class="hero-card">
                <h1 style="margin:0; font-size:2.4rem; line-height:1.05; color:#0f172a;">{html.escape(company['name'])}</h1>
                <p style="margin:1rem 0 0; color:#475569; font-size:1rem; line-height:1.7;">
                    {html.escape(company['description'] or 'No company summary available.')}
                </p>
                <div class="status-flag">(no changes detected)</div>
                <p style="margin:0.85rem 0 0; color:#64748b; font-size:0.85rem;">{html.escape(source_label)}</p>
                {badge_markup}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_right:
        st.markdown("<div style='height: 2.1rem;'></div>", unsafe_allow_html=True)
        if st.button("Back to landing page", use_container_width=True):
            st.session_state["selected_competitor_id"] = None
            st.rerun()


def render_stats(data: dict[str, Any]) -> None:
    key_figures = data["company"]["key_figures"]
    partnerships = data["company"]["partnerships"]
    columns = st.columns(4, gap="medium")
    stats = [
        ("Revenue", key_figures.get("revenue", "N/A"), ""),
        ("EBITDA", key_figures.get("ebitda", "N/A"), key_figures.get("growth", "")),
        ("Global reach", key_figures.get("countries_served", "N/A"), key_figures.get("location_count", "")),
        ("Partnerships", str(len(partnerships)), "Named partnerships and memberships"),
    ]
    for column, (title, value, subtitle) in zip(columns, stats):
        with column:
            st.markdown(stat_card_html(title, value, subtitle), unsafe_allow_html=True)


def render_overview_tab(data: dict[str, Any]) -> None:
    colours = data["colours"]
    industries = data["industries"]
    leadership = data["company"]["leadership"]
    innovations = data["innovations"]

    chart_col, leadership_col = st.columns([2.1, 1], gap="large")
    with chart_col:
        st.markdown('<div class="card-title">Colour portfolio footprint</div>', unsafe_allow_html=True)
        if colours:
            st.plotly_chart(make_colour_chart(colours), use_container_width=True)
        else:
            st.info("No colour data available.")
    with leadership_col:
        st.markdown('<div class="card-title">Leadership</div>', unsafe_allow_html=True)
        if leadership:
            for leader in leadership:
                st.markdown(card_html(leader["name"], html.escape(leader["title"])), unsafe_allow_html=True)
        else:
            st.info("No leadership entries available.")

    industry_col, innovation_col = st.columns([1.35, 1], gap="large")
    with industry_col:
        st.markdown('<div class="card-title">Industries by colour breadth</div>', unsafe_allow_html=True)
        if industries:
            st.plotly_chart(make_industry_chart(industries), use_container_width=True)
        else:
            st.info("No industry data available.")
    with innovation_col:
        st.markdown('<div class="card-title">Innovation spotlight</div>', unsafe_allow_html=True)
        if innovations:
            for innovation in innovations:
                body_parts = [innovation["description"]]
                if innovation["related_products"]:
                    body_parts.append(f"Related products: {', '.join(innovation['related_products'])}")
                st.markdown(
                    card_html(
                        innovation["name"],
                        "<br>".join(html.escape(part) for part in body_parts if part),
                        innovation["related_colours"][:6],
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.info("No innovation data available.")


def render_colours_tab(data: dict[str, Any]) -> None:
    colours = data["colours"]
    if not colours:
        st.info("No colour portfolio data available.")
        return

    columns = st.columns(2, gap="large")
    for index, colour in enumerate(colours):
        with columns[index % 2]:
            st.markdown(
                f"""
                <div class="info-card">
                    <div class="card-title">{html.escape(colour['name'])}</div>
                    <div class="card-body">{html.escape(colour['description'] or 'No description available.')}</div>
                    <div class="section-space"><strong>Sources</strong>{render_chip_list(colour['sources'])}</div>
                    <div class="section-space"><strong>Applications</strong>{render_chip_list(colour['applications'])}</div>
                    <div class="section-space"><strong>Key properties</strong>{render_chip_list(colour['key_properties'])}</div>
                    <div class="section-space"><strong>Challenges</strong>{render_chip_list(colour['challenges'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_products_tab(data: dict[str, Any]) -> None:
    products = data["products"]
    query = st.text_input("Search products", placeholder="Search by name, category, application, or colour")
    query_lower = query.strip().lower()

    filtered = [
        item
        for item in products
        if not query_lower
        or query_lower in item["name"].lower()
        or query_lower in item["category"].lower()
        or query_lower in " ".join(item["applications"]).lower()
        or query_lower in " ".join(item["related_colours"]).lower()
    ]

    st.caption(f"{len(filtered)} of {len(products)} products shown")

    if not filtered:
        st.info("No products match the current search.")
        return

    for product in filtered:
        body_parts = []
        if product["description"]:
            body_parts.append(product["description"])
        if product["features"]:
            body_parts.append(f"Features: {', '.join(product['features'])}")
        if product["benefits"]:
            body_parts.append(f"Benefits: {', '.join(product['benefits'])}")
        chips = product["applications"] + product["related_colours"]
        st.markdown(
            card_html(
                product["name"],
                f"<strong>{html.escape(product['category'] or 'Uncategorized')}</strong><br><br>"
                + "<br><br>".join(html.escape(part) for part in body_parts),
                chips,
            ),
            unsafe_allow_html=True,
        )


def render_industries_tab(data: dict[str, Any]) -> None:
    industries = data["industries"]
    if not industries:
        st.info("No industry data available.")
        return

    for industry in industries:
        st.markdown(
            f"""
            <div class="info-card">
                <div class="card-title">{html.escape(industry['name'])}</div>
                <div class="card-body">{html.escape(industry['description'] or 'No description available.')}</div>
                <div class="section-space"><strong>Consumer trends</strong>{render_chip_list(industry['consumer_trends'])}</div>
                <div class="section-space"><strong>Needs</strong>{render_chip_list(industry['needs'])}</div>
                <div class="section-space"><strong>Solutions</strong>{render_chip_list(industry['solutions'])}</div>
                <div class="section-space"><strong>Relevant colours</strong>{render_chip_list(industry['relevant_colours'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sustainability_tab(data: dict[str, Any]) -> None:
    sustainability = data["sustainability"]
    top_left, top_right = st.columns([1.1, 1], gap="large")

    with top_left:
        st.markdown(
            card_html(
                "Strategy",
                html.escape(sustainability["strategy"] or "No sustainability strategy available."),
                sustainability["focus_areas"],
            ),
            unsafe_allow_html=True,
        )
        st.markdown(card_html("Targets", "", sustainability["targets"]), unsafe_allow_html=True)

    with top_right:
        st.markdown(card_html("Initiatives", "", sustainability["initiatives"]), unsafe_allow_html=True)
        st.markdown(card_html("Key metrics", "", sustainability["key_metrics"]), unsafe_allow_html=True)


def render_company_news_tab(news_items: list[dict[str, Any]]) -> None:
    if not news_items:
        st.info("No company news file found or no valid company news items available.")
        return
    render_news_feed(news_items)


def render_sidebar(competitors: list[dict[str, str]], news_items: list[dict[str, Any]]) -> None:
    st.sidebar.header("Dataset overview")
    st.sidebar.write(f"Competitors found: {len(competitors)}")
    st.sidebar.write(f"News items found: {len(news_items)}")
    st.sidebar.caption(f"Competitor folder: {_safe_rel_path(COMPETITORS_DIR)}")
    st.sidebar.caption(f"News file: {_safe_rel_path(NEWS_PATH)}")
    if st.sidebar.button("Refresh data", use_container_width=True):
        scan_competitor_files.clear()
        load_json_file.clear()
        load_news_items.clear()
        st.rerun()


def render_detail_view(competitor: dict[str, str]) -> None:
    data = load_json_file(competitor["path"])
    company_news_items = load_news_items(str(resolve_company_news_path(competitor["id"])))
    render_detail_header(data, f"Loaded from {competitor['path_label']}")
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    render_stats(data)
    st.markdown("<div style='height: 1.35rem;'></div>", unsafe_allow_html=True)

    overview_tab, colours_tab, products_tab, industries_tab, sustainability_tab, news_tab = st.tabs(
        ["Overview", "Colours", "Products", "Industries", "Sustainability", "News"]
    )
    with overview_tab:
        render_overview_tab(data)
    with colours_tab:
        render_colours_tab(data)
    with products_tab:
        render_products_tab(data)
    with industries_tab:
        render_industries_tab(data)
    with sustainability_tab:
        render_sustainability_tab(data)
    with news_tab:
        render_company_news_tab(company_news_items)


def main() -> None:
    st.set_page_config(
        page_title="Competitor Intelligence Dashboard",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    competitors = scan_competitor_files(str(COMPETITORS_DIR))
    news_items = load_news_items(str(NEWS_PATH))
    news_summary = load_news_summary(str(NEWS_PATH))
    render_sidebar(competitors, news_items)

    if "selected_competitor_id" not in st.session_state:
        st.session_state["selected_competitor_id"] = None

    selected_id = st.session_state["selected_competitor_id"]
    selected_competitor = next((item for item in competitors if item["id"] == selected_id), None)

    if selected_competitor is None:
        st.session_state["selected_competitor_id"] = None
        render_home_view(competitors, news_items, news_summary)
        return

    render_detail_view(selected_competitor)


if __name__ == "__main__":
    main()

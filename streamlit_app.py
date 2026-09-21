from pathlib import Path
import textwrap, json, zipfile, os

root = Path("/mnt/data/health_policy_intelligence")
(root / "app").mkdir(parents=True, exist_ok=True)
(root / "data").mkdir(parents=True, exist_ok=True)
(root / ".streamlit").mkdir(parents=True, exist_ok=True)

files = {}

files["streamlit_app.py"] = r'''
import streamlit as st

from app.ui import inject_global_css, render_sidebar_brand
from app.pages import dashboard, policies, organizations, signals, about

st.set_page_config(
    page_title="HealthScope AI",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
render_sidebar_brand()

pages = {
    "INTELLIGENCE": [
        st.Page(dashboard.render, title="Executive Dashboard", icon=":material/space_dashboard:", default=True),
        st.Page(policies.render, title="Policy Explorer", icon=":material/policy:"),
        st.Page(signals.render, title="Trend Signals", icon=":material/query_stats:"),
    ],
    "ECOSYSTEM": [
        st.Page(organizations.render, title="Organization Map", icon=":material/account_tree:"),
    ],
    "ABOUT": [
        st.Page(about.render, title="About", icon=":material/info:"),
    ],
}

pg = st.navigation(pages, position="sidebar")
pg.run()
'''

files["app/__init__.py"] = ""
files["app/pages.py"] = r'''
from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.data import (
    load_policy_data,
    load_signal_data,
    load_organizations,
    compute_kpis,
)
from app.ui import (
    hero,
    metric_card,
    section_header,
    policy_card,
    insight_box,
    status_badge,
    empty_state,
)


def _filtered_policy_df() -> pd.DataFrame:
    df = load_policy_data()

    with st.sidebar:
        st.markdown("### FILTERS")
        ministries = ["전체"] + sorted(df["ministry"].unique().tolist())
        selected_ministry = st.selectbox("기관", ministries, index=0)
        categories = ["전체"] + sorted(df["category"].unique().tolist())
        selected_category = st.selectbox("분야", categories, index=0)
        stages = st.multiselect(
            "상태",
            options=sorted(df["stage"].unique().tolist()),
            default=sorted(df["stage"].unique().tolist()),
        )
        query = st.text_input("키워드 검색", placeholder="예: 디지털헬스, AI, 의료데이터")

    result = df.copy()
    if selected_ministry != "전체":
        result = result[result["ministry"] == selected_ministry]
    if selected_category != "전체":
        result = result[result["category"] == selected_category]
    if stages:
        result = result[result["stage"].isin(stages)]
    if query.strip():
        q = query.strip().lower()
        mask = (
            result["title"].str.lower().str.contains(q, na=False)
            | result["summary"].str.lower().str.contains(q, na=False)
            | result["keywords"].str.lower().str.contains(q, na=False)
        )
        result = result[mask]
    return result


class dashboard:
    @staticmethod
    def render():
        policies = load_policy_data()
        signals = load_signal_data()
        kpis = compute_kpis(policies)

        hero(
            eyebrow="HEALTHCARE POLICY INTELLIGENCE",
            title="복잡한 정책과 산업 신호를<br>한 화면에서 읽습니다.",
            subtitle=(
                "보건의료 정책, 정부사업, 규제 변화, 산업 트렌드를 연결해 "
                "‘무슨 일이 일어나고 있고 왜 중요한지’를 빠르게 파악하는 대시보드."
            ),
            tag="Prototype · 2026",
        )

        cols = st.columns(4)
        values = [
            ("추적 정책", f"{kpis['policy_count']}", "현재 데이터셋", "neutral"),
            ("진행 중", f"{kpis['active_count']}", f"{kpis['active_ratio']:.0f}% of total", "positive"),
            ("High Impact", f"{kpis['high_impact']}", "영향도 80+", "positive"),
            ("관찰 기관", f"{kpis['org_count']}", "정부·공공기관", "neutral"),
        ]
        for c, item in zip(cols, values):
            with c:
                metric_card(*item)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        left, right = st.columns([1.45, 1], gap="large")

        with left:
            section_header("정책 모멘텀", "최근 정책 이벤트와 중요도를 월별로 집계")
            trend = (
                policies.assign(month=pd.to_datetime(policies["date"]).dt.to_period("M").astype(str))
                .groupby("month", as_index=False)
                .agg(policy_count=("title", "count"), avg_impact=("impact_score", "mean"))
            )
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=trend["month"], y=trend["policy_count"],
                name="정책 건수", marker_line_width=0
            ))
            fig.add_trace(go.Scatter(
                x=trend["month"], y=trend["avg_impact"],
                name="평균 영향도", mode="lines+markers", yaxis="y2",
                line=dict(width=3), marker=dict(size=7)
            ))
            fig.update_layout(
                height=350,
                margin=dict(l=10, r=10, t=20, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#DDE4F0"),
                legend=dict(orientation="h", y=1.12),
                xaxis=dict(showgrid=False),
                yaxis=dict(title="정책 건수", gridcolor="rgba(255,255,255,.06)"),
                yaxis2=dict(title="영향도", overlaying="y", side="right", range=[0, 100], showgrid=False),
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        with right:
            section_header("AI 브리핑", "오늘 확인할 핵심 신호 3개")
            top = policies.sort_values(["impact_score", "date"], ascending=[False, False]).head(3)
            for _, row in top.iterrows():
                insight_box(
                    title=row["title"],
                    body=row["why_it_matters"],
                    meta=f"{row['ministry']} · 영향도 {row['impact_score']}",
                )

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        a, b = st.columns([1.1, 1], gap="large")

        with a:
            section_header("정책 포트폴리오", "분야별 정책 분포")
            cat = policies.groupby("category", as_index=False).size().rename(columns={"size": "count"})
            fig = px.treemap(cat, path=["category"], values="count")
            fig.update_layout(
                height=340,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
            )
            fig.update_traces(
                textinfo="label+value",
                marker=dict(line=dict(width=2, color="#101722")),
                hovertemplate="<b>%{label}</b><br>%{value}건<extra></extra>",
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        with b:
            section_header("시장 신호", "산업에서 감지되는 주요 변화")
            for _, row in signals.sort_values("score", ascending=False).head(5).iterrows():
                st.markdown(
                    f"""
                    <div class="signal-row">
                        <div>
                            <div class="signal-title">{row['signal']}</div>
                            <div class="signal-meta">{row['source']} · {row['date']}</div>
                        </div>
                        <div class="signal-score">{row['score']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        section_header("최근 주요 정책", "영향도가 높은 순으로 표시")
        for _, row in policies.sort_values(["impact_score", "date"], ascending=[False, False]).head(4).iterrows():
            policy_card(row)


class policies:
    @staticmethod
    def render():
        hero(
            eyebrow="POLICY EXPLORER",
            title="정책을 검색하고,<br>의미를 구조화합니다.",
            subtitle="기관·분야·상태·키워드로 정책을 필터링하고 영향도와 산업적 의미를 함께 확인하세요.",
            tag="Search & Filter",
            compact=True,
        )

        df = _filtered_policy_df()

        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            st.metric("검색 결과", f"{len(df)}건")
        with c2:
            st.metric("평균 영향도", f"{df['impact_score'].mean():.1f}" if len(df) else "-")
        with c3:
            sort = st.selectbox(
                "정렬",
                ["영향도 높은 순", "최신 순", "오래된 순"],
                label_visibility="collapsed",
            )

        if sort == "영향도 높은 순":
            df = df.sort_values(["impact_score", "date"], ascending=[False, False])
        elif sort == "최신 순":
            df = df.sort_values("date", ascending=False)
        else:
            df = df.sort_values("date", ascending=True)

        if df.empty:
            empty_state("조건에 맞는 정책이 없습니다.", "필터나 검색어를 바꿔보세요.")
            return

        for _, row in df.iterrows():
            policy_card(row, expanded=False)


class organizations:
    @staticmethod
    def render():
        orgs = load_organizations()

        hero(
            eyebrow="ECOSYSTEM MAP",
            title="누가 결정하고,<br>누가 실행하는가.",
            subtitle="헬스케어 정책과 사업을 움직이는 주요 정부·공공기관의 역할을 구조적으로 봅니다.",
            tag="Institution Map",
            compact=True,
        )

        section_header("기관 구조", "정책 → 집행 → 평가·데이터 흐름을 단순화한 프로토타입")
        layers = ["정책·법제", "사업·집행", "평가·데이터"]
        for layer in layers:
            st.markdown(f"<div class='layer-label'>{layer}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            subset = orgs[orgs["layer"] == layer].reset_index(drop=True)
            for i, row in subset.iterrows():
                with cols[i % 3]:
                    st.markdown(
                        f"""
                        <div class="org-card">
                            <div class="org-kind">{row['type']}</div>
                            <div class="org-name">{row['name']}</div>
                            <div class="org-role">{row['role']}</div>
                            <div class="org-watch">WATCH · {row['watch']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        section_header("기관별 관찰 포인트", "실제 서비스에서는 공고·보도자료·법령·예산 데이터를 자동 수집")
        fig = px.scatter(
            orgs,
            x="policy_power",
            y="market_influence",
            size="data_richness",
            text="short",
            hover_name="name",
            hover_data=["role"],
            labels={
                "policy_power": "정책 결정력",
                "market_influence": "시장 영향력",
                "data_richness": "데이터 풍부도",
            },
        )
        fig.update_traces(textposition="top center")
        fig.update_layout(
            height=480,
            xaxis=dict(range=[0, 105], gridcolor="rgba(255,255,255,.06)"),
            yaxis=dict(range=[0, 105], gridcolor="rgba(255,255,255,.06)"),
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#DDE4F0"),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


class signals:
    @staticmethod
    def render():
        df = load_signal_data()

        hero(
            eyebrow="TREND SIGNALS",
            title="작은 신호에서<br>큰 흐름을 읽습니다.",
            subtitle="기술·투자·정책·규제·수요 변화를 신호 점수로 구조화한 화면입니다.",
            tag="Signal Detection",
            compact=True,
        )

        cols = st.columns(3)
        with cols[0]:
            category = st.selectbox("신호 유형", ["전체"] + sorted(df["category"].unique().tolist()))
        with cols[1]:
            min_score = st.slider("최소 신호 점수", 0, 100, 60)
        with cols[2]:
            horizon = st.selectbox("관찰 기간", ["전체", "30일", "90일", "180일"])

        filtered = df[df["score"] >= min_score].copy()
        if category != "전체":
            filtered = filtered[filtered["category"] == category]

        if horizon != "전체":
            days = int(horizon.replace("일", ""))
            cutoff = pd.Timestamp(date.today() - timedelta(days=days))
            filtered = filtered[pd.to_datetime(filtered["date"]) >= cutoff]

        section_header("Signal Board", f"{len(filtered)}개의 신호가 조건에 부합")
        if filtered.empty:
            empty_state("감지된 신호가 없습니다.", "점수 기준이나 기간을 넓혀보세요.")
            return

        for _, row in filtered.sort_values(["score", "date"], ascending=[False, False]).iterrows():
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(
                    f"""
                    <div class="signal-card">
                        <div class="signal-topline">
                            <span class="chip">{row['category']}</span>
                            <span class="muted">{row['date']} · {row['source']}</span>
                        </div>
                        <div class="signal-big-title">{row['signal']}</div>
                        <div class="signal-desc">{row['description']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c2:
                score = int(row["score"])
                st.markdown(
                    f"""
                    <div class="score-ring">
                        <div class="score-number">{score}</div>
                        <div class="score-label">SIGNAL</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


class about:
    @staticmethod
    def render():
        hero(
            eyebrow="ABOUT THE PROTOTYPE",
            title="정보를 모으는 앱이 아니라,<br>판단을 돕는 앱.",
            subtitle="HealthScope AI는 정부 정책과 산업 변화를 하나의 맥락으로 연결하는 정책 인텔리전스 프로토타입입니다.",
            tag="v0.1",
            compact=True,
        )

        left, right = st.columns([1.1, 1], gap="large")
        with left:
            section_header("제품 철학")
            st.markdown(
                """
                **1. Source → Signal**  
                보도자료, 법령, 사업공고, 예산, 기관 발표 같은 원천 정보를 수집합니다.

                **2. Signal → Context**  
                단순 요약을 넘어 ‘왜 지금 나왔는가’, ‘누구에게 영향을 주는가’를 연결합니다.

                **3. Context → Action**  
                연구자, 기업, 창업가, 취업 준비자가 다음 행동을 정할 수 있도록 관찰 포인트를 제공합니다.
                """
            )

        with right:
            section_header("다음 개발 단계")
            st.markdown(
                """
                - 실제 정부기관 RSS/API/공고 데이터 연동
                - LLM 기반 정책 자동 요약 및 태깅
                - 사용자 관심 분야별 개인화 피드
                - 정책 변경 알림
                - 기업·기관·법령 Knowledge Graph
                - PostgreSQL/Supabase 데이터베이스
                - 로그인 및 북마크
                """
            )

        st.info("현재 포함된 데이터는 UI/기능 시연용 샘플 데이터입니다.")
'''

files["app/data.py"] = r'''
from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


@st.cache_data
def load_policy_data():
    return pd.read_csv(DATA_DIR / "policies.csv")


@st.cache_data
def load_signal_data():
    return pd.read_csv(DATA_DIR / "signals.csv")


@st.cache_data
def load_organizations():
    return pd.read_csv(DATA_DIR / "organizations.csv")


def compute_kpis(df):
    active = df[df["stage"].isin(["추진중", "공고", "입법예고"])]
    orgs = load_organizations()
    return {
        "policy_count": len(df),
        "active_count": len(active),
        "active_ratio": (len(active) / len(df) * 100) if len(df) else 0,
        "high_impact": int((df["impact_score"] >= 80).sum()),
        "org_count": len(orgs),
    }
'''

files["app/ui.py"] = r'''
import streamlit as st


def inject_global_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

        :root {
            --bg: #081018;
            --panel: #0E1722;
            --panel2: #101C29;
            --line: rgba(255,255,255,.08);
            --text: #F4F7FB;
            --muted: #8C9AAF;
            --cyan: #35E0C1;
            --blue: #6C8CFF;
            --amber: #F5C26B;
        }

        html, body, [class*="css"] {
            font-family: "Inter", "Noto Sans KR", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 20% 0%, rgba(53,224,193,.07), transparent 28%),
                radial-gradient(circle at 90% 10%, rgba(108,140,255,.08), transparent 25%),
                #081018;
            color: var(--text);
        }

        [data-testid="stSidebar"] {
            background: #09121C;
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stMultiSelect label,
        [data-testid="stSidebar"] .stTextInput label {
            color: #AAB6C8;
        }

        .block-container {
            max-width: 1480px;
            padding-top: 2.1rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3, h4 { letter-spacing: -0.03em; }

        .brand {
            padding: 5px 3px 24px 3px;
        }
        .brand-mark {
            font-size: 12px;
            font-weight: 800;
            letter-spacing: .16em;
            color: var(--cyan);
        }
        .brand-name {
            font-size: 23px;
            line-height: 1;
            font-weight: 800;
            margin-top: 7px;
            color: white;
        }
        .brand-sub {
            color: #6F7E91;
            font-size: 11px;
            margin-top: 8px;
        }

        .hero {
            position: relative;
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 26px;
            background:
                linear-gradient(110deg, rgba(16,28,41,.98), rgba(11,20,31,.93)),
                #0E1722;
            padding: 42px 44px;
            margin-bottom: 22px;
            box-shadow: 0 30px 80px rgba(0,0,0,.20);
        }
        .hero.compact { padding: 34px 40px; }
        .hero:after {
            content: "";
            position: absolute;
            right: -80px;
            top: -120px;
            width: 420px;
            height: 420px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(53,224,193,.18), rgba(53,224,193,0) 68%);
        }
        .hero-eyebrow {
            color: var(--cyan);
            font-size: 12px;
            letter-spacing: .16em;
            font-weight: 800;
            margin-bottom: 18px;
        }
        .hero-title {
            color: white;
            font-size: clamp(36px, 5vw, 64px);
            line-height: 1.03;
            font-weight: 800;
            letter-spacing: -.055em;
            max-width: 920px;
            margin: 0;
        }
        .hero.compact .hero-title {
            font-size: clamp(32px, 4vw, 52px);
        }
        .hero-subtitle {
            max-width: 760px;
            color: #A6B3C4;
            font-size: 16px;
            line-height: 1.75;
            margin-top: 18px;
        }
        .hero-tag {
            display: inline-block;
            margin-top: 22px;
            color: #C7D0DD;
            border: 1px solid var(--line);
            background: rgba(255,255,255,.025);
            border-radius: 999px;
            padding: 7px 11px;
            font-size: 11px;
            letter-spacing: .06em;
        }

        .metric-card {
            height: 132px;
            border: 1px solid var(--line);
            background: linear-gradient(180deg, rgba(16,28,41,.94), rgba(12,22,33,.94));
            border-radius: 18px;
            padding: 20px 20px;
        }
        .metric-label {
            color: #8795A8;
            font-size: 12px;
            font-weight: 600;
        }
        .metric-value {
            color: white;
            font-size: 34px;
            font-weight: 800;
            margin-top: 7px;
            letter-spacing: -.04em;
        }
        .metric-delta {
            font-size: 11px;
            color: #6F8095;
            margin-top: 2px;
        }
        .metric-delta.positive { color: var(--cyan); }

        .section-wrap {
            margin-top: 6px;
            margin-bottom: 12px;
        }
        .section-title {
            font-size: 20px;
            font-weight: 800;
            color: white;
            letter-spacing: -.03em;
        }
        .section-sub {
            font-size: 12px;
            color: #748397;
            margin-top: 4px;
        }

        .insight {
            border: 1px solid var(--line);
            border-radius: 16px;
            background: rgba(15,26,38,.84);
            padding: 16px 17px;
            margin-bottom: 10px;
        }
        .insight-title {
            color: #F4F7FB;
            font-size: 13px;
            font-weight: 700;
            line-height: 1.45;
        }
        .insight-body {
            color: #94A2B5;
            font-size: 12px;
            line-height: 1.6;
            margin-top: 6px;
        }
        .insight-meta {
            color: var(--cyan);
            font-size: 10px;
            margin-top: 9px;
            font-weight: 600;
        }

        .policy-card {
            border: 1px solid var(--line);
            background: rgba(14,23,34,.92);
            border-radius: 18px;
            padding: 20px 22px;
            margin-bottom: 10px;
            transition: all .2s ease;
        }
        .policy-card:hover {
            border-color: rgba(53,224,193,.25);
            transform: translateY(-1px);
        }
        .policy-top {
            display:flex;
            gap:8px;
            align-items:center;
            flex-wrap:wrap;
            margin-bottom: 10px;
        }
        .chip {
            display:inline-block;
            padding:5px 8px;
            border-radius:999px;
            background: rgba(108,140,255,.11);
            border:1px solid rgba(108,140,255,.20);
            color:#B8C5FF;
            font-size:10px;
            font-weight:700;
        }
        .stage {
            display:inline-block;
            padding:5px 8px;
            border-radius:999px;
            background: rgba(53,224,193,.09);
            border:1px solid rgba(53,224,193,.17);
            color:#74E8D1;
            font-size:10px;
            font-weight:700;
        }
        .muted { color:#758397; font-size:11px; }
        .policy-title {
            color:white;
            font-size:17px;
            font-weight:750;
            line-height:1.45;
            letter-spacing:-.02em;
        }
        .policy-summary {
            color:#97A5B7;
            font-size:13px;
            line-height:1.65;
            margin-top:8px;
        }
        .policy-bottom {
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-top:14px;
            padding-top:12px;
            border-top:1px solid rgba(255,255,255,.055);
            color:#69798D;
            font-size:11px;
        }
        .impact {
            color:#EAF0F8;
            font-weight:700;
        }

        .signal-row {
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding: 12px 0;
            border-bottom:1px solid rgba(255,255,255,.055);
        }
        .signal-title { color:#E8EDF5; font-size:13px; font-weight:600; }
        .signal-meta { color:#657488; font-size:10px; margin-top:4px; }
        .signal-score {
            min-width:46px;
            text-align:center;
            border:1px solid rgba(53,224,193,.16);
            background:rgba(53,224,193,.07);
            color:#64E5CC;
            border-radius:10px;
            padding:7px 8px;
            font-size:13px;
            font-weight:800;
        }

        .layer-label {
            color:#758498;
            letter-spacing:.12em;
            font-size:10px;
            font-weight:800;
            margin:14px 0 8px 2px;
        }
        .org-card {
            min-height:155px;
            border:1px solid var(--line);
            border-radius:17px;
            background:rgba(14,23,34,.9);
            padding:18px;
        }
        .org-kind { color:#66768A; font-size:10px; letter-spacing:.08em; }
        .org-name { color:white; font-size:16px; font-weight:800; margin-top:7px; }
        .org-role { color:#91A0B3; font-size:12px; line-height:1.55; margin-top:7px; }
        .org-watch { color:var(--cyan); font-size:9px; margin-top:12px; font-weight:700; }

        .signal-card {
            min-height:128px;
            border:1px solid var(--line);
            border-radius:17px;
            background:rgba(14,23,34,.9);
            padding:17px 19px;
        }
        .signal-topline {
            display:flex;
            gap:9px;
            align-items:center;
            margin-bottom:10px;
        }
        .signal-big-title { color:white; font-size:16px; font-weight:800; }
        .signal-desc { color:#8C9AAD; font-size:12px; line-height:1.6; margin-top:7px; }
        .score-ring {
            height:128px;
            border:1px solid rgba(53,224,193,.18);
            border-radius:17px;
            background:linear-gradient(180deg, rgba(53,224,193,.08), rgba(53,224,193,.025));
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
        }
        .score-number { color:#71E8D0; font-size:30px; font-weight:800; }
        .score-label { color:#6F807F; font-size:9px; letter-spacing:.12em; margin-top:3px; }

        .empty {
            border:1px dashed rgba(255,255,255,.12);
            border-radius:18px;
            padding:45px 30px;
            text-align:center;
            color:#8C9AAF;
        }
        .empty-title { color:#DCE4EF; font-size:16px; font-weight:700; }
        .empty-sub { font-size:12px; margin-top:5px; }

        [data-testid="stMetric"] {
            background: rgba(14,23,34,.78);
            border:1px solid var(--line);
            padding: 14px 16px;
            border-radius: 14px;
        }

        .stSelectbox > div > div,
        .stTextInput > div > div > input {
            border-radius:12px !important;
        }

        footer { visibility: hidden; }
        #MainMenu { visibility: hidden; }

        @media (max-width: 800px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
            .hero { padding: 30px 24px; }
            .hero-title { font-size: 38px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand():
    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
                <div class="brand-mark">HEALTH INTELLIGENCE</div>
                <div class="brand-name">HealthScope AI</div>
                <div class="brand-sub">Policy · Market · Signals</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def hero(eyebrow, title, subtitle, tag="", compact=False):
    cls = "hero compact" if compact else "hero"
    st.markdown(
        f"""
        <section class="{cls}">
            <div class="hero-eyebrow">{eyebrow}</div>
            <h1 class="hero-title">{title}</h1>
            <div class="hero-subtitle">{subtitle}</div>
            <div class="hero-tag">{tag}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label, value, delta="", sentiment="neutral"):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-delta {sentiment}">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title, subtitle=""):
    st.markdown(
        f"""
        <div class="section-wrap">
            <div class="section-title">{title}</div>
            <div class="section-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_box(title, body, meta=""):
    st.markdown(
        f"""
        <div class="insight">
            <div class="insight-title">{title}</div>
            <div class="insight-body">{body}</div>
            <div class="insight-meta">{meta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def policy_card(row, expanded=False):
    st.markdown(
        f"""
        <div class="policy-card">
            <div class="policy-top">
                <span class="chip">{row['category']}</span>
                <span class="stage">{row['stage']}</span>
                <span class="muted">{row['ministry']} · {row['date']}</span>
            </div>
            <div class="policy-title">{row['title']}</div>
            <div class="policy-summary">{row['summary']}</div>
            <div class="policy-bottom">
                <span>{row['keywords']}</span>
                <span class="impact">IMPACT {row['impact_score']}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if expanded:
        with st.expander("왜 중요한가"):
            st.write(row["why_it_matters"])


def status_badge(text):
    st.markdown(f"<span class='stage'>{text}</span>", unsafe_allow_html=True)


def empty_state(title, subtitle):
    st.markdown(
        f"""
        <div class="empty">
            <div class="empty-title">{title}</div>
            <div class="empty-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
'''

policies = [
    ["2026-09-18","보건복지부","디지털헬스","추진중","보건의료 데이터 활용 생태계 고도화 추진","공공·임상 데이터의 안전한 활용과 연구 연계를 강화하는 정책 패키지.","의료데이터 · AI · 연구","데이터 접근성과 표준화 수준이 높아질수록 의료 AI 기업과 연구기관의 개발 비용이 낮아질 가능성이 큼.",91],
    ["2026-09-11","식품의약품안전처","AI의료기기","입법예고","AI 기반 의료기기 심사체계 정비","AI·소프트웨어 의료기기의 성능변화와 업데이트를 반영하는 심사 체계를 정비.","SaMD · AI · 규제","시장 진입 속도와 사후관리 부담을 동시에 바꿀 수 있어 의료 AI 사업자의 규제 전략에 직접적 영향.",88],
    ["2026-08-28","보건복지부","돌봄","공고","지역사회 통합돌봄 확산 사업","노인·장애인의 지역사회 계속 거주를 지원하기 위한 의료·요양·돌봄 연계 사업.","통합돌봄 · 노인 · 재활","재활, 원격모니터링, 방문건강관리 서비스의 실증·조달 기회와 연결될 수 있음.",84],
    ["2026-08-21","과학기술정보통신부","AI/R&D","공고","바이오·헬스 AI 융합 R&D 지원","의료영상, 생체신호, 신약개발 등에 AI를 적용하는 산학연 연구과제를 지원.","R&D · 생체신호 · AI","연구비 흐름이 실제 채용 수요와 산학과제 주제에 영향을 주므로 연구자·대학원생에게 중요.",82],
    ["2026-07-30","국민건강보험공단","데이터","추진중","건강보험 빅데이터 개방 확대","가명처리·분석환경 개선을 통해 건강보험 데이터 활용 범위를 확대.","건보데이터 · RWD","실사용데이터 기반 연구와 헬스케어 서비스 검증 가능성이 확대될 수 있음.",79],
    ["2026-07-15","보건복지부","의료서비스","추진중","비대면진료 제도 정비 논의","비대면진료의 대상, 전달체계, 플랫폼 역할과 안전관리 기준을 정비하는 논의.","비대면진료 · 플랫폼","플랫폼 기업뿐 아니라 1차의료, 약국, 환자경험, 데이터 흐름에 폭넓은 영향을 줄 수 있음.",87],
    ["2026-06-24","산업통상자원부","로봇","공고","재활·돌봄 로봇 실증 지원","병원과 지역 돌봄 현장에 재활·돌봄 로봇을 실증하는 사업.","재활로봇 · 실증 · 조달","기술성뿐 아니라 병원 workflow와 비용효과성 검증이 중요해지는 신호.",90],
    ["2026-06-09","질병관리청","예방","발표","만성질환 예방관리 데이터 연계 강화","지역 건강지표와 만성질환 관리사업의 데이터 연계를 강화.","예방 · 만성질환 · 지역보건","예방 중심 헬스케어 서비스와 공공데이터 기반 연구의 활용 범위를 넓힐 수 있음.",72],
    ["2026-05-19","보건복지부","인력","발표","보건의료 전문인력 양성 강화","디지털헬스·바이오헬스 융합 인재 양성사업을 확대.","인력 · 교육 · 디지털헬스","교육과 채용이 연결되는 영역으로 대학·연구실·기업의 인력 수요 방향을 읽는 단서.",76],
    ["2026-05-03","한국보건산업진흥원","사업화","공고","디지털헬스케어 해외진출 지원","국내 디지털헬스 기업의 해외 실증·인허가·사업개발을 지원.","해외진출 · 사업화","국내 규제 적합성만으로는 부족하고 글로벌 임상·인허가 역량이 중요해지는 흐름.",74],
]
import csv
with open(root/"data/policies.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["date","ministry","category","stage","title","summary","keywords","why_it_matters","impact_score"]); w.writerows(policies)

signals = [
    ["2026-09-19","규제","AI 의료기기 규제 체계 정교화","정책 모니터","AI 소프트웨어 의료기기의 지속 업데이트를 규제 체계가 어떻게 수용할지가 핵심 이슈로 부상.",94],
    ["2026-09-15","기술","생체신호 + 멀티모달 AI 연구 증가","R&D 모니터","EMG·ECG·IMU·영상 등 이질적 신호를 함께 학습하는 연구가 확대되는 흐름.",90],
    ["2026-09-12","시장","병원 PoC 이후 실제 구매 전환 압력 증가","산업 모니터","단순 실증보다 실제 비용절감·workflow 개선을 입증해야 하는 요구가 커지는 추세.",86],
    ["2026-09-08","정책","지역사회 통합돌봄과 디지털 모니터링 결합","정책 모니터","고령자의 재가 생활을 지원하기 위한 원격 모니터링·재활 서비스의 정책적 접점 증가.",84],
    ["2026-09-02","데이터","RWD 기반 성능평가 중요성 확대","데이터 모니터","실사용데이터로 제품 효과와 안전성을 설명하려는 수요가 커짐.",82],
    ["2026-08-27","투자","B2B 의료 AI의 수익모델 검증 압력","시장 모니터","기술 정확도보다 구매 주체·수가·병원 예산과 연결되는 사업모델이 투자 판단에서 중요.",81],
    ["2026-08-12","기술","재활로봇의 개인화 제어 고도화","R&D 모니터","근전도·보행 데이터 기반 개인화 제어와 human-in-the-loop 접근이 활발.",88],
]
with open(root/"data/signals.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["date","category","signal","source","description","score"]); w.writerows(signals)

orgs = [
    ["정책·법제","중앙부처","보건복지부","복지부","보건의료 정책, 보험, 공공의료, 돌봄의 핵심 정책부처","보건의료 정책·예산·법령",100,100,80],
    ["정책·법제","규제기관","식품의약품안전처","식약처","의약품·의료기기 안전성과 인허가 규제","AI/SaMD 의료기기 규제",90,92,70],
    ["정책·법제","중앙부처","과학기술정보통신부","과기정통부","AI·데이터·R&D 정책 및 연구개발 투자","AI·바이오 R&D 공고",88,78,72],
    ["사업·집행","진흥기관","한국보건산업진흥원","진흥원","보건산업 육성, R&D, 사업화, 해외진출 지원","지원사업·R&D·산업통계",72,82,76],
    ["사업·집행","보험자","국민건강보험공단","건보공단","건강보험 자격·보험료·건강검진 및 빅데이터","건보데이터·보장성",78,90,95],
    ["사업·집행","평가기관","건강보험심사평가원","심평원","급여 심사·평가 및 의료이용 데이터 관리","급여·수가·의료질",85,95,94],
    ["평가·데이터","공공기관","질병관리청","질병청","감염병·만성질환·건강조사와 공중보건","건강조사·역학데이터",75,74,92],
    ["평가·데이터","통계기관","국가데이터처","데이터처","국가 통계와 데이터 기반 정책 지원","보건·인구·산업통계",70,66,96],
    ["평가·데이터","연구기관","한국보건사회연구원","보사연","보건·복지 정책 연구와 정책평가","정책연구·인구·복지",68,65,88],
]
with open(root/"data/organizations.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["layer","type","name","short","role","watch","policy_power","market_influence","data_richness"]); w.writerows(orgs)

files["requirements.txt"] = """streamlit==1.64.0
pandas>=2.2,<3
plotly>=6.0,<7
"""

files[".streamlit/config.toml"] = r'''
[theme]
base = "dark"
primaryColor = "#35E0C1"
backgroundColor = "#081018"
secondaryBackgroundColor = "#0E1722"
textColor = "#F4F7FB"
font = "sans serif"

[server]
headless = true

[browser]
gatherUsageStats = false
'''

files[".gitignore"] = """__pycache__/
*.py[cod]
.venv/
venv/
.env
.streamlit/secrets.toml
.DS_Store
"""

files["README.md"] = r'''
# HealthScope AI

정부 정책·산업 신호·기관 구조를 한 화면에서 탐색하는 Streamlit 기반 헬스케어 정책 인텔리전스 프로토타입입니다.

## 주요 기능

- Executive Dashboard
- 정책 검색 / 기관·분야·상태 필터
- 정책 영향도 시각화
- 산업 Trend Signal Board
- 기관 Ecosystem Map
- 반응형 다크 UI
- 샘플 CSV 데이터 분리
- GitHub → Streamlit Community Cloud 즉시 배포 가능

## 로컬 실행

```bash
git clone <YOUR_REPOSITORY_URL>
cd health_policy_intelligence

python -m venv .venv

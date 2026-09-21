import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(
    page_title="HealthScope AI",
    page_icon="🫀",
    layout="wide",
)


POLICIES = [
    {
        "date": "2026-09-18",
        "ministry": "보건복지부",
        "category": "디지털헬스",
        "stage": "추진중",
        "title": "보건의료 데이터 활용 생태계 고도화",
        "summary": "공공·임상 데이터의 안전한 활용과 연구 연계를 강화하는 정책.",
        "impact_score": 91,
    },
    {
        "date": "2026-09-11",
        "ministry": "식품의약품안전처",
        "category": "AI 의료기기",
        "stage": "입법예고",
        "title": "AI 기반 의료기기 심사체계 정비",
        "summary": "AI·소프트웨어 의료기기의 성능변화와 업데이트를 반영하는 심사체계 정비.",
        "impact_score": 88,
    },
    {
        "date": "2026-08-28",
        "ministry": "보건복지부",
        "category": "돌봄",
        "stage": "공고",
        "title": "지역사회 통합돌봄 확산 사업",
        "summary": "노인·장애인의 지역사회 계속 거주를 위한 의료·요양·돌봄 연계 사업.",
        "impact_score": 84,
    },
    {
        "date": "2026-08-21",
        "ministry": "과학기술정보통신부",
        "category": "AI/R&D",
        "stage": "공고",
        "title": "바이오·헬스 AI 융합 R&D 지원",
        "summary": "의료영상, 생체신호, 신약개발 등에 AI를 적용하는 연구과제 지원.",
        "impact_score": 82,
    },
    {
        "date": "2026-07-15",
        "ministry": "보건복지부",
        "category": "의료서비스",
        "stage": "추진중",
        "title": "비대면진료 제도 정비",
        "summary": "비대면진료 대상, 플랫폼 역할 및 안전관리 기준 정비.",
        "impact_score": 87,
    },
]

SIGNALS = [
    {
        "signal": "AI 의료기기 규제 체계 정교화",
        "category": "규제",
        "score": 94,
    },
    {
        "signal": "생체신호 + 멀티모달 AI 연구 증가",
        "category": "기술",
        "score": 90,
    },
    {
        "signal": "병원 PoC 이후 실제 구매 전환 압력",
        "category": "시장",
        "score": 86,
    },
    {
        "signal": "지역사회 통합돌봄과 디지털 모니터링 결합",
        "category": "정책",
        "score": 84,
    },
]

policy_df = pd.DataFrame(POLICIES)
signal_df = pd.DataFrame(SIGNALS)


st.sidebar.title("HealthScope AI")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Policy Explorer",
        "Trend Signals",
        "About",
    ],
)


if page == "Dashboard":
    st.title("HealthScope AI")
    st.caption("Healthcare Policy & Market Intelligence")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("추적 정책", len(policy_df))

    with col2:
        st.metric(
            "평균 영향도",
            round(policy_df["impact_score"].mean(), 1),
        )

    with col3:
        st.metric("산업 신호", len(signal_df))

    st.divider()

    st.subheader("정책 분야별 분포")

    category_data = (
        policy_df.groupby("category")
        .size()
        .reset_index(name="count")
    )

    fig = px.bar(
        category_data,
        x="category",
        y="count",
        title="정책 분야",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.subheader("주요 정책")

    sorted_df = policy_df.sort_values(
        "impact_score",
        ascending=False,
    )

    for _, row in sorted_df.iterrows():
        with st.container(border=True):
            st.markdown(f"### {row['title']}")
            st.caption(
                f"{row['ministry']} · "
                f"{row['date']} · "
                f"{row['stage']}"
            )
            st.write(row["summary"])
            st.write(
                f"Impact Score: "
                f"**{row['impact_score']}**"
            )


elif page == "Policy Explorer":
    st.title("Policy Explorer")

    keyword = st.text_input(
        "검색",
        placeholder="예: AI, 데이터, 돌봄",
    )

    ministry = st.selectbox(
        "기관",
        ["전체"] + sorted(
            policy_df["ministry"]
            .unique()
            .tolist()
        ),
    )

    filtered = policy_df.copy()

    if ministry != "전체":
        filtered = filtered[
            filtered["ministry"] == ministry
        ]

    if keyword:
        q = keyword.lower()

        filtered = filtered[
            filtered["title"]
            .str.lower()
            .str.contains(q, na=False)
            |
            filtered["summary"]
            .str.lower()
            .str.contains(q, na=False)
        ]

    st.write(f"검색 결과: {len(filtered)}건")

    for _, row in filtered.iterrows():
        with st.container(border=True):
            st.markdown(f"### {row['title']}")
            st.caption(
                f"{row['ministry']} · "
                f"{row['category']} · "
                f"{row['stage']}"
            )
            st.write(row["summary"])
            st.metric(
                "Impact Score",
                int(row["impact_score"]),
            )


elif page == "Trend Signals":
    st.title("Trend Signals")

    min_score = st.slider(
        "최소 Signal Score",
        0,
        100,
        70,
    )

    filtered_signals = signal_df[
        signal_df["score"] >= min_score
    ].sort_values(
        "score",
        ascending=False,
    )

    for _, row in filtered_signals.iterrows():
        with st.container(border=True):
            st.subheader(row["signal"])
            st.caption(row["category"])
            st.metric(
                "Signal Score",
                int(row["score"]),
            )


elif page == "About":
    st.title("About HealthScope AI")

    st.write(
        """
        HealthScope AI는 헬스케어 관련 정부 정책,
        산업 변화, 기술 신호를 구조적으로 탐색하기 위한
        Streamlit 기반 프로토타입입니다.
        """
    )

    st.subheader("향후 개발 방향")

    st.markdown(
        """
        - 보건복지부 정책 자동 수집
        - 식약처 의료기기 규제 모니터링
        - 정부 R&D 사업 자동 수집
        - AI 정책 요약
        - 정책 영향도 자동 분석
        - 기업 및 기관 Knowledge Graph
        - 개인화 정책 알림
        """
    )

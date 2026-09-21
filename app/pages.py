```python
import pandas as pd
import plotly.express as px
import streamlit as st

from app.data import load_policy_data, load_signal_data, load_organizations
from app.ui import section_header


class dashboard:
    @staticmethod
    def render():
        st.title("HealthScope AI")
        st.caption("Healthcare Policy & Market Intelligence")

        policies_df = load_policy_data()
        signals_df = load_signal_data()
        orgs_df = load_organizations()

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("정책 수", len(policies_df))

        with c2:
            st.metric("산업 신호", len(signals_df))

        with c3:
            st.metric("관찰 기관", len(orgs_df))

        st.divider()

        section_header("정책 분야 분포")

        if not policies_df.empty:
            category_counts = (
                policies_df.groupby("category")
                .size()
                .reset_index(name="count")
            )

            fig = px.bar(
                category_counts,
                x="category",
                y="count",
                title="정책 분야별 건수",
            )

            st.plotly_chart(fig, use_container_width=True)

        section_header("최근 주요 정책")

        for _, row in policies_df.sort_values(
            "impact_score",
            ascending=False
        ).head(5).iterrows():
            with st.container(border=True):
                st.subheader(row["title"])
                st.caption(
                    f"{row['ministry']} · {row['date']} · {row['category']}"
                )
                st.write(row["summary"])
                st.write(f"영향도: **{row['impact_score']}**")


class policies:
    @staticmethod
    def render():
        st.title("Policy Explorer")
        st.caption("정부 정책과 사업을 탐색합니다.")

        df = load_policy_data()

        col1, col2 = st.columns(2)

        with col1:
            ministry_options = ["전체"] + sorted(
                df["ministry"].dropna().unique().tolist()
            )

            ministry = st.selectbox(
                "기관",
                ministry_options,
            )

        with col2:
            category_options = ["전체"] + sorted(
                df["category"].dropna().unique().tolist()
            )

            category = st.selectbox(
                "분야",
                category_options,
            )

        query = st.text_input(
            "검색",
            placeholder="예: AI, 디지털헬스, 의료데이터",
        )

        filtered = df.copy()

        if ministry != "전체":
            filtered = filtered[
                filtered["ministry"] == ministry
            ]

        if category != "전체":
            filtered = filtered[
                filtered["category"] == category
            ]

        if query:
            q = query.lower()

            filtered = filtered[
                filtered["title"]
                .astype(str)
                .str.lower()
                .str.contains(q, na=False)
                |
                filtered["summary"]
                .astype(str)
                .str.lower()
                .str.contains(q, na=False)
            ]

        st.write(f"검색 결과: **{len(filtered)}건**")

        for _, row in filtered.sort_values(
            "impact_score",
            ascending=False
        ).iterrows():

            with st.container(border=True):
                st.subheader(row["title"])

                st.caption(
                    f"{row['ministry']} · "
                    f"{row['date']} · "
                    f"{row['stage']}"
                )

                st.write(row["summary"])

                st.write(
                    f"**키워드:** {row['keywords']}"
                )

                st.write(
                    f"**영향도:** {row['impact_score']}"
                )

                with st.expander("왜 중요한가"):
                    st.write(row["why_it_matters"])


class organizations:
    @staticmethod
    def render():
        st.title("Organization Map")
        st.caption("헬스케어 정책·사업 생태계")

        df = load_organizations()

        for layer in df["layer"].unique():

            st.subheader(layer)

            subset = df[
                df["layer"] == layer
            ]

            cols = st.columns(3)

            for i, (_, row) in enumerate(
                subset.iterrows()
            ):
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(
                            f"### {row['name']}"
                        )

                        st.caption(row["type"])

                        st.write(row["role"])

                        st.write(
                            f"**관찰 포인트:** "
                            f"{row['watch']}"
                        )


class signals:
    @staticmethod
    def render():
        st.title("Trend Signals")
        st.caption("시장·기술·정책 변화를 관찰합니다.")

        df = load_signal_data()

        min_score = st.slider(
            "최소 신호 점수",
            min_value=0,
            max_value=100,
            value=60,
        )

        filtered = df[
            df["score"] >= min_score
        ].sort_values(
            "score",
            ascending=False
        )

        for _, row in filtered.iterrows():

            with st.container(border=True):
                st.subheader(row["signal"])

                st.caption(
                    f"{row['category']} · "
                    f"{row['date']} · "
                    f"{row['source']}"
                )

                st.write(row["description"])

                st.metric(
                    "Signal Score",
                    int(row["score"]),
                )


class about:
    @staticmethod
    def render():
        st.title("About HealthScope AI")

        st.write(
            """
            HealthScope AI는 헬스케어 관련 정부 정책,
            산업 변화, 기관 구조를 한 화면에서
            탐색하기 위한 정책 인텔리전스
            프로토타입입니다.
            """
        )

        st.subheader("향후 개발 방향")

        st.markdown(
            """
            - 정부기관 API 및 RSS 연동
            - 보건복지부·식약처 공고 자동 수집
            - AI 정책 요약
            - 산업 영향도 분석
            - 개인화 관심 키워드
            - 정책 변화 알림
            - 기업·기관 Knowledge Graph
            """
        )
```

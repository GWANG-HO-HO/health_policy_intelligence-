import streamlit as st


def inject_global_css():
    st.markdown(
        """
        <style>
        .stApp {
            background: #081018;
            color: #F4F7FB;
        }

        [data-testid="stSidebar"] {
            background: #09121C;
        }

        .brand {
            padding: 8px 4px 24px 4px;
        }

        .brand-mark {
            color: #35E0C1;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.12em;
        }

        .brand-name {
            color: white;
            font-size: 24px;
            font-weight: 800;
            margin-top: 6px;
        }

        .brand-sub {
            color: #7F8EA3;
            font-size: 11px;
            margin-top: 6px;
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

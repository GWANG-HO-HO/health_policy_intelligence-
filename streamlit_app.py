```python
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
        st.Page(
            dashboard.render,
            title="Executive Dashboard",
            icon=":material/space_dashboard:",
            default=True,
        ),
        st.Page(
            policies.render,
            title="Policy Explorer",
            icon=":material/policy:",
        ),
        st.Page(
            signals.render,
            title="Trend Signals",
            icon=":material/query_stats:",
        ),
    ],
    "ECOSYSTEM": [
        st.Page(
            organizations.render,
            title="Organization Map",
            icon=":material/account_tree:",
        ),
    ],
    "ABOUT": [
        st.Page(
            about.render,
            title="About",
            icon=":material/info:",
        ),
    ],
}

pg = st.navigation(pages, position="sidebar")
pg.run()
```

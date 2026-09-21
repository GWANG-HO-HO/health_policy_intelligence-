from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(**file**).resolve().parents[1]
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

from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(**file**).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

@st.cache_data
def load_policy_data():
file_path = DATA_DIR / "policies.csv"
return pd.read_csv(file_path)

@st.cache_data
def load_signal_data():
file_path = DATA_DIR / "signals.csv"
return pd.read_csv(file_path)

@st.cache_data
def load_organizations():
file_path = DATA_DIR / "organizations.csv"
return pd.read_csv(file_path)


import streamlit as st
import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# import datetime
# import calendar

# --------------------
# PAGE SETUP
# --------------------
st.set_page_config(layout="wide")
st.title("Book Analysis (CSV File Updated 25 May 2025)")

# --------------------
# LOAD AND CLEAN DATA
# --------------------
# @st.cache_data
# def load_data():
#     df = pd.read_csv("books.csv")

# df = load_data()

df = pd.read_csv("books.csv")

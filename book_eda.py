# --------------------
# IMPORT LIBRARIES
# --------------------
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from cycler import cycler

# --------------------
# PAGE SETUP
# --------------------
st.set_page_config(layout="centered")
THEME_COLORS = ["#0097b2", "#32c5a8", "#ec3d77", "#ff8839", "#56bb70", "#ff00bf"]
plt.rcParams['axes.prop_cycle'] = cycler('color', THEME_COLORS)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Patrick+Hand&display=swap');
    .title {
        color: #0097b2;
        font-family: 'Patrick Hand', cursive;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown('<h1 class="title">Book Analytics Dashboard</h1>', unsafe_allow_html=True)

# --------------------
# LOAD AND CLEAN DATA
# --------------------
# @st.cache_data
def loadData():
    df = pd.read_csv("mergedBooks.csv")
    books = df[[
        "Title", "Author", "Publisher",
        "Average Rating", "Number of Ratings", "Pages",
        "Year Published",
        "Date Added", "Date Read",
        "Genres", "Summary", "Exclusive Shelf"
    ]].copy()

    # parse dates & years
    books["Date Added"] = pd.to_datetime(books["Date Added"], errors="coerce")
    books["Date Read"]  = pd.to_datetime(books["Date Read"],  errors="coerce")
    books["Year Published"] = pd.to_numeric(books["Year Published"], errors="coerce").astype('Int64')

    # normalize shelf
    books["Shelf"] = books["Exclusive Shelf"].map({
        "read": "read",
        "to-read": "want-to-read"
    }).fillna("other")

    # determine read / want-to-read
    books["HasBeenRead"]  = (books["Shelf"] == "read")  | books["Average Rating"].notna()
    books["WantToRead"]   = books["Shelf"] == "want-to-read"

    return books.reset_index(drop=True)

books = loadData()

# --------------------
# SIDEBAR: GENRE FILTER
# --------------------
allGenres = sorted({g.strip() for sub in books["Genres"].dropna().str.split(",") for g in sub})
selectedGenres = st.sidebar.multiselect("Filter by Genre", allGenres)

if selectedGenres:
    books = books[books["Genres"].apply(
        lambda cell: any(g in cell for g in selectedGenres) if pd.notna(cell) else False
    )].reset_index(drop=True)

# --------------------
# SIDEBAR: DETAIL FILTERS
# --------------------
with st.sidebar.expander("Filter details"):
    minRating, maxRating = st.slider(
        "Average Rating",
        float(books["Average Rating"].min()), float(books["Average Rating"].max()),
        (float(books["Average Rating"].min()), float(books["Average Rating"].max())),
        step=0.1
    )
    minYear, maxYear = st.slider(
        "Year Published",
        int(books["Year Published"].min()), int(books["Year Published"].max()),
        (int(books["Year Published"].min()), int(books["Year Published"].max()))
    )
    minPages, maxPages = st.slider(
        "Page Count",
        int(books["Pages"].min()), int(books["Pages"].max()),
        (int(books["Pages"].min()), int(books["Pages"].max()))
    )
    # apply detail filters
    books = books[
        (books["Average Rating"].between(minRating, maxRating)) &
        (books["Year Published"].between(minYear, maxYear))      &
        (books["Pages"].between(minPages, maxPages))
    ].reset_index(drop=True)

# --------------------
# SUMMARY CARDS
# --------------------
col1, col2 = st.columns(2)
col1.metric("Books Read",       int(books["HasBeenRead"].sum()))
col2.metric("Want to Read",     int(books["WantToRead"].sum()))

# --------------------
# BOOK LIST
# --------------------
st.subheader(
    "Books List" +
    (f" – Genres: {', '.join(selectedGenres)}" if selectedGenres else "")
)
st.dataframe(
    books[[
        "Title", "Author", "Publisher",
        "Year Published", "Pages",
        "Average Rating", "Number of Ratings",
        "Shelf"
    ]],
    use_container_width=True
)

# --------------------
# EDA: READING TIMELINE
# --------------------
st.subheader("Monthly Books Added")
fig, ax = plt.subplots()
books.groupby(books["Date Added"].dt.to_period("M")).size().plot(ax=ax)
ax.set_title("Books Added Over Time")
ax.set_xlabel("Month")
ax.set_ylabel("Count")
plt.xticks(rotation=45)
st.pyplot(fig)

st.subheader("Cumulative Books Read")
fig, ax = plt.subplots()
books[books["HasBeenRead"]].groupby(books["Date Read"].dt.to_period("M")).size().cumsum().plot(ax=ax)
ax.set_title("Cumulative Read Over Time")
ax.set_xlabel("Month")
ax.set_ylabel("Cumulative Count")
plt.xticks(rotation=45)
st.pyplot(fig)

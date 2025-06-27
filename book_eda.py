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
        margin-bottom: 0.5em;
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
        "Year Published", "Date Added", "Date Read",
        "Genres", "Summary", "Exclusive Shelf"
    ]].copy()

    # parse dates & numeric year/pages
    books["Date Added"]    = pd.to_datetime(books["Date Added"], errors="coerce")
    books["Date Read"]     = pd.to_datetime(books["Date Read"],  errors="coerce")
    books["Year Published"]= pd.to_numeric(books["Year Published"], errors="coerce")
    books["Pages"]         = pd.to_numeric(books["Pages"], errors="coerce")

    # normalize shelf
    books["Shelf"] = books["Exclusive Shelf"].map({
        "read": "read",
        "to-read": "want-to-read"
    }).fillna("other")

    # determine read/want-to-read
    books["HasBeenRead"]  = (books["Shelf"] == "read") | books["Average Rating"].notna()
    books["WantToRead"]   = books["Shelf"] == "want-to-read"

    return books.reset_index(drop=True)

books = loadData()

# --------------------
# SIDEBAR: COLUMN PICKER
# --------------------
allCols = list(books.columns)
defaultCols = ["Title", "Author", "Year Published", "Pages", "Average Rating", "Shelf"]
visibleCols = st.sidebar.multiselect("Visible columns", allCols, default=defaultCols)

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
with st.sidebar.expander("More filters"):
    # ensure no NAs before min/max
    rating_series = books["Average Rating"].dropna()
    year_series   = books["Year Published"].dropna().astype(int)
    pages_series  = books["Pages"].dropna().astype(int)

    minRating = float(rating_series.min())
    maxRating = float(rating_series.max())
    minYear   = int(year_series.min())
    maxYear   = int(year_series.max())
    minPages  = int(pages_series.min())
    maxPages  = int(pages_series.max())

    selRating = st.slider("Average Rating", minRating, maxRating, (minRating, maxRating), 0.1)
    selYear   = st.slider("Year Published", minYear, maxYear, (minYear, maxYear))
    selPages  = st.slider("Page Count", minPages, maxPages, (minPages, maxPages))

    books = books[
        (books["Average Rating"].between(*selRating)) &
        (books["Year Published"].between(*selYear))   &
        (books["Pages"].between(*selPages))
    ].reset_index(drop=True)

# --------------------
# SUMMARY CARDS
# --------------------
col1, col2 = st.columns(2)
col1.metric("Books Read",   int(books["HasBeenRead"].sum()))
col2.metric("Want to Read", int(books["WantToRead"].sum()))

# helper for dynamic titles
def makeTitle(base):
    if selectedGenres:
        return f"{base} (Genres: {', '.join(selectedGenres)})"
    return base

# --------------------
# BOOK LIST
# --------------------
st.subheader(makeTitle("Books List"))
st.dataframe(books[visibleCols], use_container_width=True)

# --------------------
# EDA: TIMELINES
# --------------------
st.subheader(makeTitle("Monthly Books Added"))
fig, ax = plt.subplots()
books.groupby(books["Date Added"].dt.to_period("M")).size().plot(ax=ax)
ax.set_xlabel("Month")
ax.set_ylabel("Count Added")
ax.set_title("Books Added Over Time")
plt.xticks(rotation=45)
st.pyplot(fig)

st.subheader(makeTitle("Cumulative Books Read"))
fig, ax = plt.subplots()
books[books["HasBeenRead"]].groupby(books["Date Read"].dt.to_period("M")).size().cumsum().plot(ax=ax)
ax.set_xlabel("Month")
ax.set_ylabel("Cumulative Read")
ax.set_title("Cumulative Read Over Time")
plt.xticks(rotation=45)
st.pyplot(fig)

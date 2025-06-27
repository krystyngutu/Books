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
# theme colors, with deep turquoise default
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
        "Date Added", "Date Started", "Date Read",
        "Genres", "Summary", "Exclusive Shelf"
    ]].copy()

    # parse dates
    dateColumns = ["Date Added", "Date Started", "Date Read"]
    for col in dateColumns:
        books[col] = pd.to_datetime(books[col], errors="coerce")

    # normalize shelf values
    books["Shelf"] = books["Exclusive Shelf"].map({
        "read": "read",
        "to-read": "want-to-read",
        "currently-reading": "currently-reading"
    }).fillna("other")

    # determine read/unread
    books["HasBeenRead"] = (
        (books["Shelf"] == "read") |
        books["Average Rating"].notna()
    )
    books["WantToRead"] = books["Shelf"] == "want-to-read"
    books["CurrentlyReading"] = books["Shelf"] == "currently-reading"

    # compute reading pace
    books["DaysToRead"] = (books["Date Read"] - books["Date Started"]).dt.days

    return books.reset_index(drop=True)

books = loadData()

# --------------------
# SIDEBAR FILTERS
# --------------------
allGenres = sorted({g.strip() for sub in books["Genres"].dropna().str.split(",") for g in sub})
selected = st.sidebar.multiselect("Filter by Genre", allGenres)
if selected:
    genreMask = books["Genres"].apply(
        lambda cell: any(g in cell for g in selected) if pd.notna(cell) else False
    )
    books = books[genreMask].reset_index(drop=True)

# --------------------
# SUMMARY CARDS
# --------------------
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Books", len(books))
col2.metric("Books Read", int(books["HasBeenRead"].sum()))
col3.metric("Want to Read", int(books["WantToRead"].sum()))
col4.metric("Currently Reading", int(books["CurrentlyReading"].sum()))
col5.metric("Avg. Rating", f"{books['Average Rating'].mean():.2f}")

# helper for dynamic titles
def makeTitle(base):
    return f"{base} – filtered: {', '.join(selected)}" if selected else base

# --------------------
# EDA VISUALIZATIONS
# --------------------
st.subheader(makeTitle("Books Added Over Time"))
fig, ax = plt.subplots()
books.groupby(books["Date Added"].dt.to_period("M")).size().plot(ax=ax)
ax.set_title("Monthly Books Added")
ax.set_xlabel("Month")
ax.set_ylabel("Count")
plt.xticks(rotation=45)
st.pyplot(fig)

st.subheader(makeTitle("Cumulative Books Read"))
fig, ax = plt.subplots()
books[books["HasBeenRead"]].groupby(books["Date Read"].dt.to_period("M")).size().cumsum().plot(ax=ax)
ax.set_title("Cumulative Read Over Time")
ax.set_xlabel("Month")
ax.set_ylabel("Cumulative Count")
plt.xticks(rotation=45)
st.pyplot(fig)

st.subheader(makeTitle("Genre Distribution (Top 10)"))
genreExploded = books.assign(
    Genre=books["Genres"].str.split(",")
).explode("Genre")
genreExploded["Genre"] = genreExploded["Genre"].str.strip()
genreCounts = genreExploded["Genre"].value_counts().head(10)
fig, ax = plt.subplots()
ax.pie(genreCounts, labels=genreCounts.index, autopct="%1.1f%%", startangle=140, wedgeprops={'width':0.5})
ax.set_title("Genre Share")
st.pyplot(fig)

st.subheader(makeTitle("Pages vs. Rating"))
fig, ax = plt.subplots()
ax.scatter(books["Pages"], books["Average Rating"], alpha=0.6)
ax.set_title("Length vs. Enjoyment")
ax.set_xlabel("Pages")
ax.set_ylabel("Rating")
st.pyplot(fig)

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
st.set_page_config(layout="wide")

# Inject Patrick Hand font and style title
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Patrick+Hand&display=swap');
    .title {
        color: #ff00bf;
        font-family: 'Patrick Hand', cursive;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown('<h1 class="title">Book Analysis (Data Updated 25.05.2025)</h1>', unsafe_allow_html=True)
st.title("Book Analysis (Data Updated 25.05.2025)")

# Apply theme palette globally
THEME_COLORS = ["#ff00bf", "#0097b2", "#32c5a8", "#ec3d77", "#ff8839", "#56bb70"]
plt.rcParams['axes.prop_cycle'] = cycler('color', THEME_COLORS)

# --------------------
# LOAD AND CLEAN DATA
# --------------------
# @st.cache_data
def loadData():
    df = pd.read_csv("mergedBooks.csv")

    books = df[[
        "Title", "Author", "Additional Authors", "Publisher",
        "Average Rating", "Number of Ratings", "My Rating",
        "My Review", "Number of Pages", "Pages",
        "Year Published", "Original Publication Year",
        "Date Published", "Date Added", "Date Started", "Date Read",
        "Summary", "Genres", "Exclusive Shelf"
    ]].copy()

    # Convert to datetime
    dateColumns = ["Date Published", "Date Added", "Date Started", "Date Read"]
    for col in dateColumns:
        books[col] = pd.to_datetime(books[col], errors="coerce")

    # Fill missing publication dates
    books["Original Publication Year"] = pd.to_numeric(books["Original Publication Year"], errors="coerce")
    books["Year Published"] = pd.to_numeric(books["Year Published"], errors="coerce")
    books["Date Published"] = (
        books["Date Published"]
        .combine_first(pd.to_datetime(books["Original Publication Year"], format="%Y", errors="coerce"))
        .combine_first(pd.to_datetime(books["Year Published"], format="%Y", errors="coerce"))
    )

    # Cleanup columns
    books.drop(columns=["Pages", "Year Published", "Original Publication Year"], inplace=True)
    books.rename(columns={"Number of Pages": "Pages"}, inplace=True)

    return books

books = loadData()

# --------------------
# CHECK FOR MISSING VALUES
# --------------------
print("Columns With Missing Values:\n", books.isna().sum())
print("\nUnique Values in Key Columns:")
for col in books:
    print(f"{col}: {books[col].nunique()} unique entries")

# --------------------
# SIDEBAR FILTERS
# --------------------
allGenres = sorted(
    {g.strip() for sub in books["Genres"].dropna().str.split(",") for g in sub}
)
selected = st.sidebar.multiselect("Filter by Genre", allGenres)

if selected:
    mask = books["Genres"].apply(
        lambda cell: any(g in cell for g in selected) if pd.notna(cell) else False
    )
    books = books[mask].reset_index(drop=True)

# --------------------
# HIGH-LEVEL METRICS
# --------------------
st.sidebar.markdown("### Summary Metrics")
st.sidebar.metric("Books Shown", len(books))
st.sidebar.metric("Avg. Rating", f"{books['Average Rating'].mean():.2f}")

# Helper for dynamic titles
def makeTitle(base):
    if selected:
        return f"{base} (Genres: {', '.join(selected)})"
    return base

# --------------------
# EDA VISUALIZATIONS
# --------------------
# 1) Timeline of Books Added
st.subheader(makeTitle("Books Added Over Time"))
fig, ax = plt.subplots()
books.groupby(books["Date Added"].dt.to_period("M")).size().plot(ax=ax)
ax.set_xlabel("Month")
ax.set_ylabel("Count")
ax.set_title(makeTitle("Monthly Books Added"))
plt.xticks(rotation=45)
st.pyplot(fig)

# 2) Histogram of Average Ratings
st.subheader(makeTitle("Distribution of Average Ratings"))
fig, ax = plt.subplots()
ax.hist(books["Average Rating"].dropna(), bins=20)
ax.set_xlabel("Average Rating")
ax.set_ylabel("Frequency")
ax.set_title(makeTitle("Ratings Histogram"))
st.pyplot(fig)

# 3) Histogram of Page Counts
st.subheader(makeTitle("Distribution of Page Counts"))
fig, ax = plt.subplots()
ax.hist(books["Pages"].dropna(), bins=20)
ax.set_xlabel("Pages")
ax.set_ylabel("Frequency")
ax.set_title(makeTitle("Pages Histogram"))
st.pyplot(fig)

# 4) Top Publishers
st.subheader(makeTitle("Top 10 Publishers by Number of Books"))
publisherCounts = books["Publisher"].value_counts().head(10)
fig, ax = plt.subplots()
publisherCounts.plot(kind="barh", ax=ax)
ax.set_xlabel("Number of Books")
ax.invert_yaxis()
ax.set_title(makeTitle("Top Publishers"))
st.pyplot(fig)

# --------------------
# TOP REPEAT AUTHORS
# --------------------
authorCounts = books["Author"].value_counts()
repeatAuthors = authorCounts[authorCounts > 1].index
authoredBooks = books[books["Author"].isin(repeatAuthors)].copy()

authoredBooks["Shelf Status"] = authoredBooks["Exclusive Shelf"].map({
    "read": "Have Read",
    "to-read": "Want to Read"
}).fillna("Other")

authorSummary = (
    authoredBooks
    .groupby(["Author", "Shelf Status"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

for col in ("Have Read", "Want to Read"):
    if col not in authorSummary:
        authorSummary[col] = 0

authorSummary["Total"] = authorSummary["Have Read"] + authorSummary["Want to Read"]
authorSummary = authorSummary.sort_values("Total", ascending=False)

st.subheader(makeTitle("Top Repeat Authors: Have Read vs Want to Read"))
fig, ax = plt.subplots(figsize=(10, 6))
authorSummary.head(10).set_index("Author")[["Have Read", "Want to Read"]].plot(
    kind="bar", stacked=True, ax=ax
)
ax.set_ylabel("Number of Books")
ax.set_title(makeTitle("Author Shelf Status Comparison"))
plt.xticks(rotation=45, ha="right")
st.pyplot(fig)

if st.checkbox("Show author breakdown table"):
    st.dataframe(authorSummary.head(20))

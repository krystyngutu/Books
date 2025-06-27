# --------------------
# IMPORT LIBRARIES
# --------------------
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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

# --------------------
# LOAD AND CLEAN DATA
# --------------------
# @st.cache_data
def loadData():
    df = pd.read_csv("mergedBooks.csv")

    # Keep only relevant columns
    books = df[[
        "Title", "Author", "Additional Authors", "Publisher",
        "Average Rating", "Number of Ratings", "My Rating",
        "My Review", "Number of Pages", "Pages",
        "Year Published", "Original Publication Year",
        "Date Published", "Date Added", "Date Started", "Date Read",
        "Summary", "Genres", "Exclusive Shelf"
    ]].copy()

    # Convert data columns
    dateColumns = ["Date Published", "Date Added", "Date Started", "Date Read"]
    for col in dateColumns:
        books[col] = pd.to_datetime(books[col], errors="coerce")

    # Fill missing Date Published data with info from other fields
    books["Original Publication Year"] = pd.to_numeric(books["Original Publication Year"], errors="coerce")
    books["Year Published"] = pd.to_numeric(books["Year Published"], errors="coerce")

    books["Date Published"] = books["Date Published"] \
        .combine_first(pd.to_datetime(books["Original Publication Year"], format="%Y", errors="coerce")) \
        .combine_first(pd.to_datetime(books["Year Published"], format="%Y", errors="coerce"))

    books.drop(columns=["Pages", "Year Published", "Original Publication Year"], inplace=True)
    books.rename(columns={"Number of Pages": "Pages"}, inplace=True)

    return books

books = loadData()

# --------------------
# CHECK FOR MISSING VALUES
# --------------------
print(f"Columns With Missing Values:\n", books.isna().sum())
print("\n Unique Values in Key Columns:")

for col in books:
    print(f"{col}: {books[col].nunique()} unique entries")

# --------------------
# SIDEBAR FILTERS
# --------------------
# Build a list of all unique genres
allGenres = sorted(
    {g.strip() for sub in books["Genres"].dropna().str.split(",") for g in sub}
)
selected = st.sidebar.multiselect("Filter by Genre", allGenres)

# Apply genre filter
if selected:
    mask = books["Genres"].apply(
        lambda cell: any(g in cell for g in selected) if pd.notna(cell) else False
    )
    books = books[mask]

# --------------------
# HIGH-LEVEL METRICS
# --------------------
st.sidebar.markdown("### Summary Metrics")
st.sidebar.metric("Books Shown", len(books))
st.sidebar.metric("Avg. Rating", f"{books['Average Rating'].mean():.2f}")

# --------------------
# EDA VISUALIZATIONS
# --------------------
# 1) Timeline of Books Added
st.subheader("Books Added Over Time")
fig, ax = plt.subplots()
books.groupby(books["Date Added"].dt.to_period("M")).size().plot(ax=ax)
ax.set_xlabel("Month")
ax.set_ylabel("Count")
ax.set_title("Monthly Books Added")
plt.xticks(rotation=45)
st.pyplot(fig)

# 2) Histogram of Average Ratings
st.subheader("Distribution of Average Ratings")
fig, ax = plt.subplots()
ax.hist(books["Average Rating"].dropna(), bins=20)
ax.set_xlabel("Average Rating")
ax.set_ylabel("Frequency")
st.pyplot(fig)

# 3) Histogram of Page Counts
st.subheader("Distribution of Page Counts")
fig, ax = plt.subplots()
ax.hist(books["Pages"].dropna(), bins=20)
ax.set_xlabel("Pages")
ax.set_ylabel("Frequency")
st.pyplot(fig)

# 4) Top Publishers
st.subheader("Top 10 Publishers by Number of Books")
publisher_counts = books["Publisher"].value_counts().head(10)
fig, ax = plt.subplots()
publisher_counts.plot(kind="barh", ax=ax)
ax.set_xlabel("Number of Books")
ax.invert_yaxis()
st.pyplot(fig)

# --------------------
# TOP REPEAT AUTHORS
# --------------------
# Identify authors with multiple books
authorCounts = books["Author"].value_counts()
repeat = authorCounts[authorCounts > 1].index
authored = books[books["Author"].isin(repeat)].copy()

# Map shelf status
authored["Shelf Status"] = authored["Exclusive Shelf"].map({
    "read": "Have Read",
    "to-read": "Want to Read"
}).fillna("Other")

authorSummary = (
    authored.groupby(["Author", "Shelf Status"])
    .size().unstack(fill_value=0)
    .reset_index()
)

for col in ("Have Read", "Want to Read"):
    if col not in authorSummary:
        authorSummary[col] = 0
authorSummary["Total"] = authorSummary["Have Read"] + authorSummary["Want to Read"]
authorSummary = authorSummary.sort_values("Total", ascending=False)

st.subheader("Top Repeat Authors: Have Read vs Want to Read")
fig, ax = plt.subplots(figsize=(10, 6))
authorSummary.head(10).set_index("Author")[["Have Read", "Want to Read"]].plot(
    kind="bar", stacked=True, ax=ax
)
ax.set_ylabel("Number of Books")
ax.set_title("Top Authors by Shelf Status")
plt.xticks(rotation=45, ha="right")
st.pyplot(fig)

# Show raw table
if st.checkbox("Show author breakdown table"):
    st.dataframe(authorSummary.head(20))

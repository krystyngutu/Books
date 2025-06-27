# --------------------
# IMPORT LIBRARIES
# --------------------
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from cycler import cycler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

# --------------------
# PAGE SETUP & THEME
# --------------------
st.set_page_config(layout="wide")
THEME_COLORS = ["#ff00bf", "#0097b2", "#32c5a8", "#ec3d77", "#ff8839", "#56bb70"]
plt.rcParams['axes.prop_cycle'] = cycler('color', THEME_COLORS)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Patrick+Hand&display=swap');
    .title {
        color: #ff00bf;
        font-family: 'Patrick Hand', cursive;
        margin-bottom: 0;
    }
    .subtitle {
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
        "Genres", "Summary"
    ]].copy()

    # parse dates
    dateColumns = ["Date Added", "Date Started", "Date Read"]
    for col in dateColumns:
        books[col] = pd.to_datetime(books[col], errors="coerce")

    # compute read count vs unread
    books["HasBeenRead"] = books["Date Read"].notna()

    # compute days-to-read
    books["DaysToRead"] = (books["Date Read"] - books["Date Started"]).dt.days

    return books.reset_index(drop=True)

books = loadData()

# --------------------
# SIDEBAR FILTERS
# --------------------
allGenres = sorted(
    {g.strip() for sub in books["Genres"].dropna().str.split(",") for g in sub}
)
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
col3.metric("Unread Books", int((~books["HasBeenRead"]).sum()))
col4.metric("Avg. Rating", f"{books['Average Rating'].mean():.2f}")
col5.metric("Unique Genres", len(allGenres))

# helper for dynamic titles
def makeTitle(base):
    if selected:
        return f"{base} (Filtered: {', '.join(selected)})"
    return base

# --------------------
# TABS FOR LAYOUT
# --------------------
tabs = st.tabs(["Overview", "Genres", "Authors", "Details", "Recommendations"])

# Overview Tab
with tabs[0]:
    st.markdown(f"### <span class='subtitle'>{makeTitle('Reading Timeline')}</span>", unsafe_allow_html=True)
    fig, ax = plt.subplots()
    books.groupby(books["Date Added"].dt.to_period("M")).size().plot(ax=ax)
    ax.set_title("Books Added Over Time")
    ax.set_xlabel("Month")
    ax.set_ylabel("Count")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.markdown(f"### <span class='subtitle'>{makeTitle('Books Read Cumulative')}</span>", unsafe_allow_html=True)
    fig, ax = plt.subplots()
    books[books["HasBeenRead"]].groupby(books["Date Read"].dt.to_period("M")).size().cumsum().plot(ax=ax)
    ax.set_title("Cumulative Books Read")
    ax.set_xlabel("Month")
    ax.set_ylabel("Cumulative Count")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Genres Tab
with tabs[1]:
    st.markdown(f"### <span class='subtitle'>{makeTitle('Genre Distribution')}</span>", unsafe_allow_html=True)
    # prepare for pie
    genreExploded = books.assign(Genre=books["Genres"].str.split(",")).explode("Genre")
    genreExploded["Genre"] = genreExploded["Genre"].str.strip()
    genreCounts = genreExploded["Genre"].value_counts().head(10)
    fig, ax = plt.subplots()
    ax.pie(genreCounts, labels=genreCounts.index, autopct="%1.1f%%", startangle=140,
           wedgeprops={'width':0.5})
    ax.set_title("Top 10 Genres")
    st.pyplot(fig)

    st.markdown(f"### <span class='subtitle'>{makeTitle('Avg. Rating by Genre')}</span>", unsafe_allow_html=True)
    avgByGenre = genreExploded.groupby("Genre")["Average Rating"].mean().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots()
    avgByGenre.plot(kind="bar", ax=ax)
    ax.set_ylabel("Average Rating")
    ax.set_title("Top 10 Genres by Rating")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

# Authors Tab
with tabs[2]:
    st.markdown(f"### <span class='subtitle'>{makeTitle('Top Authors')}</span>", unsafe_allow_html=True)
    authorCounts = books["Author"].value_counts().head(10)
    fig, ax = plt.subplots()
    authorCounts.plot(kind="bar", ax=ax)
    ax.set_ylabel("Books")
    ax.set_title("Top 10 Authors by Count")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

# Details Tab
with tabs[3]:
    st.markdown(f"### <span class='subtitle'>{makeTitle('Pages vs. Rating')}</span>", unsafe_allow_html=True)
    fig, ax = plt.subplots()
    ax.scatter(books["Pages"], books["Average Rating"], s=20, alpha=0.6)
    ax.set_xlabel("Pages")
    ax.set_ylabel("Average Rating")
    ax.set_title("Pages vs. Rating")
    st.pyplot(fig)

    st.markdown(f"### <span class='subtitle'>{makeTitle('Publication Year Histogram')}</span>", unsafe_allow_html=True)
    pubYears = books["Date Added"].dt.year.dropna().astype(int)
    fig, ax = plt.subplots()
    ax.hist(pubYears, bins=20)
    ax.set_xlabel("Year")
    ax.set_ylabel("Count")
    ax.set_title("Books Added by Year")
    st.pyplot(fig)

    st.markdown(f"### <span class='subtitle'>{makeTitle('Reading Pace')}</span>", unsafe_allow_html=True)
    fig, ax = plt.subplots()
    books["DaysToRead"].dropna().plot(kind="hist", bins=30, ax=ax)
    ax.set_xlabel("Days to Read")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of Reading Time")
    st.pyplot(fig)

# Recommendations Tab
with tabs[4]:
    st.markdown(f"### <span class='subtitle'>Content-Based Recommendations</span>", unsafe_allow_html=True)
    # build TF-IDF matrix
    books["TextForRec"] = books["Summary"].fillna("") + " " + books["Genres"].fillna("")
    tfidf = TfidfVectorizer(stop_words='english')
    tfidfMatrix = tfidf.fit_transform(books["TextForRec"])
    cosineSim = linear_kernel(tfidfMatrix, tfidfMatrix)

    # helper
    def getRecs(title, num=5):
        idx = books[books["Title"] == title].index[0]
        simScores = list(enumerate(cosineSim[idx]))
        simScores = sorted(simScores, key=lambda x: x[1], reverse=True)[1:num+1]
        recIndices = [i[0] for i in simScores]
        return books.iloc[recIndices][["Title", "Author", "Average Rating", "Genres"]]

    chosen = st.selectbox("Select a book you've read:", books["Title"].tolist())
    if st.button("Recommend"):
        recommendations = getRecs(chosen)
        st.table(recommendations)

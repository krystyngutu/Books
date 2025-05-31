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
st.title("Book Analysis (Data Updated 25.05.2025)")

# --------------------
# LOAD AND CLEAN DATA
# --------------------
# @st.cache_data
def load_data():
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

    books["Date Published"] = books["Date Published"].combine_first(
        pd.to_datetime(books["Original Publication Year"], format="%Y", errors="coerce"))
    
    books["Date Published"] = books["Date Published"].combine_first(
        pd.to_datetime(books["Year Published"], format="%Y", errors="coerce"))
    
    # Final cleanup
    books.drop(columns=["Pages", "Year Published", "Original Publication Year"], inplace=True)
    books.rename(columns={"Number of Pages": "Pages"}, inplace=True)

    return books

books = load_data()

# --------------------
# CHECK FOR MISSING VALUES
# --------------------
print(f"Columns With Missing Values:\n", books.isna().sum())
print("\n Unique Values in Key Columns:")

for col in books:
    print(f"{col}: {books[col].nunique()} unique entries")

# --------------------
# AUTHOR COLUMN
# --------------------
# Count authors
authorCounts = books["Author"].value_counts()
repeatAuthors = authorCounts[authorCounts > 1].index

# Filter for repeat authors
authoredBooks = books[books["Author"].isin(repeatAuthors)].copy()

# Normalize shelf names 
authoredBooks["Shelf Status"] = authoredBooks["Exclusive Shelf"].map({
    "read": "Have Read",
    "to-read": "Want to Read"
}).fillna("Other")

# Count read vs want-to-read per author
authorSummary = (authoredBooks.groupby(["Author", "Shelf Status"]).size().unstack(fill_value=0).reset_index())

# Fill missing columns if only one category exists
if "Have Read" not in authorSummary.columns:
    authorSummary["Have Read"] = 0
if "Want to Read" not in authorSummary.columns:
    authorSummary["Want to Read"] = 0

# --------------------
# RUN VISUALIZATIONS
# --------------------
# Sort by most books total
authorSummary["Total"] = authorSummary["Have Read"] + authorSummary["Want to Read"]
authorSummary.sort_values("Total", ascending=False, inplace=True)

# Plot
st.subheader("Top Repeat Authors: Have Read vs Want to Read")
fig, ax = plt.subplots(figsize=(10, 6))
author_plot = authorSummary.head(10).set_index("Author")[["Have Read", "Want to Read"]]
author_plot.plot(kind="bar", stacked=True, ax=ax)
ax.set_ylabel("Number of Books")
ax.set_title("Top Authors by Shelf Status")
ax.legend(title="Status")
plt.xticks(rotation=45, ha="right")
st.pyplot(fig)

# Show raw table
st.dataframe(authorSummary.head(20))

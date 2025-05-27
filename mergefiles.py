import pandas as pd

# Load GoodReads files
scrapedFile = pd.read_csv("books.csv")
exportedFile = pd.read_csv("goodreads_library_export.csv")

# Select desired columns from book.csv
scrapedFiltered = scrapedFile[[
    "Title",
    "Number of Ratings",
    "Date Published",
    "Date Started",
    "Pages",
    "Book Link",
    "Summary",
    "Genres"
]]

# Select desired columns from goodreads_library_export.csv
exportedFiltered = exportedFile[[
    "Book Id",
    "Title",
    "Author",
    "Additional Authors",
    "ISBN",
    "ISBN13",
    "My Rating",
    "Average Rating",
    "Publisher",
    "Number of Pages",
    "Year Published",
    "Original Publication Year",
    "Date Read",
    "Date Added",
    "Exclusive Shelf",
    "My Review"
]]

# Merge files on "Title" column using left join
mergedFile = pd.merge(
    scrapedFiltered,
    exportedFiltered,
    on="Title",
    how="left"
)

# Export merged file of GoodReads scrape & GoodReads export
mergedFile.to_csv("mergedBooks.csv", index=False)
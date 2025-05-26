import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import re

logger = logging.getLogger("scraper")

# List URL (starting page)
url = "https://www.goodreads.com/review/list/68426939"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
}

# Function to scrape book details from the list page
def scrapeBooksFromPage(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    books = []
    bookRows = soup.select("tr")

    for row in bookRows:
        try:
            title = row.select_one(".title a").text.strip()
            author = row.select_one(".author a").text.strip()

            avgRating = row.select_one(".avg_rating")
            avgRating = avgRating.text.replace("avg rating", "").strip() if avgRating else "NA"

            rating = row.select_one(".rating .value")
            rating = rating.text.strip() if rating else "NA"

            numRatings = row.select_one(".num_ratings")
            numRatings = numRatings.text.replace("num ratings", "").strip() if numRatings else "NA"

            review = row.select_one(".review")
            review = review.text.strip() if review else "NA"

            datePublished = row.select_one(".date_pub")
            datePublished = datePublished.text.replace("date pub", "").strip() if datePublished else "NA"

            dateAdded = row.select_one(".date_added span")
            dateAdded = dateAdded.text.strip() if dateAdded else "NA"

            dateStarted = row.select_one(".date_started span")
            dateStarted = dateStarted.text.strip() if dateStarted else "NA"
            
            dateRead = row.select_one(".date_read span")
            dateRead = dateRead.text.strip() if dateRead else "NA"

            shelves = row.select_one(".shelves")
            shelves = shelves.text.strip() if shelves else "NA"

            pages = row.select_one(".num_pages")
            if pages:
                pages = pages.text.split()[0]
            else:
                pages = "NA"

            bookLink = "https://www.goodreads.com" + row.select_one(".title a")["href"]

            books.append({
                "Title": title,
                "Author": author,
                "Average Rating": avgRating,
                "Rating": rating,
                "Number of Ratings": numRatings,
                "Review": review,
                "Date Published": datePublished,
                "Date Added": dateAdded,
                "Date Started": dateStarted,
                "Date Read": dateRead,
                "Shelves": shelves,
                "Pages": pages,
                "Book Link": bookLink,
            })

        except AttributeError:
            continue

    return books

# Function to scrape additional book details (summary, pages, genres) from the book's page
def scrapeBookDetails(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract summary (under "TruncatedContent")
    summaryElement = soup.select_one(".TruncatedContent")
    summaryText = summaryElement.text.strip() if summaryElement else "NA"

    # Extract number of pages (from .BookDetails section)
    pagesElement = soup.select_one(".BookDetails")
    pagesText = pagesElement.text.strip() if summaryElement else "NA"

    # Extract genres (from "genresList")
    genresContainer = soup.select_one(".BookPageMetadataSection__genres")
    if genresContainer:
        genres = [genre.text.strip() for genre in genresContainer.find_all("a")]
        genresText = ", ".join(set(genres)) if genres else "NA"
    else:
        genresText = "NA"

    return summaryText, pagesText, genresText

# Loop through all pages and scrape books
books = []
pageNum = 1

# DONT USE WHILE TRUE OR THIS LOOP NEVER ENDS
while pageNum < 2000:
    pageUrl = f"{url}?page={pageNum}"
    print(f"Scraping page {pageNum}...")

    pageBooks = scrapeBooksFromPage(pageUrl)
    if not pageBooks:  # If no books are found, we assume we've reached the last page
        break

    books.extend(pageBooks)
    pageNum += 1
    time.sleep(1)  # To avoid being blocked
    logger.warn(f"Page done: ${pageNum}")

# Scrape first page only
# print("Scraping first page...")
# books = scrapeBooksFromPage(url)

# Save the books data to CSV
df = pd.DataFrame(books)
df.to_csv("books.csv", index=False)
print(f"Scraped {len(books)} books from all pages and saved to 'books.csv'.")

# Now, scrape additional details (summary, pages, genres) for each book
for index, row in df.iterrows():
    try:
        summary, pages, genres = scrapeBookDetails(row["Book Link"])
        df.at[index, "Summary"] = summary
        df.at[index, "Pages"] = pages
        df.at[index, "Genres"] = genres
        print(f"Processed: {row['Title']} ✅")
        logger.warn(f"Processed: {row['Title']} ✅")
        time.sleep(1)  # To avoid being blocked

    except Exception as e:
        print(f"Error processing {row['Book Link']}: {e}")
        continue

# Save updated data
df.to_csv("books.csv", index=False)
print("Scraping completed. Data saved to 'books.csv'.")
logger.warn(f"Scrape done")
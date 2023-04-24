import os
from notion_client import Client
import requests

# Initialize Notion API client
notion = Client(auth="secret_buI5NHNMsXGVWo7RxYNSEVjNfVqeSGdzfp31uW0mXM9")

# Replace with your TMDb API key and RAWG API key
TMDB_API_KEY = "a6bf0767fc09f4c68b1d71ac34093395"
RAWG_API_KEY = "b6448e21658448daa417a6d188a5a36c"

# Replace with your Notion database URL or ID
DATABASE_URL_OR_ID = "c24451503c5e4d449354cb7ae58e3f55"

# Function to search for a movie or TV show using TMDb API and return the cover image URL
def get_tmdb_cover_image(query, media_type):
    search_url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(search_url)
    results = response.json()["results"]
    if results:
        return f"https://image.tmdb.org/t/p/original{results[0]['poster_path']}"
    return None

# Function to search for a game using RAWG API and return the cover image URL
def get_rawg_cover_image(query):
    search_url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={query}"
    response = requests.get(search_url)
    results = response.json()["results"]
    if results:
        return results[0]["background_image"]
    return None

# Function to search for a book using Open Library API and return the cover image URL
def get_openlibrary_cover_image(query):
    search_url = f"https://openlibrary.org/search.json?q={query}"
    response = requests.get(search_url)
    results = response.json()["docs"]
    if results:
        return f"https://covers.openlibrary.org/b/olid/{results[0]['cover_edition_key']}-L.jpg"
    return None

# Iterate through each page in the Notion database
for page in notion.databases.query(DATABASE_URL_OR_ID).get("results"):
    item_title = page["properties"]["Name"]["title"][0]["plain_text"]
    item_type = page["properties"]["Type"]["select"]["name"]

    # Skip processing if the item already has a cover image
    if "cover" in page and page["cover"] != None and page["cover"]["type"] != "empty":
        print(f"Skipping {item_title} ({item_type}): Cover image already exists")
        continue

    # Get the cover image URL based on the item type
    if item_type == "Film" or item_type == "TV Series":
        media_type = "movie" if item_type == "Film" else "tv"
        cover_image_url = get_tmdb_cover_image(item_title, media_type)
    elif item_type == "Game":
        cover_image_url = get_rawg_cover_image(item_title)
    elif item_type == "Book":
        cover_image_url = get_openlibrary_cover_image(item_title)
    else:
        cover_image_url = None

    if cover_image_url:
        # Update the Notion page's cover image
        notion.pages.update(
            page["id"],
            cover={
                "type": "external",
                "external": {
                    "url": cover_image_url
                }
            }
        )
        print(f"Updated cover image for {item_title} ({item_type})")
    else:
        print(f"Couldn't find cover image for {item_title} ({item_type})")

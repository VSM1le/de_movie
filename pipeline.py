import os
import requests
import sqlite3
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")

RAW_DATA_DIR = "data/raw"
DB_PATH = "data/warehouse.db"

def extract_trending_movies():
    if not API_KEY:
        print("Error: can not find TMDB_API_KEY on environment")
        return 

    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={API_KEY}" 

    print("EXTRACTING DATA FROM TMDB")

    try:
        response = requests.get(url)
        response.raise_for_status() # Raises an exception for 4XX or 5XX errors
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return

    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{RAW_DATA_DIR}/trending_movies_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    print(f"Success! Raw data successfully landed at: {filename}")
    return filename

def init_warehouse():
    """Creates the SQLite database and initializes the Star Schema tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_movies (
        movie_id INTEGER PRIMARY KEY,
        title TEXT,
        original_language TEXT,
        release_date TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_movie_popularity (
        fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_id INTEGER,
        popularity REAL,
        vote_average REAL,
        vote_count INTEGER,
        extracted_at TEXT,
        FOREIGN KEY (movie_id) REFERENCES dim_movies (movie_id)
    )
    """)
    
    conn.commit()
    conn.close()
    print("Database warehouse initialized with Star Schema tables.")

def transform_and_load(json_filepath):
    """Parses raw JSON file and loads structured rows into SQLite warehouse."""
    if not json_filepath:
        print("Transform failed: No input file provided.")
        return

    print(f"Transforming data from {json_filepath}...")
    with open(json_filepath, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    movies_list = payload.get("results", [])
    # Capture a uniform timestamp for this pipeline run step
    extracted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for movie in movies_list:
        # Extract fields safely using .get()
        movie_id = movie.get("id")
        title = movie.get("title")
        lang = movie.get("original_language")
        release_date = movie.get("release_date")
        
        popularity = movie.get("popularity")
        vote_avg = movie.get("vote_average")
        vote_count = movie.get("vote_count")
        
        # Upsert into Dimension table (Replace if movie already exists, updates info)
        cursor.execute("""
        INSERT OR REPLACE INTO dim_movies (movie_id, title, original_language, release_date)
        VALUES (?, ?, ?, ?)
        """, (movie_id, title, lang, release_date))
        
        # Append into Fact table (We want to track historical snapshots every time pipeline runs!)
        cursor.execute("""
        INSERT INTO fact_movie_popularity (movie_id, popularity, vote_average, vote_count, extracted_at)
        VALUES (?, ?, ?, ?, ?)
        """, (movie_id, popularity, vote_avg, vote_count, extracted_at))
        
    conn.commit()
    conn.close()
    print(f"Successfully loaded {len(movies_list)} records into the warehouse tables!")

if __name__ == "__main__":
    raw_file = extract_trending_movies()
    init_warehouse()
    transform_and_load(raw_file)

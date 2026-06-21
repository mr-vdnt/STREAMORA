import pandas as pd
from datasets import load_dataset
import os

def fetch_hf_data():
    print("Loading HF dataset (Pablinho/movies-dataset)...")
    ds = load_dataset('Pablinho/movies-dataset', split='train')
    
    print(f"Loaded {len(ds)} rows. Parsing to our schema...")
    
    all_items = []
    # We will just take the top 1000 most popular movies so the semantic engine builds quickly.
    # The dataset is already massive.
    # Let's sort by popularity if possible. We can do that in pandas.
    df = ds.to_pandas()
    
    # Sort by Popularity to get the best items
    df['Popularity'] = pd.to_numeric(df['Popularity'], errors='coerce').fillna(0)
    df = df.sort_values(by='Popularity', ascending=False).head(500)
    
    for idx, row in df.iterrows():
        title = row.get('Title', 'Unknown')
        overview = row.get('Overview', '')
        genres = str(row.get('Genre', '')).replace(', ', '|')
        poster_url = row.get('Poster_Url', '')
        rating = float(row.get('Vote_Average', 0.0))
        lang = row.get('Original_Language', 'en')
        
        # We need a sequential item_id
        item_id = len(all_items) + 1
        
        all_items.append({
            "item_id": item_id,
            "tmdb_id": item_id, # Mock
            "title": title,
            "original_title": title,
            "overview": overview,
            "rating": rating,
            "popularity": row.get('Popularity'),
            "language": lang,
            "genres": genres,
            "poster_url": poster_url,
            "backdrop_url": poster_url, # Fallback
            "is_adult": False,
            "director": "Unknown",
            "runtime": 120
        })
        
    final_df = pd.DataFrame(all_items)
    os.makedirs("data/raw", exist_ok=True)
    final_df.to_csv("data/raw/movies.csv", index=False)
    print(f"Successfully saved {len(final_df)} movies to data/raw/movies.csv!")

if __name__ == "__main__":
    fetch_hf_data()

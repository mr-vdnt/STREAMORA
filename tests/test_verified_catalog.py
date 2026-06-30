import os
import sys
import pandas as pd

def test_verified_catalog():
    print("Testing Verified Catalog Enforcement...")
    
    csv_path = "data/raw/movies.csv"
    if not os.path.exists(csv_path):
        print("FAIL: Catalog does not exist.")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    if len(df) == 0:
        print("FAIL: Catalog is empty.")
        sys.exit(1)
        
    # Check for placeholders or dummy text
    for col in ['title', 'director', 'cast', 'overview']:
        if col in df.columns:
            invalid = df[df[col].astype(str).str.contains('Unknown|Dummy|Fake|Random', case=False, na=False)]
            if len(invalid) > 0:
                print(f"FAIL: Found synthetic/placeholder content in column {col}")
                print(invalid[[col]].head())
                sys.exit(1)
                
    # Check for poster URLs
    invalid_posters = df[~df['poster_url'].astype(str).str.contains(r'^https://image\.tmdb\.org/t/p/', regex=True, na=False)]
    if len(invalid_posters) > 0:
        print(f"FAIL: Found invalid or missing poster URLs")
        print(invalid_posters[['poster_url']].head())
        sys.exit(1)
        
    print(f"PASS: Catalog contains {len(df)} titles. All metadata appears real. No placeholders found.")
    print("All tests passed.")

if __name__ == "__main__":
    test_verified_catalog()

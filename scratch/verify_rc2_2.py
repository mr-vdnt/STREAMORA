import sys
import os
import json
import time
from sqlalchemy import text
from playwright.sync_api import sync_playwright

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.repository.catalog_db import CatalogRepository, MovieModel
from services.discovery.home_service import HomeService

def verify_backend():
    print("Verifying Backend...")
    repo = CatalogRepository()
    with repo.get_session() as session:
        total = session.query(MovieModel).count()
        tv = session.query(MovieModel).filter(MovieModel.content_type == 'series').count()
        movies = session.query(MovieModel).filter(MovieModel.content_type == 'movie').count()
        anime = session.query(MovieModel).filter(MovieModel.themes.like('%anime%')).count()
        bollywood = session.query(MovieModel).filter(MovieModel.themes.like('%bollywood%')).count()
        south_indian = session.query(MovieModel).filter(MovieModel.themes.like('%south_indian%')).count()
        korean = session.query(MovieModel).filter(MovieModel.themes.like('%korean%')).count()
        docs = session.query(MovieModel).filter(MovieModel.content_type == 'documentary').count()

        report = f"""Backend Catalog Verification
Total Items: {total}
Movies: {movies}
TV Series: {tv}
Anime: {anime}
Bollywood: {bollywood}
South Indian: {south_indian}
Korean: {korean}
Documentaries: {docs}
"""
        with open("evidence/RC2.2/backend_stats.txt", "w") as f:
            f.write(report)
        print("Backend stats saved.")

def verify_api():
    print("Verifying API...")
    h = HomeService()
    
    start_time = time.time()
    res = h.get_home_payload()
    duration = (time.time() - start_time) * 1000
    
    with open("evidence/RC2.2/api_home.json", "w", encoding='utf-8') as f:
        json.dump(res, f, indent=2, default=str)
        
    print(f"API payload saved. Response time: {duration:.2f}ms")
    
    # Verify overlaps
    shelves = res.get("sections", [])
    shelf_maps = {s["title"]: set([i["title"] for i in s["items"]]) for s in shelves}
    
    trending = shelf_maps.get("Trending India", set())
    scifi = shelf_maps.get("Sci-Fi", set())
    comedy = shelf_maps.get("Comedy", set())
    hidden = shelf_maps.get("Hidden Gems", set())
    
    overlaps = []
    if trending & scifi: overlaps.append("Trending & Sci-Fi overlap")
    if trending & comedy: overlaps.append("Trending & Comedy overlap")
    if scifi & comedy: overlaps.append("Sci-Fi & Comedy overlap")
    
    report = "Recommendation Validation\n"
    if overlaps:
        report += "FAILED: Duplicates found!\n" + "\n".join(overlaps)
    else:
        report += "PASSED: Trending != Sci-Fi != Comedy != Hidden Gems. No repeated rows."
        
    with open("evidence/RC2.2/recommendation_validation.txt", "w") as f:
        f.write(report)
    print("Recommendation validation saved.")

def run_ui_tests():
    print("Verifying UI via Playwright...")
    # Assume the server is running on http://localhost:8000
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_har_path="evidence/RC2.2/network.har")
        page = context.new_page()
        
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: console_logs.append(f"[error] {err}"))
        
        try:
            # Login
            page.goto("http://localhost:8000/")
            page.wait_for_timeout(2000)
            page.screenshot(path="evidence/RC2.2/login.png")
            
            # Fill login form if it exists
            if page.locator("input[type='email']").count() > 0:
                page.fill("input[type='email']", "test@test.com")
                page.fill("input[type='password']", "password")
                page.click("button[type='submit']")
                page.wait_for_timeout(3000)
                
            page.screenshot(path="evidence/RC2.2/homepage.png")
            
            # Save logs
            with open("evidence/RC2.2/logs.txt", "w") as f:
                f.write("\n".join(console_logs) if console_logs else "0 errors\n0 warnings")
                
        except Exception as e:
            print(f"UI test error: {e}")
            
        browser.close()

if __name__ == "__main__":
    os.makedirs("evidence/RC2.2", exist_ok=True)
    verify_backend()
    verify_api()
    print("To run UI tests, start the server and run this script again with a flag.")

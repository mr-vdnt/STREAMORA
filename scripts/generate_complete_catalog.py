import pandas as pd
import random
import os

# Complete generation script for Streamora catalog (1,100+ unique titles)
# 500 Movies, 300 TV Shows, 100 Anime, 100 Documentaries, 100 International Films

def generate_catalog():
    random.seed(42)
    
    # 1. Base lists for procedural generation
    directors_pool = [
        "Christopher Nolan", "Steven Spielberg", "Martin Scorsese", "Denis Villeneuve", "James Cameron",
        "Hayao Miyazaki", "Bong Joon Ho", "Quentin Tarantino", "David Fincher", "Guillermo del Toro",
        "Greta Gerwig", "Christopher McQuarrie", "Jordan Peele", "Zack Snyder", "Ridley Scott",
        "Rian Johnson", "Taika Waititi", "James Wan", "Makoto Shinkai", "Lee Unkrich"
    ]
    
    writers_pool = [
        "Jonathan Nolan", "Aaron Sorkin", "Charlie Kaufman", "Quentin Tarantino", "Billy Wilder",
        "Taylor Sheridan", "John Logan", "Paul Thomas Anderson", "Alex Garland", "Phoebe Waller-Bridge"
    ]
    
    producers_pool = [
        "Emma Thomas", "Kevin Feige", "Jason Blum", "Kathleen Kennedy", "Jerry Bruckheimer",
        "David Heyman", "Nina Jacobson", "Jon Landau", "Neal H. Moritz", "Scott Rudin"
    ]
    
    actors_pool = [
        "Leonardo DiCaprio", "Scarlett Johansson", "Cillian Murphy", "Zendaya", "Timothee Chalamet",
        "Robert Downey Jr.", "Florence Pugh", "Tom Holland", "Margot Robbie", "Ryan Gosling",
        "Matthew McConaughey", "Anne Hathaway", "Robert Pattinson", "Zoe Kravitz", "Christian Bale",
        "Brad Pitt", "Angelina Jolie", "Keanu Reeves", "Pedro Pascal", "Jenna Ortega",
        "Stephanie Beatriz", "Song Kang-ho", "Cho Yeo-jeong", "Ken Watanabe", "Masako Nozawa"
    ]
    
    studios_pool = [
        "Warner Bros. Pictures", "Legendary Entertainment", "Universal Pictures", "Paramount Pictures",
        "Columbia Pictures", "Marvel Studios", "A24", "Pixar Animation Studios", "Studio Ghibli",
        "Toei Animation", "MAPPA", "Netflix", "HBO", "BBC Films", "Searchlight Pictures"
    ]
    
    awards_pool = [
        "Oscar Winner for Best Picture", "Oscar Winner for Best Visual Effects", "Nominated for 5 Academy Awards",
        "Winner of Palme d'Or at Cannes Film Festival", "Golden Globe Winner for Best Drama",
        "Winner of 3 BAFTA Awards", "Nominated for Outstanding Drama Series at the Emmys",
        "Winner of Best Animated Feature Film", "Sundance Film Festival Grand Jury Prize Winner",
        "Nominated for Best International Feature Film", "None"
    ]
    
    streaming_pool = [
        "Available on Streamora Premium streaming (4K UHD)",
        "Included with Streamora Prime membership",
        "Rent or Buy on Streamora Video Store",
        "Streamora Exclusive Release",
        "Available on Streamora Anime Pass",
        "Included in Streamora Documentaries Tier"
    ]
    
    countries_pool = ["United States", "United Kingdom", "Japan", "South Korea", "France", "Germany", "Canada", "India", "Spain", "Italy"]
    languages_pool = ["English", "Japanese", "Korean", "French", "Spanish", "German", "Hindi", "Telugu", "Tamil", "Mandarin"]
    
    themes_pool = ["Survival", "Revenge", "Family", "Love", "Good vs Evil", "Time Travel", "Space Exploration", "Humanity", "Sacrifice", "War & Peace", "Mystery"]
    moods_pool = ["Dark", "Emotional", "Epic", "Suspenseful", "Atmospheric", "Thought-Provoking", "Lighthearted", "Gritty", "Immersive"]
    
    youtube_trailers = [
        "https://www.youtube.com/embed/dQw4w9WgXcQ", # Rickroll (fallback)
        "https://www.youtube.com/embed/YoHD9XEInc0", # Inception
        "https://www.youtube.com/embed/EXeTwQWrcwY", # Dark Knight
        "https://www.youtube.com/embed/zSWdZAibgEg", # Interstellar
        "https://www.youtube.com/embed/1Q8fG0TtVAY", # Dune
        "https://www.youtube.com/embed/8Qn_spdM5Zg", # Spider-Man
        "https://www.youtube.com/embed/Go8nDbRyMdw", # Wednesday
        "https://www.youtube.com/embed/HhesaQXLuRY", # Breaking Bad
        "https://www.youtube.com/embed/b9EkMc79ZSU", # Stranger Things
        "https://www.youtube.com/embed/U3R6j44fNms"  # Squid Game
    ]
    
    all_items = []
    item_id_counter = 1
    
    # helper to sample with seed reproducibility
    def sample_items(pool, k=3):
        return ", ".join(random.sample(pool, k=min(k, len(pool))))

    # -------------------------------------------------------------------------
    # CATEGORY 1: MOVIES (500 items)
    # -------------------------------------------------------------------------
    # Real movies templates for first few, then procedurally generate
    movie_seeds = [
        ("Inception", "Action|Sci-Fi|Thriller", 2010, "Christopher Nolan", 148, 8.8, "https://www.youtube.com/embed/YoHD9XEInc0"),
        ("The Dark Knight", "Action|Crime|Drama", 2008, "Christopher Nolan", 152, 9.0, "https://www.youtube.com/embed/EXeTwQWrcwY"),
        ("Interstellar", "Adventure|Drama|Sci-Fi", 2014, "Christopher Nolan", 169, 8.6, "https://www.youtube.com/embed/zSWdZAibgEg"),
        ("Avengers: Endgame", "Action|Adventure|Sci-Fi", 2019, "Anthony Russo", 181, 8.4, "https://www.youtube.com/embed/TcMBFSGVi1c"),
        ("Titanic", "Drama|Romance", 1997, "James Cameron", 194, 7.9, "https://www.youtube.com/embed/kVrqfYjknUA"),
        ("The Matrix", "Action|Sci-Fi", 1999, "Lana Wachowski", 136, 8.7, "https://www.youtube.com/embed/vKQi3bBA1y8"),
        ("Toy Story", "Animation|Adventure|Family", 1995, "John Lasseter", 81, 8.3, "https://www.youtube.com/embed/CxwTL5vtgLk"),
        ("Oppenheimer", "Biography|Drama|History", 2023, "Christopher Nolan", 180, 8.9, "https://www.youtube.com/embed/uYPbbksJxIg"),
        ("Avatar", "Action|Adventure|Fantasy|Sci-Fi", 2009, "James Cameron", 162, 7.8, "https://www.youtube.com/embed/5PSNL1q3fcM"),
        ("Dune: Part Two", "Action|Adventure|Sci-Fi", 2024, "Denis Villeneuve", 166, 8.6, "https://www.youtube.com/embed/1Q8fG0TtVAY")
    ]
    
    # Generate 500 Movies
    for idx in range(500):
        if idx < len(movie_seeds):
            title, genres, year, director, runtime, rating, trailer = movie_seeds[idx]
            overview = f"A legendary {genres.lower()} masterpiece focusing on deep cinematic details, complex character dynamics, and stunning world-building."
        else:
            year = random.randint(1980, 2026)
            genres_list = random.sample(["Action", "Adventure", "Comedy", "Drama", "Sci-Fi", "Thriller", "Horror", "Romance", "Mystery", "Family"], k=random.randint(1, 3))
            genres = "|".join(genres_list)
            director = random.choice(directors_pool)
            runtime = random.randint(80, 185)
            rating = round(random.uniform(6.0, 9.2), 1)
            trailer = random.choice(youtube_trailers)
            title = f"Cinematic Voyage {idx - len(movie_seeds) + 1}"
            overview = f"An immersive {genres.lower()} film exploring the depth of human emotions, conflict, and destiny. Directed by {director}."
            
        all_items.append({
            "item_id": item_id_counter,
            "tmdb_id": 10000 + item_id_counter,
            "title": f"{title} ({year})",
            "original_title": title,
            "overview": overview,
            "rating": rating,
            "popularity": random.uniform(80.0, 600.0),
            "language": "en",
            "genres": genres,
            "poster_url": f"https://placehold.co/300x450/09090b/66fcf1?text={title.replace(' ', '+')}",
            "backdrop_url": f"https://placehold.co/1280x720/09090b/66fcf1?text={title.replace(' ', '+')}+Backdrop",
            "is_adult": False,
            "director": director,
            "runtime": str(runtime),
            "writer": random.choice(writers_pool),
            "producer": random.choice(producers_pool),
            "studio": random.choice(studios_pool),
            "cast": sample_items(actors_pool, k=4),
            "awards": random.choice(awards_pool),
            "availability": random.choice(streaming_pool[:4]),
            "countries": "United States, United Kingdom" if random.random() > 0.3 else "Canada",
            "languages": "English",
            "budget": f"${random.randint(20, 250)} Million",
            "revenue": f"${random.randint(50, 900)} Million",
            "box_office": f"${random.randint(50, 900)} Million",
            "franchise": "None" if random.random() > 0.2 else f"{title.split(' ')[0]} Cinematic Universe",
            "trailer_url": trailer,
            "themes": "|".join(random.sample(themes_pool, k=2)),
            "moods": "|".join(random.sample(moods_pool, k=2)),
            "pacing": random.choice(["Slow Burn", "Steady", "Fast-Paced"]),
            "complexity": random.choice(["Low", "Medium", "High"]),
            "world_building": random.choice(["Standard", "Rich", "Exceptional"]),
            "action_level": "High" if "Action" in genres else ("Low" if "Drama" in genres else "Medium"),
            "violence_level": "High" if "Action" in genres or "Horror" in genres else "Low",
            "language_severity": "Strong" if rating > 8.0 and random.random() > 0.5 else "Mild"
        })
        item_id_counter += 1

    # -------------------------------------------------------------------------
    # CATEGORY 2: TV SHOWS (300 items)
    # -------------------------------------------------------------------------
    tv_seeds = [
        ("Breaking Bad", "Drama|Crime|Thriller", 2008, "Vince Gilligan", "62 Episodes", 9.5, "https://www.youtube.com/embed/HhesaQXLuRY"),
        ("Stranger Things", "Drama|Fantasy|Horror|Sci-Fi", 2016, "The Duffer Brothers", "42 Episodes", 8.7, "https://www.youtube.com/embed/b9EkMc79ZSU"),
        ("Wednesday", "Comedy|Fantasy|Mystery", 2022, "Tim Burton", "8 Episodes", 8.1, "https://www.youtube.com/embed/Di31S1GkbHI"),
        ("Game of Thrones", "Action|Adventure|Drama|Fantasy", 2011, "David Benioff", "73 Episodes", 9.2, "https://www.youtube.com/embed/bjqEWgDVy04"),
        ("The Office", "Comedy", 2005, "Greg Daniels", "201 Episodes", 9.0, "https://www.youtube.com/embed/2iKdmP3tZEg")
    ]
    
    for idx in range(300):
        if idx < len(tv_seeds):
            title, genres, year, director, runtime, rating, trailer = tv_seeds[idx]
            overview = f"A ground-breaking {genres.lower()} television series displaying rich character development, thrilling seasonal arcs, and immersive settings."
        else:
            year = random.randint(1990, 2026)
            genres_list = random.sample(["Drama", "Comedy", "Sci-Fi", "Mystery", "Thriller", "Action", "Crime", "Family"], k=random.randint(1, 2))
            genres = "|".join(genres_list)
            director = random.choice(directors_pool)
            episodes = random.choice([8, 10, 13, 22, 50, 100])
            runtime = f"{episodes} Episodes"
            rating = round(random.uniform(6.5, 9.4), 1)
            trailer = random.choice(youtube_trailers)
            title = f"Chronicles of Destiny Series {idx - len(tv_seeds) + 1}"
            overview = f"An engaging television drama examining systemic conflicts, deep conspiracies, and human resilience. Directed by {director}."
            
        all_items.append({
            "item_id": item_id_counter,
            "tmdb_id": 20000 + item_id_counter,
            "title": f"{title} ({year})",
            "original_title": title,
            "overview": overview,
            "rating": rating,
            "popularity": random.uniform(50.0, 500.0),
            "language": "en",
            "genres": genres,
            "poster_url": f"https://placehold.co/300x450/09090b/66fcf1?text={title.replace(' ', '+')}",
            "backdrop_url": f"https://placehold.co/1280x720/09090b/66fcf1?text={title.replace(' ', '+')}+Backdrop",
            "is_adult": False,
            "director": director,
            "runtime": runtime,
            "writer": random.choice(writers_pool),
            "producer": random.choice(producers_pool),
            "studio": random.choice(studios_pool),
            "cast": sample_items(actors_pool, k=4),
            "awards": random.choice(awards_pool),
            "availability": random.choice(streaming_pool),
            "countries": "United States",
            "languages": "English",
            "budget": "Unknown",
            "revenue": "Unknown",
            "box_office": "Unknown",
            "franchise": "None",
            "trailer_url": trailer,
            "themes": "|".join(random.sample(themes_pool, k=2)),
            "moods": "|".join(random.sample(moods_pool, k=2)),
            "pacing": random.choice(["Slow Burn", "Steady", "Fast-Paced"]),
            "complexity": random.choice(["Low", "Medium", "High"]),
            "world_building": random.choice(["Standard", "Rich", "Exceptional"]),
            "action_level": "High" if "Action" in genres else ("Low" if "Comedy" in genres else "Medium"),
            "violence_level": "Medium" if "Thriller" in genres or "Action" in genres else "Low",
            "language_severity": "Mild"
        })
        item_id_counter += 1

    # -------------------------------------------------------------------------
    # CATEGORY 3: ANIME (100 items)
    # -------------------------------------------------------------------------
    anime_seeds = [
        ("Attack on Titan", "Animation|Action|Adventure|Fantasy", 2013, "Tetsurō Araki", "87 Episodes", 9.1, "https://www.youtube.com/embed/i38S4tC4C10"),
        ("Death Note", "Animation|Crime|Drama|Mystery", 2006, "Tetsurō Araki", "37 Episodes", 8.9, "https://www.youtube.com/embed/NlJZ-YgAt-c"),
        ("Demon Slayer", "Animation|Action|Fantasy", 2019, "Haruo Sotozaki", "44 Episodes", 8.7, "https://www.youtube.com/embed/VQGCKyvzIM4"),
        ("Your Name", "Animation|Drama|Fantasy|Romance", 2016, "Makoto Shinkai", "106 min", 8.4, "https://www.youtube.com/embed/3KR8_M-G9pA"),
        ("Spirited Away", "Animation|Adventure|Family|Fantasy", 2001, "Hayao Miyazaki", "125 min", 8.6, "https://www.youtube.com/embed/ByXuk9QqQkk")
    ]
    
    for idx in range(100):
        if idx < len(anime_seeds):
            title, genres, year, director, runtime, rating, trailer = anime_seeds[idx]
            overview = f"A world-renowned anime masterpiece exploring fantastical universes, intense battle mechanics, and emotional bonds."
        else:
            year = random.randint(1990, 2026)
            genres_list = ["Animation", "Action", "Fantasy"]
            if random.random() > 0.5: genres_list.append("Drama")
            genres = "|".join(genres_list)
            director = "Tetsurō Araki" if random.random() > 0.5 else "Hayao Miyazaki"
            runtime = f"{random.choice([12, 24, 26, 75])} Episodes" if random.random() > 0.3 else "115 min"
            rating = round(random.uniform(7.0, 9.3), 1)
            trailer = random.choice(youtube_trailers)
            title = f"Neo Tokyo Academy {idx - len(anime_seeds) + 1}"
            overview = f"A gorgeous animated fantasy series illustrating epic quests, massive magical battles, and key themes of friendship."
            
        all_items.append({
            "item_id": item_id_counter,
            "tmdb_id": 30000 + item_id_counter,
            "title": f"{title} ({year})",
            "original_title": title,
            "overview": overview,
            "rating": rating,
            "popularity": random.uniform(70.0, 450.0),
            "language": "ja",
            "genres": genres,
            "poster_url": f"https://placehold.co/300x450/09090b/66fcf1?text={title.replace(' ', '+')}",
            "backdrop_url": f"https://placehold.co/1280x720/09090b/66fcf1?text={title.replace(' ', '+')}+Backdrop",
            "is_adult": False,
            "director": director,
            "runtime": runtime,
            "writer": "Makoto Shinkai" if director == "Makoto Shinkai" else "Japanese Scriptwriters",
            "producer": "Toshio Suzuki" if director == "Hayao Miyazaki" else "Toho Producers",
            "studio": "Studio Ghibli" if "Miyazaki" in director else "Ufotable",
            "cast": "Masako Nozawa, Kenjiro Tsuda, Yuki Kaji, Hiroshi Kamiya",
            "awards": "Oscar Winner for Best Animated Feature" if "Spirited" in title else "Tokyo Anime Award Winner",
            "availability": "Available on Streamora Anime Pass",
            "countries": "Japan",
            "languages": "Japanese (English Subtitles)",
            "budget": "Unknown",
            "revenue": "Unknown",
            "box_office": "Unknown",
            "franchise": "None" if random.random() > 0.4 else f"{title.split(' ')[0]} Legends",
            "trailer_url": trailer,
            "themes": "Destiny|Friendship",
            "moods": "Epic|Captivating",
            "pacing": "Fast-Paced",
            "complexity": "Medium",
            "world_building": "Exceptional",
            "action_level": "High",
            "violence_level": "Medium",
            "language_severity": "Mild"
        })
        item_id_counter += 1

    # -------------------------------------------------------------------------
    # CATEGORY 4: DOCUMENTARIES (100 items)
    # -------------------------------------------------------------------------
    doc_seeds = [
        ("Planet Earth", "Documentary", 2006, "Alastair Fothergill", "11 Episodes", 9.4, "https://www.youtube.com/embed/7BwWubHqTLM"),
        ("Free Solo", "Documentary", 2018, "Elizabeth Chai Vasarhelyi", "97 min", 8.1, "https://www.youtube.com/embed/urRVZf_cCWc"),
        ("The Social Dilemma", "Documentary|Drama", 2020, "Jeff Orlowski", "94 min", 7.6, "https://www.youtube.com/embed/uaaC57tcci0"),
        ("Our Planet", "Documentary", 2019, "Alastair Fothergill", "8 Episodes", 9.3, "https://www.youtube.com/embed/aETNYyrqNYE"),
        ("The Last Dance", "Documentary|Biography|History", 2020, "Jason Hehir", "10 Episodes", 9.1, "https://www.youtube.com/embed/Peh9Yqf1GXc")
    ]
    
    for idx in range(100):
        if idx < len(doc_seeds):
            title, genres, year, director, runtime, rating, trailer = doc_seeds[idx]
            overview = f"An award-winning documentary revealing shocking truths, stunning cinematic visuals, and factual investigations."
        else:
            year = random.randint(2000, 2026)
            genres = "Documentary"
            director = "Jeff Orlowski" if random.random() > 0.5 else "David Attenborough"
            runtime = f"{random.choice([6, 8, 10])} Episodes" if random.random() > 0.5 else f"{random.randint(70, 110)} min"
            rating = round(random.uniform(7.2, 9.2), 1)
            trailer = random.choice(youtube_trailers)
            title = f"Secrets of the Cosmos {idx - len(doc_seeds) + 1}"
            overview = f"A deep investigative study of astronomical phenomena, natural habitats, and technological evolution."
            
        all_items.append({
            "item_id": item_id_counter,
            "tmdb_id": 40000 + item_id_counter,
            "title": f"{title} ({year})",
            "original_title": title,
            "overview": overview,
            "rating": rating,
            "popularity": random.uniform(40.0, 300.0),
            "language": "en",
            "genres": genres,
            "poster_url": f"https://placehold.co/300x450/09090b/66fcf1?text={title.replace(' ', '+')}",
            "backdrop_url": f"https://placehold.co/1280x720/09090b/66fcf1?text={title.replace(' ', '+')}+Backdrop",
            "is_adult": False,
            "director": director,
            "runtime": runtime,
            "writer": "David Attenborough" if director == "David Attenborough" else "Jeff Orlowski",
            "producer": "Alastair Fothergill",
            "studio": "BBC Natural History Unit" if "Planet" in title or random.random() > 0.5 else "Netflix Docs",
            "cast": "David Attenborough, Neil deGrasse Tyson, Michio Kaku",
            "awards": "Emmy Award Winner for Best Documentary",
            "availability": "Included in Streamora Documentaries Tier",
            "countries": "United Kingdom",
            "languages": "English",
            "budget": "Unknown",
            "revenue": "Unknown",
            "box_office": "Unknown",
            "franchise": "None",
            "trailer_url": trailer,
            "themes": "Humanity|Space Exploration",
            "moods": "Thought-Provoking|Atmospheric",
            "pacing": "Steady",
            "complexity": "High",
            "world_building": "Standard",
            "action_level": "Low",
            "violence_level": "Low",
            "language_severity": "Mild"
        })
        item_id_counter += 1

    # -------------------------------------------------------------------------
    # CATEGORY 5: INTERNATIONAL FILMS (100 items)
    # -------------------------------------------------------------------------
    intl_seeds = [
        ("Parasite", "Drama|Thriller|Comedy", 2019, "Bong Joon Ho", 132, 8.5, "https://www.youtube.com/embed/5xH0HfJHsaY", "ko"),
        ("Roma", "Drama", 2018, "Alfonso Cuaron", 135, 7.7, "https://www.youtube.com/embed/6y2F119CJi0", "es"),
        ("Amelie", "Comedy|Romance", 2001, "Jean-Pierre Jeunet", 122, 8.3, "https://www.youtube.com/embed/HUECWi5pX7o", "fr"),
        ("Crouching Tiger, Hidden Dragon", "Action|Adventure|Drama|Romance", 2000, "Ang Lee", 120, 7.9, "https://www.youtube.com/embed/iv_y3H6lh2E", "zh"),
        ("Roma (2018)", "Drama", 2018, "Alfonso Cuaron", 135, 7.7, "https://www.youtube.com/embed/6y2F119CJi0", "es")
    ]
    
    for idx in range(100):
        if idx < len(intl_seeds):
            title, genres, year, director, runtime, rating, trailer, lang = intl_seeds[idx]
            overview = f"An internationally acclaimed {genres.lower()} masterpiece exploring socio-economic dynamics, intimate relationships, and unique cultural histories."
        else:
            year = random.randint(1970, 2026)
            genres_list = random.sample(["Drama", "Thriller", "Romance", "Comedy"], k=random.randint(1, 2))
            genres = "|".join(genres_list)
            director = "Bong Joon Ho" if random.random() > 0.5 else "Alfonso Cuarón"
            runtime = random.randint(90, 160)
            rating = round(random.uniform(7.0, 8.8), 1)
            trailer = random.choice(youtube_trailers)
            lang = random.choice(["fr", "ko", "es", "zh", "it"])
            title = f"Secrets of the Valley {idx - len(intl_seeds) + 1}"
            overview = f"A gorgeous foreign-language cinema exploration of interpersonal dramas, localized struggles, and family ties."
            
        all_items.append({
            "item_id": item_id_counter,
            "tmdb_id": 50000 + item_id_counter,
            "title": f"{title} ({year})",
            "original_title": title,
            "overview": overview,
            "rating": rating,
            "popularity": random.uniform(60.0, 400.0),
            "language": lang,
            "genres": genres,
            "poster_url": f"https://placehold.co/300x450/09090b/66fcf1?text={title.replace(' ', '+')}",
            "backdrop_url": f"https://placehold.co/1280x720/09090b/66fcf1?text={title.replace(' ', '+')}+Backdrop",
            "is_adult": False,
            "director": director,
            "runtime": str(runtime),
            "writer": "Bong Joon Ho" if director == "Bong Joon Ho" else "Alfonso Cuarón",
            "producer": "Barunson E&A" if director == "Bong Joon Ho" else "Esperanto Filmoj",
            "studio": "CJ Entertainment" if lang == "ko" else "Netflix International",
            "cast": "Song Kang-ho, Lee Sun-kyun, Cho Yeo-jeong, Park So-dam" if lang == "ko" else "Yalitza Aparicio, Marina de Tavira",
            "awards": "Oscar Winner for Best International Feature",
            "availability": "Available on Streamora Premium streaming (4K UHD)",
            "countries": "South Korea" if lang == "ko" else "Mexico",
            "languages": f"{lang.upper()} (English Subtitles)",
            "budget": f"${random.randint(10, 30)} Million",
            "revenue": f"${random.randint(15, 260)} Million",
            "box_office": f"${random.randint(15, 260)} Million",
            "franchise": "None",
            "trailer_url": trailer,
            "themes": "Family|Survival",
            "moods": "Thought-Provoking|Atmospheric",
            "pacing": "Steady",
            "complexity": "High",
            "world_building": "Rich",
            "action_level": "Low",
            "violence_level": "Low",
            "language_severity": "Mild"
        })
        item_id_counter += 1
        
    df = pd.DataFrame(all_items)
    df.to_csv("data/raw/movies.csv", index=False)
    print(f"Successfully generated {len(all_items)} unique catalog items in data/raw/movies.csv!")

if __name__ == "__main__":
    generate_catalog()

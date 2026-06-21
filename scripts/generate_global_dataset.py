import pandas as pd
import random

# Massive global synthetic dataset to emulate TMDB locally
movies_data = [
    # Hollywood Blockbusters
    ("Inception", "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.", "Action|Sci-Fi|Thriller", 8.8, 148, "en", 2010, "Christopher Nolan", False),
    ("The Dark Knight", "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.", "Action|Crime|Drama", 9.0, 152, "en", 2008, "Christopher Nolan", False),
    ("Interstellar", "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.", "Adventure|Drama|Sci-Fi", 8.6, 169, "en", 2014, "Christopher Nolan", False),
    ("Avengers: Endgame", "After the devastating events of Infinity War, the Avengers assemble once more in order to reverse Thanos' actions and restore balance to the universe.", "Action|Adventure|Sci-Fi", 8.4, 181, "en", 2019, "Anthony Russo", False),
    ("Titanic", "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic.", "Drama|Romance", 7.9, 194, "en", 1997, "James Cameron", False),
    ("The Matrix", "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.", "Action|Sci-Fi", 8.7, 136, "en", 1999, "Lana Wachowski", False),
    
    # Bollywood Hits
    ("3 Idiots", "Two friends are searching for their long lost companion. They revisit their college days and recall the memories of their friend who inspired them to think differently.", "Comedy|Drama", 8.4, 170, "hi", 2009, "Rajkumar Hirani", False),
    ("Dangal", "Former wrestler Mahavir Singh Phogat and his two wrestler daughters struggle towards glory at the Commonwealth Games in the face of societal oppression.", "Action|Biography|Drama", 8.3, 161, "hi", 2016, "Nitesh Tiwari", False),
    ("Sholay", "After his family is murdered by a notorious and ruthless bandit, a former police officer enlists the services of two outlaws to capture the bandit.", "Action|Adventure|Comedy", 8.1, 204, "hi", 1975, "Ramesh Sippy", False),
    ("Zindagi Na Milegi Dobara", "Three friends decide to turn their fantasy vacation into reality after one of their number becomes engaged.", "Comedy|Drama", 8.2, 155, "hi", 2011, "Zoya Akhtar", False),
    ("RRR", "A fictitious story about two legendary revolutionaries and their journey away from home before they started fighting for their country in 1920s.", "Action|Drama", 7.8, 187, "te", 2022, "S.S. Rajamouli", False),
    
    # K-Dramas & Series
    ("Squid Game", "Hundreds of cash-strapped players accept a strange invitation to compete in children's games. Inside, a tempting prize awaits with deadly high stakes.", "Action|Drama|Mystery", 8.0, 55, "ko", 2021, "Hwang Dong-hyuk", True),
    ("Crash Landing on You", "The absolute top secret love story of a chaebol heiress who made an emergency landing in North Korea because of a paragliding accident and a North Korean special officer who falls in love with her.", "Comedy|Romance", 8.7, 85, "ko", 2019, "Lee Jeong-hyo", False),
    ("Vincenzo", "During a visit to his motherland, a Korean-Italian mafia lawyer gives an unrivaled conglomerate a taste of its own medicine with a side of justice.", "Action|Comedy|Crime", 8.4, 80, "ko", 2021, "Kim Hee-won", False),
    ("Stranger Things", "When a young boy disappears, his mother, a police chief and his friends must confront terrifying supernatural forces in order to get him back.", "Drama|Fantasy|Horror", 8.7, 50, "en", 2016, "The Duffer Brothers", False),
    ("Dark", "A family saga with a supernatural twist, set in a German town where the disappearance of two young children exposes the relationships among four families.", "Crime|Drama|Mystery", 8.7, 60, "de", 2017, "Baran bo Odar", True),
    
    # Anime
    ("Your Name", "Two strangers find themselves linked in a bizarre way. When a connection forms, will distance be the only thing to keep them apart?", "Animation|Drama|Fantasy", 8.4, 106, "ja", 2016, "Makoto Shinkai", False),
    ("Spirited Away", "During her family's move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits, and where humans are changed into beasts.", "Animation|Adventure|Family", 8.6, 125, "ja", 2001, "Hayao Miyazaki", False),
    ("Attack on Titan", "After his hometown is destroyed and his mother is killed, young Eren Jaeger vows to cleanse the earth of the giant humanoid Titans that have brought humanity to the brink of extinction.", "Animation|Action|Adventure", 9.1, 24, "ja", 2013, "Tetsurō Araki", True),
    ("Death Note", "An intelligent high school student goes on a secret crusade to eliminate criminals from the world after discovering a notebook capable of killing anyone whose name is written into it.", "Animation|Crime|Drama", 8.9, 24, "ja", 2006, "Tetsurō Araki", True),
    
    # Horror / Thrillers
    ("The Conjuring", "Paranormal investigators Ed and Lorraine Warren work to help a family terrorized by a dark presence in their farmhouse.", "Horror|Mystery|Thriller", 7.5, 112, "en", 2013, "James Wan", True),
    ("Get Out", "A young African-American visits his white girlfriend's parents for the weekend, where his simmering uneasiness about their reception of him eventually reaches a boiling point.", "Horror|Mystery|Thriller", 7.8, 104, "en", 2017, "Jordan Peele", True),
    ("Parasite", "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.", "Comedy|Drama|Thriller", 8.5, 132, "ko", 2019, "Bong Joon Ho", True)
]

all_items = []
for idx, m in enumerate(movies_data):
    title, overview, genres, rating, runtime, lang, year, director, adult = m
    
    all_items.append({
        "item_id": idx + 1,
        "tmdb_id": 10000 + idx,
        "title": f"{title} ({year})",
        "original_title": title,
        "overview": overview,
        "rating": rating,
        "popularity": random.uniform(50.0, 500.0),
        "language": lang,
        "genres": genres,
        "poster_url": f"https://placehold.co/300x450/111111/66fcf1?text={title.replace(' ', '+')}",
        "backdrop_url": f"https://placehold.co/1280x720/111111/66fcf1?text={title.replace(' ', '+')}+Backdrop",
        "is_adult": adult,
        "director": director
    })

df = pd.DataFrame(all_items)
df.to_csv("data/raw/movies.csv", index=False)
print(f"Successfully generated {len(df)} global items to data/raw/movies.csv!")

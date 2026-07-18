import csv
import os

class MovieRepository:
    """
    Centralized repository for accessing movie data.
    Provides standard access patterns to replace direct global variables.
    """
    _instance = None
    
    def __new__(cls, data_path="data/raw/movies.csv"):
        if cls._instance is None:
            cls._instance = super(MovieRepository, cls).__new__(cls)
            cls._instance._load_data(data_path)
        return cls._instance

    def _load_data(self, data_path):
        self.movies_db = {}
        self._genres = set()
        self._languages = set()
        self._years = set()
        self._content_types = set()

        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        iid = int(row.get('item_id', 0))
                        self.movies_db[iid] = row
                        
                        # Extract metadata for quick discovery lookup
                        if 'genres' in row and row['genres']:
                            for g in row['genres'].split('|'):
                                if g.strip():
                                    self._genres.add(g.strip())
                        
                        if 'language' in row and row['language']:
                            self._languages.add(row['language'].strip())
                            
                        if 'year' in row and row['year']:
                            self._years.add(str(row['year']).strip())

                        if 'content_type' in row and row['content_type']:
                            self._content_types.add(row['content_type'].strip().lower())
                            
                    except ValueError:
                        pass
        else:
            print(f"Warning: MovieRepository could not find {data_path}")
            
    def get_by_id(self, item_id: int):
        return self.movies_db.get(item_id)
        
    def get_all(self):
        return self.movies_db

    def get_genres(self):
        return sorted(list(self._genres))

    def get_languages(self):
        return sorted(list(self._languages))

    def get_years(self):
        return sorted(list(self._years))

    def get_content_types(self):
        return sorted(list(self._content_types))

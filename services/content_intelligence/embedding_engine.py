import os
import json
import numpy as np
import faiss

class EmbeddingEngine:
    """
    Handles generation of embeddings using sentence-transformers,
    and managing the FAISS index for semantic similarity.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingEngine, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.index_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/index/semantic_items.index'))
        self.mapping_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/index/semantic_items_mapping.json'))
        
        self.model = None
        self.index = None
        self.id_mapping = []
        
        self._load_model()
        self._load_index()

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            print("Loading SentenceTransformer model...")
            # all-MiniLM-L6-v2 is fast and effective for semantic search
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Failed to load SentenceTransformer: {e}")

    def _load_index(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            if os.path.exists(self.mapping_path):
                with open(self.mapping_path, 'r') as f:
                    self.id_mapping = json.load(f)
        else:
            # 384 is the dimension for all-MiniLM-L6-v2
            self.index = faiss.IndexFlatL2(384)
            self.id_mapping = []

    def _save_index(self):
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            with open(self.mapping_path, 'w') as f:
                json.dump(self.id_mapping, f)

    def generate_embedding(self, text: str) -> np.ndarray:
        if self.model is None:
            self._load_model()
        if self.model is None:
            return np.zeros((1, 384), dtype='float32')
            
        return self.model.encode([text], convert_to_numpy=True).astype('float32')

    def add_item(self, item_id: int, text_content: str):
        """Generates embedding for text and adds it to FAISS"""
        if self.index is None:
            self._load_index()
            
        # Check if already exists (very basic check)
        if item_id in self.id_mapping:
            return
            
        emb = self.generate_embedding(text_content)
        self.index.add(emb)
        self.id_mapping.append(item_id)
        self._save_index()

    def search_similar(self, query_text: str, top_k: int = 15) -> list[tuple[int, float]]:
        """Returns list of (item_id, distance)"""
        if self.index is None or self.index.ntotal == 0:
            return []
            
        emb = self.generate_embedding(query_text)
        distances, indices = self.index.search(emb, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.id_mapping):
                results.append((self.id_mapping[idx], float(distances[0][i])))
                
        return results

    def get_item_embedding(self, item_id: int) -> np.ndarray:
        """Fetch embedding for a specific item"""
        if self.index is None or item_id not in self.id_mapping:
            return None
            
        idx = self.id_mapping.index(item_id)
        emb = self.index.reconstruct(idx)
        return np.array([emb]).astype('float32')

# AURORA AI

**Enterprise-Scale Real-Time Recommendation Intelligence Platform**

*Tagline: "Unified Recommendations, Retrieval Intelligence, Agentic Personalization, and Real-Time Ranking at Planet Scale."*

AURORA AI is a production-grade Recommendation + Retrieval + Agentic Decisioning Platform. It combines real-time recommendation systems, enterprise RAG, knowledge graph intelligence, agentic AI, multimodal understanding, and online learning into a single enterprise ecosystem.

## Architecture & Phased Roadmap

This project is built iteratively through the following phases:

1. **Phase 1: MVP (Minimum Viable Product)**
   - Foundational architecture
   - Mock data generation
   - Local FAISS vector database
   - Simple FastAPI backend serving content-based recommendations
2. **Phase 2: Production Recommender**
   - Deep Learning & Matrix Factorization
   - Multi-stage ranking
3. **Phase 3: Real-Time Platform**
   - Kafka and Stream Processing
   - Feature Store integration
4. **Phase 4: Enterprise RAG & Graph Intelligence**
   - Document ingestion and GraphRAG (Neo4j)
5. **Phase 5: Agentic Intelligence**
   - Planner, Retriever, Summarizer agents
6. **Phase 6: Multimodal AI & Autonomous Optimization**

## Getting Started (Phase 1 MVP)

### Prerequisites
- Python 3.10+

### Setup

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate mock data:**
   ```bash
   python pipelines/ingestion/mock_data.py
   ```

4. **Build the Vector Index (FAISS):**
   ```bash
   python pipelines/training/build_vector_index.py
   ```
   *Note: This step downloads the `all-MiniLM-L6-v2` SentenceTransformer model (approx. 90MB) locally.*

5. **Run the Recommendation Service:**
   ```bash
   uvicorn services.recommendation.main:app --reload
   ```

### API Usage

You can access the interactive API docs at: `http://localhost:8000/docs`

Example Request to `/recommend`:
```json
{
  "query": "I want a space adventure with AI",
  "top_k": 3
}
```

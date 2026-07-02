import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.ranking.main import app as ranking_app
from services.agent.main import app as agent_app

class TestSearchEndpoints(unittest.TestCase):
    def test_ranking_search_endpoint(self):
        # Use context manager to trigger FastAPI startup event
        with TestClient(ranking_app) as client:
            payload = {
                "query": "something like Inception or Interstellar",
                "top_k": 5
            }
            response = client.post("/search", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, list)
            if len(data) > 0:
                first_item = data[0]
                self.assertIn("item_id", first_item)
                self.assertIn("title", first_item)
                self.assertIn("retrieval_score", first_item)

    @patch("requests.post")
    def test_agent_search_endpoint(self, mock_post):
        # Mock ranking service response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"item_id": 1, "title": "Inception", "retrieval_score": 1.2, "ranking_score": 1.2},
            {"item_id": 2, "title": "The Dark Knight", "retrieval_score": 1.0, "ranking_score": 1.0}
        ]
        mock_post.return_value = mock_response

        with TestClient(agent_app) as client:
            payload = {
                "query": "dark knight rises superhero",
                "top_k": 3
            }
            headers = {"Authorization": "Bearer guest-token"}
            response = client.post("/search", json=payload, headers=headers)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, list)
            self.assertTrue(len(data) > 0)
            self.assertEqual(data[0]["item_id"], 1)
            self.assertEqual(data[0]["title"], "Inception")

if __name__ == "__main__":
    unittest.main()

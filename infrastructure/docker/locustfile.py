import random
from locust import HttpUser, task, between

class StreamoraUserBehavior(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Register and authenticate test user."""
        self.user_email = f"loadtest_{random.randint(1000, 99999)}@streamora.ai"
        self.password = "LoadTestPass2026!"
        
        # Register
        self.client.post("/api/v2/auth/register", json={
            "email": self.user_email,
            "password": self.password,
            "full_name": "Load Test User"
        })

        # Login
        res = self.client.post("/api/v2/auth/login", json={
            "email": self.user_email,
            "password": self.password
        })

        if res.status_code == 200:
            token = res.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}

    @task(4)
    def view_hero_banner(self):
        self.client.get("/api/v2/hero/banner", headers=self.headers)

    @task(3)
    def view_discovery_collections(self):
        self.client.get("/api/v2/discovery/collections", headers=self.headers)

    @task(3)
    def get_personalized_recommendations(self):
        self.client.get("/api/v2/recommendations/personalized", headers=self.headers)

    @task(2)
    def execute_search(self):
        queries = ["Inception", "Sci-Fi", "Christopher Nolan", "Marvel", "Action"]
        q = random.choice(queries)
        self.client.get(f"/api/v2/search?q={q}", headers=self.headers)

    @task(1)
    def get_media_bundle(self):
        content_id = random.randint(1, 5)
        self.client.get(f"/api/v2/media/bundle/{content_id}", headers=self.headers)

    @task(2)
    def sync_playback_progress(self):
        self.client.post("/api/v2/playback/progress", json={
            "content_id": 1,
            "progress_seconds": random.randint(100, 5000),
            "duration_seconds": 9000
        }, headers=self.headers)

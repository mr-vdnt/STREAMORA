from locust import HttpUser, task, between

class StreamoraUser(HttpUser):
    # Simulate users clicking around every 1-5 seconds
    wait_time = between(1, 5)

    @task(5)
    def view_homepage(self):
        """Simulates viewing the homepage."""
        self.client.get("/")

    @task(3)
    def view_trending(self):
        """Simulates requesting the trending lists (should be heavily cached)."""
        self.client.get("/discover/genre/Action")

    @task(1)
    def ask_ai(self):
        """Simulates asking the AI a question."""
        # Using a fixed prompt to test semantic caching
        self.client.post("/chat", json={
            "query": "Show me some great sci-fi movies",
            "exclude_ids": []
        })

    @task(2)
    def auth_login(self):
        """Simulates login attempts."""
        self.client.post("/token", data={
            "username": "testuser",
            "password": "password"
        })

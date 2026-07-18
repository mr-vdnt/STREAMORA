from fastapi import FastAPI
from api.routes import health, recommendations
from services.platform.startup import startup_event, shutdown_event
import time

app = FastAPI(
    title="Streamora Recommendation API",
    description="Core backend API for Streamora's recommendation engine.",
    version="1.0.0"
)

# Register Events
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

# Register Routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

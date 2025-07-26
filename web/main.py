"""FastAPI web application for CoreLogger."""

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from web.routes import router

# Create FastAPI app
app = FastAPI(
    title="CoreLogger Web Interface",
    description="A thoughtful logging system with AI integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

# Mount static files (if we have any)
# app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Root redirect
@app.get("/")
async def root():
    """Redirect root to dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=302)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)

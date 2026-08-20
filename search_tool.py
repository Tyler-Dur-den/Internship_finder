import os
from dotenv import load_dotenv
from serpapi import GoogleSearch

load_dotenv()

def serpapi_search(query: str, location: str = "Bangalore", limit: int = 5):
    params = {
        "engine": "google_jobs",
        "q": f"{query} intern",
        "location": location,
        "api_key": os.getenv("SERPAPI_API_KEY")
    }
    search = GoogleSearch(params)
    results = search.get_dict().get("jobs_results", [])
    return results[:limit]
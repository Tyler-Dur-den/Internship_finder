import os
from dotenv import load_dotenv
from serpapi import GoogleSearch

load_dotenv()

def serpapi_search(domain: str, location: str = "Bangalore"):
    params = {
        "engine": "google_jobs",
        "q": f"{domain} intern",
        "location": location,
        "api_key": os.getenv("SERPAPI_API_KEY")
    }
    search = GoogleSearch(params)
    response = search.get_dict()
    return response.get("jobs_results", [])
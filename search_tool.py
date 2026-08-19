from serpapi import GoogleSearch
import os
from dotenv import load_dotenv
load_dotenv()

def serpapi_search():
    params = {
        "engine": "google_jobs",
        "q":"Ai engineer intern",
        "location": "Bangalore",
        "api_key": os.getenv("SERPAPI_API_KEY")
    }
    search = GoogleSearch(params)
    response = search.get_dict()
    return response.get("jobs_results", [])
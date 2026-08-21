import os
from dotenv import load_dotenv
from serpapi import GoogleSearch

load_dotenv()

def serpapi_search(query: str, location: str = "Bangalore", limit: int = 5) -> list[dict]:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SERPAPI_API_KEY environment variable is not set in .env")

    params = {
        "engine": "google_jobs",
        "q": f"{query} intern",
        "location": location,
        "api_key": api_key
    }

    search = GoogleSearch(params)
    raw_results = search.get_dict().get("jobs_results", [])

    cleaned_results = []
    for job in raw_results[:limit]:
        cleaned_results.append({
            "job_id": job.get("job_id"),
            "title": job.get("title"),
            "company": job.get("company_name"),
            "location": job.get("location"),
            "posted_at": job.get("detected_extensions", {}).get("posted_at", "N/A"),
            "apply_link": _extract_best_apply_link(job)
        })

    return cleaned_results

BLOCKED_DOMAINS = [
    "bebee.com", "jooble.org", "talent.com", "neuvoo.com", 
    "ziprecruiter.com", "lensa.com", "jobget.com", "monster.com"
]

TRUSTED_PLATFORMS = [
    "greenhouse.io", "lever.co", "workday.com", "myworkdayjobs.com", 
    "ashbyhq.com", "smartrecruiters.com", "wellfound.com", "angel.co",
    "internshala.com"  # Legit for Indian internship listings
]

def _is_blocked(url: str) -> bool:
    if not url:
        return True
    return any(blocked in url.lower() for blocked in BLOCKED_DOMAINS)

def _extract_best_apply_link(job_result: dict) -> str:
    apply_options = job_result.get("apply_options") or []

    clean_options = [
        opt.get("link", "") for opt in apply_options 
        if isinstance(opt, dict) and not _is_blocked(opt.get("link", ""))
    ]

    for link in clean_options:
        if any(platform in link.lower() for platform in TRUSTED_PLATFORMS):
            return link

    if clean_options:
        return clean_options[0]

    share_link = job_result.get("share_link", "")
    if share_link and not _is_blocked(share_link):
        return share_link

    company = job_result.get("company_name", job_result.get("company", ""))
    title = job_result.get("title", "internship")
    return f"https://www.google.com/search?q={company}+{title}+careers".replace(" ", "+")
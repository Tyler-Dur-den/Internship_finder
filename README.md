# 🎯 AI Internship Finder

An agentic AI system that analyses your resume, searches live internship 
listings, and generates a personalised skill gap report — all in one workflow.

## The Problem

Finding internships manually is slow. You visit multiple job boards, copy 
paste job descriptions, and manually figure out which roles match your skills 
and which don't. This project automates the entire process.

## How It Works

Enter a username, upload your resume and target role. The system:
1. Parses your resume and extracts technical skills and experience level
2. Simultaneously searches live Google Jobs listings using SerpApi
3. Generates a skill gap report for each internship — match percentage, 
   missing skills, and a direct recommendation on whether to apply
4. Saves your search history to PostgreSQL — revisit past searches anytime

## Architecture
```text
┌──────────────────────────────────────────┐
│        User (Streamlit Frontend)         │
└────────────────────┬─────────────────────┘
                     │ HTTP Request
                     ▼
┌──────────────────────────────────────────┐
│         FastAPI Backend (Render)         │
└────────────────────┬─────────────────────┘
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
┌──────────────┐            ┌──────────────┐
│   Resume     │            │  Internship  │
│  Analyser    │            │    Finder    │
│(Gemini Flash)│            │(SerpApi Jobs)│
└──────┬───────┘            └──────┬───────┘
       └─────────────┬─────────────┘
                     ▼
┌──────────────────────────────────────────┐
│            Skill Gap Analyser            │
│              (Gemini Flash)              │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│            PostgreSQL (Neon)             │
│          (Search History Saved)          │
└──────────────────────────────────────────┘
```

## Tech Stack

**Frontend:** Streamlit — deployed on Streamlit Cloud  
**Backend:** FastAPI — deployed on Render  
**Orchestration:** LangGraph, LangChain  
**LLM:** Google Gemini Flash  
**Search:** SerpApi Google Jobs API  
**Database:** PostgreSQL (Neon) via SQLAlchemy  
**Containerisation:** Docker  
**PDF Parsing:** PyPDF  
**Validation:** Pydantic  

## Challenges and Optimizations

**1. Token limit on skill gap analysis**
Initially called the LLM once per internship — 10 internships meant 10 
separate LLM calls. Fixed by creating a `SkillsGapContainer` Pydantic 
wrapper that processes all internships in a single LLM call — reducing 
token costs and latency significantly.

**2. Poor search result quality with Tavily**
Tavily returned irrelevant results from YouTube and Instagram instead of 
job postings. Replaced with SerpApi's Google Jobs endpoint which returns 
structured, targeted listings directly.

**3. Parallel agent execution**
Resume analysis and internship search were running sequentially. 
Restructured the LangGraph DAG to run both nodes in parallel — resume 
analyser and internship finder execute simultaneously since they don't 
depend on each other.

**4. Unnecessary LLM extraction of structured data**
Was using an LLM to re-parse SerpApi results that were already structured 
JSON. Removed this step entirely — saving tokens and reducing latency.

**5. Event loop blocking**
`graph.invoke()` is synchronous and was blocking FastAPI's async event 
loop. Fixed using `run_in_threadpool` so the graph runs in a separate 
thread — FastAPI remains non-blocking under concurrent requests.

## Setup

1. Clone the repo
```bash
git clone https://github.com/Tyler-Dur-den/Internship_finder
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Create a `.env` file

GOOGLE_API_KEY=your_gemini_key
SERPAPI_API_KEY=your_serpapi_key
DATABASE_URL=your_neon_postgresql_url


4. Run with Docker
```bash
docker build -t internship-finder .
docker run -p 8000:8000 --env-file .env internship-finder
```

5. Or run directly
```bash
uvicorn api:app --reload      # backend
streamlit run app.py          # frontend
```

## Live Demo
[Frontend](https://internshipfinder-765rs.streamlit.app) — 
[API Docs](https://internship-finder-ielk.onrender.com/docs)

## Limitations
- Scanned PDFs are not supported
- SerpApi free tier has limited monthly searches so only 5 search results
- Username-based history is not authenticated — use a unique username
- Render free tier spins down after inactivity — first request may take 
  30-60 seconds
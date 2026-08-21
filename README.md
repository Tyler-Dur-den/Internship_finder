# 🎯 AI Internship Finder

An agentic AI system that analyses your resume, searches live internship 
listings, and generates a personalised skill gap report — all in one workflow.

## The Problem

Finding internships manually is slow. You visit multiple job boards, copy 
paste job descriptions, and manually figure out which roles match your skills 
and which don't. This project automates the entire process.

## How It Works

Upload your resume and enter your target role. The agent:
1. Parses your resume and extracts your technical skills and experience level
2. Simultaneously searches live Google Jobs listings using SerpApi
3. Structures raw job results into clean internship metadata
4. Generates a skill gap report for each internship — match percentage, 
   missing skills, and a direct recommendation on whether to apply

## Architecture & Execution Flow

The workflow is orchestrated using **LangGraph** as a Directed Acyclic Graph (DAG):

1. **`START` $\rightarrow$ `resume_analyser` & `internship_finder` (Parallel Execution):**
   * `resume_analyser`: Parses uploaded resume text and extracts candidate technical skills.
   * `internship_finder`: Fetches top matching job listings from Google Jobs via SerpApi.
2. **`skill_gap` (Convergence Node):**
   * Merges extracted candidate skills and job descriptions to perform structured batch comparative analysis via Google Gemini (`gemini-3.6-flash`)

## Tech Stack

* **Frontend Framework:** Streamlit
* **Workflow Orchestration:** LangGraph, LangChain
* **LLM Providers:** Google Gemini (`gemini-3.6-flash`)
* **Search Integration:** SerpApi (Google Jobs API)
* **PDF Engine:** PyPDF
* **Data Validation:** Pydantic

## Challenges and Optimizations

**1. Token limit on skill gap analysis**
Initially called the LLM once per internship — 10 internships meant 10 
separate LLM calls. This was slow and expensive. Fixed by creating a 
`SkillsGapContainer` Pydantic wrapper that processes all internships in 
a single LLM call.

**2. Poor search result quality with Tavily**
Tavily returned irrelevant results from YouTube, Instagram, and LinkedIn 
instead of actual job postings. Replaced with SerpApi's Google Jobs 
endpoint which returns structured, targeted job listings directly.

**3. Parallel agent execution**
Resume analysis and internship search were running sequentially even 
though they don't depend on each other. Restructured the LangGraph 
workflow to run both nodes in parallel — resume analyser extracts skills 
while internship finder searches simultaneously, reducing total runtime.

**4. Unnecessary LLM extraction of structured data**
Was using an LLM to re-parse SerpApi results that were already structured 
JSON. Removed this step entirely — SerpApi data is used directly, saving 
tokens and reducing latency.

## Setup

1. Clone the repo
   git clone https://github.com/Tyler-Dur-den/internship-finder

2. Install dependencies
   pip install -r requirements.txt

3. Create a .env file
   GOOGLE_API_KEY=your_gemini_key
   GROQ_API_KEY=your_groq_key
   SERPAPI_KEY=your_serpapi_key

4. Run the app
   streamlit run app.py

## Live Demo
[Try it here](https://internshipfinder-765rs.streamlit.app)

## Limitations
- Scanned PDFs are not supported
- SerpApi free tier has limited monthly searches
- Results depend on what Google Jobs currently indexes
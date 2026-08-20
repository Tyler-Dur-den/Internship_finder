import os
from typing import TypedDict
from pydantic import BaseModel, Field
from pypdf import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from search_tool import serpapi_search

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

class ResumeSkills(BaseModel):
    skills: list[str] = Field(description="List of key technical skills extracted from resume")
    level: str = Field(description="beginner, intermediate or experienced")

class SkillGapReport(BaseModel):
    matched_skills: list[str] = Field(description="Skills user has that match the role")
    missing_skills: list[str] = Field(description="Required skills for the role that user lacks")
    match_percentage: float = Field(description="Percentage match (0 to 100)")
    recommendations: str = Field(description="Direct advice on applying")

class SkillsGapContainer(BaseModel):
    listings: list[SkillGapReport] = Field(description="Skill gap reports matching each internship in order")

class InternshipState(TypedDict):
    skills: list[str]
    level: str
    domain: str
    location: str
    internships_found: list[dict]
    skill_gap: list[dict]
    resume_path: str | None

resume_llm = llm.with_structured_output(ResumeSkills)
def resume_analyser(state: InternshipState):
    resume_path = state.get("resume_path")
    if not resume_path or not os.path.exists(resume_path):
        return {"skills": [], "level": "entry-level"}

    reader = PdfReader(resume_path)
    resume_text = "\n".join(page.extract_text() or "" for page in reader.pages)

    prompt = f"Extract core technical skills and experience level from this resume:\n{resume_text}"
    result = resume_llm.invoke(prompt)

    return {
        "skills": result.skills,
        "level": result.level
    }

def internship_finder(state: InternshipState):
    domain = state.get('domain', '')
    #skills = state.get('skills', [])
    location = state.get('location', 'Bangalore')

    #top_skills = " ".join(skills[:3]) if skills else ""
    #query = f"{domain} {top_skills}".strip()
    raw_results = serpapi_search(query =domain, location=location, limit=5)

    parsed_jobs = []
    for item in raw_results:
        parsed_jobs.append({
            "company_name": item.get("company_name", "N/A"),
            "role_title": item.get("title", "N/A"),
            "location": item.get("location", location),
            "worktype": "N/A",
            "duration": "N/A",
            "stipend_range": "Not mentioned",
            "website_link": item.get("share_link") or item.get("link") or "",
            "description": item.get("description", "")
        })

    return {"internships_found": parsed_jobs}

gap_llm = llm.with_structured_output(SkillsGapContainer)

def skill_gap(state: InternshipState):
    user_skills = state.get("skills", [])
    internships = state.get("internships_found", [])

    if not internships:
        return {"skill_gap": []}

    prompt = f"""
    User Skills: {user_skills}
    Analyze each internship below and compare its required skills against 'User Skills'.
    Generate a gap report for each internship in the exact same order as listed.

    Internships:
    {internships}
    """

    response = gap_llm.invoke(prompt)
    return {"skill_gap": [item.model_dump() for item in response.listings]}

builder = StateGraph(InternshipState)

builder.add_node("resume_analyser", resume_analyser)
builder.add_node("internship_finder", internship_finder)
builder.add_node("skill_gap", skill_gap)

builder.add_edge(START, "resume_analyser")
builder.add_edge(START, "internship_finder")

builder.add_edge("resume_analyser", "skill_gap")
builder.add_edge("internship_finder", "skill_gap")
builder.add_edge("skill_gap", END)

graph = builder.compile()
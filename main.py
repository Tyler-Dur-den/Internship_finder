import os
from typing import TypedDict, Annotated, Literal, List
from pydantic import BaseModel, Field
from pypdf import PdfReader

from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from search_tool import serpapi_search

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

alt_llm = ChatGroq(model_name="openai/gpt-oss-120b")

class InternshipMetadata(BaseModel):
    company_name: str = Field(description="Name of the company")
    role_title: str = Field(description="Title of internship")
    location: str = Field(description="Location of company")
    level: str = Field(description="beginner, intermediate or experienced")
    worktype: Literal["inoffice", "remote", "both"] = Field(description="Work arrangement")
    duration: str | None = Field(default=None, description="Duration of internship")
    skills: list[str] = Field(default_factory=list, description="List of required skills")
    work: str | None = Field(default=None, description="Description of the work")
    stipend_range: str = Field(description="Stipend range or 'Not mentioned'")
    website_link: str = Field(description="Link to the job posting")


class InternshipListContainer(BaseModel):
    listings: list[InternshipMetadata] = Field(description="List of extracted internship postings")

class ResumeSkills(BaseModel):
    skills: list[str] = Field(description="List of technical skills extracted from resume")
    level: str = Field(description="beginner, intermediate or experienced")

class SkillGapReport(BaseModel):
    matched_skills: list[str] = Field(description="Skills user has that match the role")
    missing_skills: list[str] = Field(description="Required skills for the role that user lacks")
    match_percentage: float = Field(description="Percentage match between user skills and role requirement (0-100)")
    recommendations: str = Field(description="Direct advice on whether user should apply and why")

class SkillsGapContainer(BaseModel):
    listings: list[SkillGapReport] = Field(description="Skill gap reports matching each internship in order")

class InternshipState(TypedDict):
    skills: list[str]
    level: str
    domain: str
    location: str = Field(description="Location of company")
    internships_found: list[dict]
    skill_gap: list[dict] 
    website_link: list[str]
    resume_path: str

resume_llm = llm.with_structured_output(ResumeSkills)
def resume_analyser(state: InternshipState):
    reader = PdfReader(state["resume_path"])
    resume_text = "\n".join(page.extract_text() or "" for page in reader.pages)

    prompt = f"Extract skills and experience level from this resume:\n{resume_text}"
    result = resume_llm.invoke(prompt)

    return {
        "skills": result.skills,
        "level": result.level
    }

def internship_finder(state: InternshipState):
    domain = state['domain']
    location = state['location']
    raw_results = serpapi_search(domain,location)
    
    urls = [item.get("link") or item.get("url") for item in raw_results if item.get("link") or item.get("url")]
    return {
        "internships_found": raw_results,
        "website_link": urls
    }

extraction_llm = llm.with_structured_output(InternshipListContainer)
def extraction(state: InternshipState):
    raw_results = state["internships_found"]

    prompt = f"""
    Extract structured internship details from the following raw search results.
    Raw results: {raw_results}
    """

    internship_container = extraction_llm.invoke(prompt)
    listings_dict = [item.model_dump() for item in internship_container.listings]

    return {"internships_found": listings_dict}

gap_llm = alt_llm.with_structured_output(SkillsGapContainer)
def skill_gap(state: InternshipState):
    user_skills = state["skills"]
    internships = state["internships_found"]

    prompt = f"""
    User Skills: {user_skills}

    Analyze each internship below and compare its required 'skills' against 'User Skills'.
    Generate a gap report for each internship in the exact same order as listed.

    Internships:
    {internships}
    """

    response = gap_llm.invoke(prompt)
    return {"skill_gap": [item.model_dump() for item in response.listings]}

builder = StateGraph(InternshipState)

builder.add_node("resume_analyser", resume_analyser)
builder.add_node("internship_finder", internship_finder)
builder.add_node("extraction", extraction)
builder.add_node("skill_gap", skill_gap)

builder.add_edge(START, "resume_analyser")
builder.add_edge(START, "internship_finder")
builder.add_edge("resume_analyser", "extraction")
builder.add_edge("internship_finder", "extraction")
builder.add_edge("extraction", "skill_gap")
builder.add_edge("skill_gap", END)

graph = builder.compile()

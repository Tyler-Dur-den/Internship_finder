from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from typing import TypedDict, Annotated, Literal, List
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_community.document_loaders import PyPDFLoader
import os

from search_tool import serpapi_search

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

alt_llm = ChatGroq(model_name="openai/gpt-oss-120b")

class Internship_metadata(BaseModel):
    company_name : str = Field(description="Name of the company")
    role_title : str = Field(description="Title of internship")
    location : str = Field(description="location of company")
    level : str = Field(description="beginner, intermediate or experienced as per internships")
    worktype : Literal["inoffice","remote", "both"] = Field(description="where they except us to work")
    duration : str | None = Field(default=None,description="Duration of intership")
    skills : list[str] = Field(default_factory=list, description="List of skills required") 
    work : str | None = Field(default=None, description="What is the work")
    stipend_range : str = Field(description="Stipend range(e.g, '₹30k-50k/month') return 0 is not mentioned")
    website_link : str = Field(description="link of website page that contain this internship")

class InternshipListContainer(BaseModel):
    listings: list[Internship_metadata] = Field(description="List of extracted internship postings")

class ResumeSkills(BaseModel):
    skills: list[str] = Field(description="List of technical skills extracted from resume")
    domain: str = Field(description="Main domain e.g AI, web dev, ML")
    level: str = Field(description="beginner, intermediate or experienced")

class skills_gap(BaseModel):
    matched_skills : list[str] = Field(description="Skills user have that match the role")
    missing_skills : list[str] = Field(description="Skills user do not that that is required for the role")
    match_percentage : int = Field(description="Percentage of match between user skills and role")
    recomendations : str = Field(description="should user apply?,why")

class Skills_gap_container(BaseModel):
    listings : list[skills_gap] = Field(description="Skill gap reports for each internship")

class InternshipState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    skills : list[str]
    required_skills : list[str]
    level : str
    domain : str
    internships_found : list[dict]
    skill_gap : list[str]
    website_link : list[str]
    resume_path : str

resume_llm = llm.with_structured_output(ResumeSkills)
def resume_analyser(state:InternshipState):
    loader = PyPDFLoader(state["resume_path"])
    docs = loader.load()
    resume_text = "\n".join(doc.page_content for doc in docs)

    prompt = f"Extract skills, domain and level from this resume \n{resume_text}"
    result = resume_llm.invoke(prompt)

    return {
        "skills" : result.skills,
        "level" : result.level,
        "domain" : result.domain
    }

def internship_finder(state: InternshipState):

    raw_results = serpapi_search()
    urls = [item.get("url") for item in raw_results if item.get("url")]
    
    return {
        "internships_found": raw_results,
        "website_link": urls
    }

extraction_llm = llm.with_structured_output(InternshipListContainer)
def extraction(state:InternshipState):
    raw_results = state["internships_found"]

    prompt = f"""Extract internship details from the following search results
    results : {raw_results}
    """

    internship_list_container = extraction_llm.invoke(prompt)
    listings_dict = [item.model_dump() for item in internship_list_container.listings]
    
    return {
        "internships_found": listings_dict
    }

gap_llm = alt_llm.with_structured_output(Skills_gap_container)
def skill_gap(state:InternshipState):
    user_skills = state["skills"]
    internships = state["internships_found"]
    prompt = f"""
    User Skills: {user_skills}

    Analyze each internship below and compare its required 'skills' against the 'User Skills'.
    Identify which required skills the user is missing for each job, and assign a match score (0-100).

    Internships:
    {internships}
    """

    response = gap_llm.invoke(prompt)
    return {'skill_gap' : [item.model_dump() for item in response.listings]}


builder = StateGraph(InternshipState)

builder.add_node("resume_analyser", resume_analyser)
builder.add_node("internship_finder", internship_finder)
builder.add_node("extraction", extraction)
builder.add_node("skill_gap",skill_gap)

builder.add_edge(START, "resume_analyser")
builder.add_edge("resume_analyser", "internship_finder")
builder.add_edge("internship_finder", "extraction")
builder.add_edge("extraction", "skill_gap")
builder.add_edge("skill_gap", END)

graph = builder.compile()

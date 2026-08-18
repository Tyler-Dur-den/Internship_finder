from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from typing import TypedDict, Annotated, Literal, List
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_community.document_loaders import PyPDFLoader
import os

from search_tool import tavily_search

llm = ChatGroq(model_name="openai/gpt-oss-120b")

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

class InternshipState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    skills : list[str]
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

    skills_str = " ".join(state['skills'][:5])
    query = f"AI engineer internship {skills_str} Bangalore 2026 site:internshala.com, site:wellfound.com or site:linkedin.com"
    
    raw_results = tavily_search(query)
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

builder = StateGraph(InternshipState)

builder.add_node("resume_analyser", resume_analyser)
builder.add_node("internship_finder", internship_finder)
builder.add_node("extraction", extraction)

builder.add_edge(START, "resume_analyser")
builder.add_edge("resume_analyser", "internship_finder")
builder.add_edge("internship_finder", "extraction")
builder.add_edge("extraction", END)

graph = builder.compile()

if __name__ == "__main__":
    test_input = {"resume_path": "resume.pdf"} 
    
    print("Parsing resume and searching...")
    output = graph.invoke(test_input)
    
    print(f"\nSkills extracted: {output.get('skills')}")
    print(f"Found {len(output.get('internships_found', []))} structured internships.")
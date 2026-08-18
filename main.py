from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from typing import TypedDict, Annotated, Literal, List
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
import os

from search_tool import tavily_search

llm = ChatGroq(model_name="llama-3.3-70b-versatile")

class Internship_metadata(BaseModel):
    company_name : str = Field(description="Name of the company")
    role_title : str = Field(description="Title of internship")
    location : str = Field(description="location of company")
    worktype : Literal["inoffice","remote", "both"] = Field(description="where they except us to work")
    duration : str | None = Field(default=None,description="Duration of intership")
    skills : list[str] = Field(default_factory=list, description="List of skills required")
    work : str | None = Field(default=None, description="What is the work")
    stipend_range : str = Field(description="Stipend range(e.g, '₹30k-50k/month') return 0 is not mentioned")
    website_link : str = Field(description="link of website page that contain this internship")

class InternshipState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    userskills : list[str]
    internships_found : list[dict]
    skill_gap : list[str]
    website_link : list[str]

def internship_finder(state:InternshipState):
    query = f"AI engineer internship {' '.join(state['userskills'])} Bangalore 2026 site:internshala.com OR site:wellfound.com OR site:linkedin.com"
    internships = tavily_search(query)
    return {
        "internships_found" : internships,
        "website_link" : internships["url"]
    }

extraction_llm = llm.with_structured_output(Internship_metadata)

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

builder.add_node("internship_finder",internship_finder)
builder.add_node("extraction",extraction)

builder.add_edge(START, "internship_finder")
builder.add_edge("internship_finder","extraction")
builder.add_edge("extraction", END)

graph = builder.compile()
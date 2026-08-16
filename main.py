from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from typing import TypedDict, Annotated, Literal, List
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field
from tavily import TavilyClient
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
import os

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
    location : str
    interships_found : list[dict]
    skill_gap : list[str]
    website_link : list[str]

@tool
def search_internships():
    
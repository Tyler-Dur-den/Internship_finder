from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import tempfile
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

from main import graph

app = FastAPI(
    title="AI Internship Finder API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024 

class Internship(BaseModel):
    company_name: str
    role_title: str
    location: str
    worktype: str
    stipend_range: str
    website_link: str

class SkillGap(BaseModel):
    matched_skills: list[str]
    missing_skills: list[str]
    match_percentage: float
    recommendations: str

class InternshipResponse(BaseModel):
    skills: list[str]
    level: str
    internships: list[Internship]
    skill_gaps: list[SkillGap]


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/find-internships", response_model=InternshipResponse)
async def find_internships(
    domain: str = Form(...),
    location: str = Form(default="Bangalore"),
    resume: UploadFile = File(default=None)
):
    tmp_path = None

    if resume and resume.filename:
        # Fix 1 — check content_type not filename extension
        if resume.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

        contents = await resume.read(MAX_FILE_SIZE + 1)
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size is 5MB"
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

    try:
        output = await run_in_threadpool(graph.invoke, {
            "resume_path": tmp_path,
            "domain": domain,
            "location": location,
            "skills": [],
            "level": "",
            "internships_found": [],
            "skill_gap": []
        })

        return InternshipResponse(
            skills=output.get("skills", []),
            level=output.get("level", ""),
            internships=output.get("internships_found", []),
            skill_gaps=output.get("skill_gap", [])
        )

    except Exception as e:
        # Fix 4 — log internally, never expose to client
        logger.error(f"Graph invoke failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Something went wrong. Please try again."
        )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
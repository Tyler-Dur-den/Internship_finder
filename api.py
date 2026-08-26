from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import tempfile
import os
import logging
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from database import init_db, get_db, Search
from main import graph
load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Internship Finder API", version="1.0.0")
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

@app.on_event("startup")
def startup():
    init_db()

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
    user_id: str = Form(...),
    resume: UploadFile = File(default=None),
    db: Session = Depends(get_db)
):
    tmp_path = None

    if resume and resume.filename:
        if resume.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        contents = await resume.read(MAX_FILE_SIZE + 1)
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 5MB")

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

        try:
            search_record = Search(
                user_id=user_id.lower().strip(),
                domain=domain,
                location=location,
                skills_extracted=output.get("skills", []),
                internships_found=output.get("internships_found", []),
                skill_gaps=output.get("skill_gap", [])
            )
            db.add(search_record)
            db.commit()
        except Exception as db_err:
            logger.error(f"Failed to record search in DB: {db_err}")
            db.rollback()

        return InternshipResponse(
            skills=output.get("skills", []),
            level=output.get("level", ""),
            internships=output.get("internships_found", []),
            skill_gaps=output.get("skill_gap", [])
        )

    except Exception as e:
        logger.error(f"Graph invoke failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.get("/history")
def get_history(user_id: str, db: Session = Depends(get_db)):
    try:
        searches = (
            db.query(Search)
            .filter(Search.user_id == user_id.lower().strip())
            .order_by(Search.created_at.desc())
            .limit(10)
            .all()
        )
        return [
            {
                "id": s.id,
                "domain": s.domain,
                "location": s.location,
                "skills": s.skills_extracted or [],
                "internships": s.internships_found or [],
                "searched_at": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else ""
            }
            for s in searches
        ]
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch search history")
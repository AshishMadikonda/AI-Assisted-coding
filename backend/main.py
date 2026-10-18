import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Lets this file import code from the /ai folder at the project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
from ai.classify import classify_issue  # noqa: E402

app = FastAPI(title="Civic Issue API")

# Allows the HTML pages to call this backend from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "issues.db"

CATEGORIES = [
    "road_damage",
    "water_drainage",
    "electricity",
    "sanitation",
    "mosquito_breeding",
    "streetlight",
]
STATUSES = ["reported", "assigned", "resolved"]
PROJECT_STATUSES = ["planned", "ongoing", "completed"]

# Sample department names. Replace them with your local panchayat or municipality departments.
DEPARTMENTS = {
    "road_damage": "Roads and Highways Department",
    "water_drainage": "Water Supply and Drainage Board",
    "electricity": "Electricity Board",
    "sanitation": "Sanitation Department",
    "mosquito_breeding": "Public Health Department",
    "streetlight": "Street Lighting Department",
}


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            description TEXT,
            urgency TEXT DEFAULT 'medium',
            latitude REAL,
            longitude REAL,
            status TEXT DEFAULT 'reported',
            resolution_note TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    # Databases created before the note column existed need it added
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(issues)").fetchall()]
    if "resolution_note" not in columns:
        conn.execute("ALTER TABLE issues ADD COLUMN resolution_note TEXT")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            department TEXT,
            area TEXT,
            description TEXT,
            status TEXT DEFAULT 'planned',
            start_date TEXT,
            expected_end_date TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


def add_department(row):
    issue = dict(row)
    issue["department"] = DEPARTMENTS.get(issue["category"], "Unassigned")
    return issue


def clean_date(value):
    # Accepts an empty value or a date written like 2026-12-31
    if not value:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must look like 2026-12-31")
    return value


class IssueCreate(BaseModel):
    category: str
    description: str = ""
    urgency: str = "medium"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class StatusUpdate(BaseModel):
    status: str
    note: Optional[str] = None


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    department: str = ""
    area: str = ""
    description: str = ""
    status: str = "planned"
    start_date: Optional[str] = None
    expected_end_date: Optional[str] = None


class ProjectStatusUpdate(BaseModel):
    status: str


@app.get("/")
def home():
    return {"status": "ok", "message": "Civic Issue backend running"}


@app.get("/departments")
def list_departments():
    return DEPARTMENTS


@app.post("/classify")
def classify_photo(photo: UploadFile = File(...)):
    suffix = os.path.splitext(photo.filename or "")[1].lower()
    if suffix not in (".jpg", ".jpeg", ".png"):
        raise HTTPException(status_code=400, detail="Upload a .jpg, .jpeg or .png photo")

    # Save the upload to a temporary file so classify_issue can read it
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(photo.file, tmp)
        tmp_path = tmp.name

    try:
        return classify_issue(tmp_path)
    except Exception as error:
        print(f"classify error: {error}")
        raise HTTPException(
            status_code=502,
            detail="AI classification failed. Check the backend terminal for details.",
        )
    finally:
        os.remove(tmp_path)


@app.post("/issues")
def create_issue(issue: IssueCreate):
    if issue.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"category must be one of {CATEGORIES}")
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO issues (category, description, urgency, latitude, longitude, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            issue.category,
            issue.description,
            issue.urgency,
            issue.latitude,
            issue.longitude,
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {
        "id": new_id,
        "message": "Issue reported",
        "status": "reported",
        "department": DEPARTMENTS[issue.category],
    }


@app.get("/issues")
def list_issues():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM issues ORDER BY id DESC").fetchall()
    conn.close()
    return [add_department(row) for row in rows]


@app.get("/issues/{issue_id}")
def get_issue(issue_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return add_department(row)


@app.patch("/issues/{issue_id}/status")
def update_status(issue_id: int, update: StatusUpdate):
    if update.status not in STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {STATUSES}")
    conn = get_connection()
    if update.note is not None:
        cursor = conn.execute(
            "UPDATE issues SET status = ?, resolution_note = ? WHERE id = ?",
            (update.status, update.note, issue_id),
        )
    else:
        cursor = conn.execute(
            "UPDATE issues SET status = ? WHERE id = ?", (update.status, issue_id)
        )
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Issue not found")
    return {"id": issue_id, "status": update.status, "note": update.note}


@app.get("/projects")
def list_projects(status: Optional[str] = None):
    if status is not None and status not in PROJECT_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {PROJECT_STATUSES}")
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM projects WHERE status = ? ORDER BY id DESC", (status,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.post("/projects")
def create_project(project: ProjectCreate):
    if project.status not in PROJECT_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {PROJECT_STATUSES}")
    start_date = clean_date(project.start_date)
    end_date = clean_date(project.expected_end_date)
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO projects (title, department, area, description, status, "
        "start_date, expected_end_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            project.title.strip(),
            project.department,
            project.area,
            project.description,
            project.status,
            start_date,
            end_date,
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "message": "Project added", "status": project.status}


@app.patch("/projects/{project_id}/status")
def update_project_status(project_id: int, update: ProjectStatusUpdate):
    if update.status not in PROJECT_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {PROJECT_STATUSES}")
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE projects SET status = ? WHERE id = ?", (update.status, project_id)
    )
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"id": project_id, "status": update.status}
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uuid

app = FastAPI(title="Civic Issue Reporting API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary in-memory storage (will move to PostgreSQL in Phase 2)
issues_db = []

class Issue(BaseModel):
    category: str
    description: str
    latitude: float
    longitude: float
    urgency: str = "medium"

class IssueOut(Issue):
    id: str
    status: str = "Reported"

@app.get("/")
def root():
    return {"status": "ok", "message": "Civic Issue API running"}

@app.post("/issues", response_model=IssueOut)
def create_issue(issue: Issue):
    new_issue = IssueOut(id=str(uuid.uuid4()), **issue.dict())
    issues_db.append(new_issue)
    return new_issue

@app.get("/issues", response_model=List[IssueOut])
def get_issues():
    return issues_db

@app.put("/issues/{issue_id}/resolve", response_model=IssueOut)
def resolve_issue(issue_id: str):
    for issue in issues_db:
        if issue.id == issue_id:
            issue.status = "Resolved"
            return issue
    return {"error": "Issue not found"}
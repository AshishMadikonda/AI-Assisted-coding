
import main

SAMPLE_ISSUE = {
    "category": "sanitation",
    "description": "Blocked drain near the school gate",
    "urgency": "high",
    "latitude": 13.0827,
    "longitude": 80.2707,
}

SAMPLE_PROJECT = {
    "title": "Sample: Main Street resurfacing",
    "department": "Roads and Highways Department",
    "area": "Ward 4",
    "status": "ongoing",
    "start_date": "2026-10-01",
    "expected_end_date": "2026-12-15",
}


def fake_photo():
    # A tiny fake image; the AI is replaced in these tests.
    return {"photo": ("test.jpg", b"not-a-real-image", "image/jpeg")}


# ---------- basics ----------

def test_home_is_running(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_every_category_has_a_department():
    assert set(main.DEPARTMENTS) == set(main.CATEGORIES)


def test_departments_endpoint(client):
    response = client.get("/departments")
    assert response.status_code == 200
    assert response.json()["sanitation"] == "Sanitation Department"


# ---------- issues ----------

def test_create_issue_returns_id_and_department(client):
    response = client.post("/issues", json=SAMPLE_ISSUE)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["status"] == "reported"
    assert data["department"] == "Sanitation Department"


def test_created_issue_can_be_read_back(client):
    issue_id = client.post("/issues", json=SAMPLE_ISSUE).json()["id"]
    response = client.get(f"/issues/{issue_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "sanitation"
    assert data["urgency"] == "high"
    assert data["latitude"] == 13.0827
    assert data["status"] == "reported"
    assert data["department"] == "Sanitation Department"


def test_issue_with_unknown_category_is_rejected(client):
    response = client.post(
        "/issues", json={**SAMPLE_ISSUE, "category": "unknown"}
    )
    assert response.status_code == 400


def test_issue_without_location_is_allowed(client):
    response = client.post("/issues", json={"category": "streetlight"})
    assert response.status_code == 200
    data = client.get(f"/issues/{response.json()['id']}").json()
    assert data["latitude"] is None
    assert data["longitude"] is None


def test_list_issues_shows_newest_first(client):
    client.post("/issues", json=SAMPLE_ISSUE)
    client.post("/issues", json={**SAMPLE_ISSUE, "category": "electricity"})
    issues = client.get("/issues").json()
    assert [i["id"] for i in issues] == [2, 1]
    assert issues[0]["department"] == "Electricity Board"


def test_missing_issue_returns_404(client):
    assert client.get("/issues/999").status_code == 404


def test_status_can_move_to_resolved_with_a_note(client):
    issue_id = client.post("/issues", json=SAMPLE_ISSUE).json()["id"]
    response = client.patch(
        f"/issues/{issue_id}/status",
        json={"status": "resolved", "note": "Drain cleared by the crew"},
    )
    assert response.status_code == 200
    data = client.get(f"/issues/{issue_id}").json()
    assert data["status"] == "resolved"
    assert data["resolution_note"] == "Drain cleared by the crew"


def test_status_change_without_note_keeps_existing_note(client):
    issue_id = client.post("/issues", json=SAMPLE_ISSUE).json()["id"]
    client.patch(
        f"/issues/{issue_id}/status",
        json={"status": "resolved", "note": "Fixed"},
    )
    client.patch(
        f"/issues/{issue_id}/status",
        json={"status": "assigned"},
    )
    data = client.get(f"/issues/{issue_id}").json()
    assert data["status"] == "assigned"
    assert data["resolution_note"] == "Fixed"


def test_invalid_status_is_rejected(client):
    issue_id = client.post("/issues", json=SAMPLE_ISSUE).json()["id"]
    response = client.patch(
        f"/issues/{issue_id}/status",
        json={"status": "finished"},
    )
    assert response.status_code == 400


def test_status_update_on_missing_issue_returns_404(client):
    response = client.patch(
        "/issues/999/status", json={"status": "assigned"}
    )
    assert response.status_code == 404


# ---------- AI classification ----------

def test_classify_returns_the_ai_result(client, monkeypatch):
    fake_result = {
        "category": "road_damage",
        "urgency": "medium",
        "description": "A pothole.",
    }
    monkeypatch.setattr(main, "classify_issue", lambda path: fake_result)
    response = client.post("/classify", files=fake_photo())
    assert response.status_code == 200
    assert response.json() == fake_result


def test_classify_rejects_files_that_are_not_photos(client):
    response = client.post(
        "/classify",
        files={"photo": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400


def test_classify_reports_ai_failure_as_502(client, monkeypatch):
    def broken_ai(path):
        raise RuntimeError("AI is down")

    monkeypatch.setattr(main, "classify_issue", broken_ai)
    response = client.post("/classify", files=fake_photo())
    assert response.status_code == 502


# ---------- projects / transparency board ----------

def test_create_and_list_project(client):
    response = client.post("/projects", json=SAMPLE_PROJECT)
    assert response.status_code == 200
    assert response.json()["status"] == "ongoing"

    projects = client.get("/projects").json()
    assert len(projects) == 1
    assert projects[0]["title"] == "Sample: Main Street resurfacing"
    assert projects[0]["start_date"] == "2026-10-01"


def test_project_with_bad_date_is_rejected(client):
    response = client.post(
        "/projects",
        json={**SAMPLE_PROJECT, "start_date": "01-10-2026"},
    )
    assert response.status_code == 400


def test_project_with_invalid_status_is_rejected(client):
    response = client.post(
        "/projects",
        json={**SAMPLE_PROJECT, "status": "cancelled"},
    )
    assert response.status_code == 400


def test_project_with_empty_title_is_rejected(client):
    response = client.post(
        "/projects", json={**SAMPLE_PROJECT, "title": ""}
    )
    assert response.status_code == 422


def test_projects_can_be_filtered_by_status(client):
    client.post("/projects", json=SAMPLE_PROJECT)
    client.post(
        "/projects",
        json={
            **SAMPLE_PROJECT,
            "title": "Sample: Water tank",
            "status": "planned",
        },
    )
    ongoing = client.get(
        "/projects", params={"status": "ongoing"}
    ).json()
    assert [p["title"] for p in ongoing] == [
        "Sample: Main Street resurfacing"
    ]
    assert client.get(
        "/projects", params={"status": "bogus"}
    ).status_code == 400


def test_project_status_can_be_updated(client):
    project_id = client.post(
        "/projects", json={**SAMPLE_PROJECT, "status": "planned"}
    ).json()["id"]
    response = client.patch(
        f"/projects/{project_id}/status",
        json={"status": "completed"},
    )
    assert response.status_code == 200
    assert client.get("/projects").json()[0]["status"] == "completed"


def test_updating_a_missing_project_returns_404(client):
    response = client.patch(
        "/projects/999/status", json={"status": "ongoing"}
    )
    assert response.status_code == 404

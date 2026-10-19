import pytest

ADMIN_KEY = "test-admin-key"

# Routes only an admin may use: (method, path, json body)
PROTECTED_ROUTES = [
    ("PATCH", "/issues/1/status", {"status": "assigned"}),
    ("POST", "/projects", {"title": "Sample: Water tank"}),
    ("PATCH", "/projects/1/status", {"status": "ongoing"}),
    ("GET", "/admin/check", None),
]


@pytest.mark.parametrize("method,path,body", PROTECTED_ROUTES)
def test_admin_routes_reject_requests_without_a_key(anon_client, method, path, body):
    response = anon_client.request(method, path, json=body)
    assert response.status_code == 401


@pytest.mark.parametrize("method,path,body", PROTECTED_ROUTES)
def test_admin_routes_reject_a_wrong_key(anon_client, method, path, body):
    response = anon_client.request(method, path, json=body, headers={"X-Admin-Key": "wrong-key"})
    assert response.status_code == 401


def test_admin_check_accepts_the_right_key(anon_client):
    response = anon_client.get("/admin/check", headers={"X-Admin-Key": ADMIN_KEY})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_citizen_routes_work_without_a_key(anon_client):
    assert anon_client.get("/").status_code == 200
    assert anon_client.get("/departments").status_code == 200
    created = anon_client.post("/issues", json={"category": "streetlight"})
    assert created.status_code == 200
    assert anon_client.get("/issues").status_code == 200
    assert anon_client.get(f"/issues/{created.json()['id']}").status_code == 200
    assert anon_client.get("/projects").status_code == 200


def test_admin_routes_are_closed_when_no_key_is_configured(anon_client, monkeypatch):
    monkeypatch.delenv("ADMIN_KEY", raising=False)
    response = anon_client.get("/admin/check", headers={"X-Admin-Key": "anything"})
    assert response.status_code == 503


def test_the_right_key_lets_an_admin_change_a_status(anon_client):
    issue_id = anon_client.post("/issues", json={"category": "sanitation"}).json()["id"]
    response = anon_client.patch(
        f"/issues/{issue_id}/status",
        json={"status": "assigned"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert response.status_code == 200
    assert anon_client.get(f"/issues/{issue_id}").json()["status"] == "assigned"


def test_a_rejected_request_does_not_change_anything(anon_client):
    issue_id = anon_client.post("/issues", json={"category": "sanitation"}).json()["id"]
    anon_client.patch(f"/issues/{issue_id}/status", json={"status": "resolved"})
    assert anon_client.get(f"/issues/{issue_id}").json()["status"] == "reported"


def test_browser_preflight_allows_the_admin_key_header(anon_client):
    response = anon_client.options(
        "/projects",
        headers={
            "Origin": "http://localhost:5501",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-admin-key",
        },
    )
    assert response.status_code == 200
    assert "x-admin-key" in response.headers["access-control-allow-headers"].lower()
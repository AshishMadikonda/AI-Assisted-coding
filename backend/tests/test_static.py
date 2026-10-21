def test_citizen_site_is_served(anon_client):
    response = anon_client.get("/citizen/")
    assert response.status_code == 200
    assert "Report a Civic Issue" in response.text


def test_admin_site_is_served(anon_client):
    response = anon_client.get("/admin-ui/")
    assert response.status_code == 200
    assert "Admin Dashboard" in response.text


def test_admin_login_script_is_served(anon_client):
    response = anon_client.get("/admin-ui/auth.js")
    assert response.status_code == 200
    assert "adminFetch" in response.text


def test_api_routes_are_not_hidden_by_the_web_pages(anon_client):
    assert anon_client.get("/").json()["status"] == "ok"
    assert anon_client.get("/admin/check").status_code == 401
    assert anon_client.get("/issues").status_code == 200
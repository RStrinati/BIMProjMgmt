import backend.app as app_module


def test_service_reviews_get_scoped(monkeypatch):
    def fake_assert_service_in_project(project_id, service_id):
        raise app_module.ServiceScopeError("Service not found")

    called = {"get": False}

    def fake_get_service_reviews(service_id):
        called["get"] = True
        return {"reviews": [], "summary": {}}

    monkeypatch.setattr(app_module, "assert_service_in_project", fake_assert_service_in_project)
    monkeypatch.setattr(app_module, "get_service_reviews", fake_get_service_reviews)

    client = app_module.app.test_client()
    response = client.get("/api/projects/1/services/999/reviews")

    assert response.status_code == 404
    assert response.get_json().get("error") == "Service not found"
    assert called["get"] is False


def test_service_reviews_create_scoped(monkeypatch):
    def fake_assert_service_in_project(project_id, service_id):
        raise app_module.ServiceScopeError("Service not found")

    called = {"create": False}

    def fake_create_service_review(*args, **kwargs):
        called["create"] = True
        return 123

    monkeypatch.setattr(app_module, "assert_service_in_project", fake_assert_service_in_project)
    monkeypatch.setattr(app_module, "create_service_review", fake_create_service_review)

    client = app_module.app.test_client()
    response = client.post(
        "/api/projects/1/services/999/reviews",
        json={"cycle_no": 1, "planned_date": "2026-01-01"},
    )

    assert response.status_code == 404
    assert response.get_json().get("error") == "Service not found"
    assert called["create"] is False

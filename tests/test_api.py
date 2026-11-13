import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_and_login(client, email, name="Pavel"):
    response = client.post(
        "/auth/register", json={"email": email, "name": name, "password": "secret123"}
    )
    assert response.status_code == 201
    response = client.post(
        "/auth/login", data={"username": email, "password": "secret123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_and_login(client):
    token = register_and_login(client, "user@example.com")
    assert token


def test_duplicate_email_rejected(client):
    register_and_login(client, "dup@example.com")
    response = client.post(
        "/auth/register",
        json={"email": "dup@example.com", "name": "Pavel", "password": "secret123"},
    )
    assert response.status_code == 409


def test_wrong_password_rejected(client):
    client.post(
        "/auth/register",
        json={"email": "wp@example.com", "name": "Pavel", "password": "secret123"},
    )
    response = client.post(
        "/auth/login", data={"username": "wp@example.com", "password": "wrong"}
    )
    assert response.status_code == 401


def test_tasks_require_auth(client):
    response = client.get("/tasks")
    assert response.status_code in (401, 403)


def test_task_crud_flow(client):
    token = register_and_login(client, "crud@example.com")
    headers = auth(token)

    response = client.post(
        "/tasks",
        json={"title": "Написать отчёт", "description": "Итоговое задание", "theme": "учёба"},
        headers=headers,
    )
    assert response.status_code == 201
    task = response.json()
    assert task["status"] == "new"
    task_id = task["id"]

    response = client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Написать отчёт"

    response = client.patch(
        f"/tasks/{task_id}", json={"title": "Написать отчёт v2"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Написать отчёт v2"

    response = client.patch(
        f"/tasks/{task_id}/status", json={"status": "in_progress"}, headers=headers
    )
    assert response.json()["status"] == "in_progress"

    response = client.delete(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 204

    response = client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 404


def test_task_filters(client):
    token = register_and_login(client, "filter@example.com")
    headers = auth(token)
    client.post(
        "/tasks", json={"title": "A", "theme": "работа"}, headers=headers
    )
    client.post(
        "/tasks", json={"title": "B", "theme": "учёба"}, headers=headers
    )
    response = client.get("/tasks?theme=работа", headers=headers)
    assert len(response.json()) == 1
    response = client.get("/tasks?status=new", headers=headers)
    assert len(response.json()) == 2
    response = client.get("/tasks?status=done", headers=headers)
    assert len(response.json()) == 0


def test_unknown_executor_rejected(client):
    token = register_and_login(client, "executor@example.com")
    response = client.post(
        "/tasks",
        json={"title": "T", "executor_id": 999},
        headers=auth(token),
    )
    assert response.status_code == 422


def test_invalid_status_rejected(client):
    token = register_and_login(client, "status@example.com")
    headers = auth(token)
    task = client.post("/tasks", json={"title": "T"}, headers=headers).json()
    response = client.patch(
        f"/tasks/{task['id']}/status", json={"status": "unknown"}, headers=headers
    )
    assert response.status_code == 422


def test_only_owner_can_edit(client):
    owner_token = register_and_login(client, "owner@example.com")
    other_token = register_and_login(client, "other@example.com")
    task = client.post("/tasks", json={"title": "T"}, headers=auth(owner_token)).json()
    response = client.patch(
        f"/tasks/{task['id']}", json={"title": "Hack"}, headers=auth(other_token)
    )
    assert response.status_code == 403


def test_analytics_summary_and_chart(client):
    token = register_and_login(client, "analytics@example.com")
    headers = auth(token)
    client.post("/tasks", json={"title": "A", "theme": "x"}, headers=headers)
    client.post("/tasks", json={"title": "B", "theme": "x"}, headers=headers)
    task = client.post("/tasks", json={"title": "C", "theme": "y"}, headers=headers).json()
    client.patch(f"/tasks/{task['id']}/status", json={"status": "done"}, headers=headers)

    response = client.get("/analytics/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["by_status"]["new"] == 2
    assert data["by_status"]["done"] == 1
    assert data["by_theme"] == {"x": 2, "y": 1}

    response = client.get("/analytics/status-chart", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_filter_is_parameterized(client):
    token = register_and_login(client, "sqlinj@example.com")
    headers = auth(token)
    client.post("/tasks", json={"title": "Normal"}, headers=headers)
    payload = "' OR '1'='1"
    response = client.get(f"/tasks?theme={payload}", headers=headers)
    assert response.status_code == 200
    assert response.json() == []

import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from shortener_app.models import URL_short

from shortener_app import main, models, schemas, misc
from shortener_app.misc import generate_db_url

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from shortener_app.config import get_settings

from shortener_app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    get_settings().db_url, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)
Base = declarative_base()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def print_test_database_contents():
    db = TestingSessionLocal()

    try:
        urls = db.query(URL_short).all()
        for url in urls:
            print(url.id, url.secret_key, url.key, url.target_url, url.is_active, url.clicks)
    finally:
        db.close()

# Override app dependency with test session
main.app.dependency_overrides[main.get_db] = override_get_db

@pytest.fixture
def client():
    with TestClient(main.app) as test_client:
        yield test_client

def test_create_url(client):
    url_data = {"target_url": "https://www.example.com"}
    response = client.post("/url", json=url_data)
    assert response.status_code == 200
    data = response.json()
    assert data["target_url"] == url_data["target_url"]

def test_forward_to_target_url():
    url_data = {"target_url": "https://www.example.com"}
    create_response = requests.post("http://127.0.0.1:8000/url", json=url_data)
    assert create_response.status_code == 200

    create_response_json = create_response.json()
    assert "key" in create_response_json, "Key not found in response"
    key = create_response_json["key"]

    response = requests.get(f"http://127.0.0.1:8000/{key}", allow_redirects=True)

    print("Response Status Code:", response.status_code)
    print("Response Content:", response.content)

    assert response.status_code == 200 

def test_forward_to_target_url_temp_redirect():
    url_data = {"target_url": "https://www.example.com"}
    create_response = requests.post("http://127.0.0.1:8000/url", json=url_data)
    assert create_response.status_code == 200

    create_response_json = create_response.json()
    assert "key" in create_response_json, "Key not found in response"
    key = create_response_json["key"]

    response = requests.get(f"http://127.0.0.1:8000/{key}", allow_redirects=False)

    print("Response Status Code:", response.status_code)
    print("Response Content:", response.content)

    assert response.status_code == 307 


def test_get_url_info(client):
    url_data = {"target_url": "https://www.example.com"}
    create_response = client.post("/url", json=url_data)
    url_info = create_response.json()
    secret_key = url_info["secret_key"]

    print_test_database_contents()

    response = client.get(f"/admin/{secret_key}")
    assert response.status_code == 200
    data = response.json()
    assert data["target_url"] == url_data["target_url"]

def test_delete_url(client):
    url_data = {"target_url": "https://www.example.com"}
    create_response = client.post("/url", json=url_data)
    url_info = create_response.json()
    secret_key = url_info["secret_key"]

    delete_response = client.delete(f"/admin/{secret_key}")
    assert delete_response.status_code == 200

    response = client.get(f"/admin/{secret_key}")
    assert response.status_code == 404

def test_invalid_url(client):
    url_data = {"target_url": "not_a_valid_url"}
    response = client.post("/url", json=url_data)
    assert response.status_code == 400

def test_nonexistent_url(client):
    response = client.get("/nonexistenturl")
    assert response.status_code == 404

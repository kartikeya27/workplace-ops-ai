import pytest
from fastapi.testclient import TestClient
from workplace_ops.app import create_app

@pytest.fixture
def app_and_db(tmp_path):
    db = tmp_path / 'sample.db'
    return TestClient(create_app(db)), db

@pytest.fixture
def client(app_and_db):
    return app_and_db[0]

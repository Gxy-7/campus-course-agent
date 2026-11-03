import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import api
from app.common.exceptions import (
    BusinessException,
    business_exception_handler,
    global_excpetion_hadler,
    http_excpetion_hadler,
    validation_excpetion_hadler,
)
from app.database import Base, get_db
from app.models.user import User
from app.utils.password import hash_password


# 每个测试使用独立的内存 SQLite，不依赖 MySQL
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    # SQLite 默认不启用外键，测试里手动开启以验证级联删除
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_test_app():
    test_app = FastAPI()
    test_app.include_router(api)
    test_app.add_exception_handler(
        BusinessException, business_exception_handler
    )
    test_app.add_exception_handler(
        StarletteHTTPException, http_excpetion_hadler
    )
    test_app.add_exception_handler(
        RequestValidationError, validation_excpetion_hadler
    )
    test_app.add_exception_handler(Exception, global_excpetion_hadler)
    return test_app


test_app = create_test_app()


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    session.add_all(
        [
            User(
                username="admin",
                password=hash_password("admin"),
                name="管理员",
                role="admin",
                status=1,
            ),
            User(
                username="aaa",
                password=hash_password("123"),
                name="小白",
                role="student",
                status=1,
            ),
            User(
                username="bbb",
                password=hash_password("123"),
                name="小黑",
                role="student",
                status=1,
            ),
        ]
    )
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    test_app.dependency_overrides[get_db] = override_get_db
    with TestClient(test_app, raise_server_exceptions=False) as test_client:
        yield test_client
    test_app.dependency_overrides.clear()


def login(client, username, password):
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body
    return body["data"]["token"]


@pytest.fixture()
def admin_token(client):
    return login(client, "admin", "admin")


@pytest.fixture()
def student_token(client):
    return login(client, "aaa", "123")


@pytest.fixture()
def other_student_token(client):
    return login(client, "bbb", "123")


@pytest.fixture()
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture()
def student_headers(student_token):
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture()
def other_student_headers(other_student_token):
    return {"Authorization": f"Bearer {other_student_token}"}


@pytest.fixture()
def course_factory(client, admin_headers):
    def _create(code="CS101", name="数据结构", status=1):
        response = client.post(
            "/api/course",
            headers=admin_headers,
            json={
                "name": name,
                "code": code,
                "teacher": "张老师",
                "description": "测试课程",
                "status": status,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200, body
        return body["data"]

    return _create


@pytest.fixture()
def schedule_factory(client, admin_headers):
    def _create(
        course_id,
        weekday=1,
        start_section=1,
        end_section=2,
        classroom="A101",
    ):
        response = client.post(
            "/api/schedule",
            headers=admin_headers,
            json={
                "course_id": course_id,
                "weekday": weekday,
                "start_section": start_section,
                "end_section": end_section,
                "start_week": 1,
                "end_week": 16,
                "week_type": 0,
                "classroom": classroom,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200, body
        return body["data"]

    return _create

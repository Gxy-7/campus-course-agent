def test_admin_login_and_me(client, admin_headers):
    response = client.get("/api/user/me", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["role"] == "admin"


def test_wrong_password(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "aaa", "password": "bad"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] != 200
    assert "账号或密码错误" in body["message"]


def test_request_without_token(client):
    response = client.get("/api/user/me")
    assert response.status_code == 401


def test_student_cannot_list_users(client, student_headers):
    response = client.get("/api/user/list", headers=student_headers)
    assert response.status_code == 200
    assert response.json()["code"] == 403


def test_admin_course_crud_and_duplicate_code(
    client, admin_headers, course_factory
):
    course = course_factory()

    duplicate = client.post(
        "/api/course",
        headers=admin_headers,
        json={
            "name": "重复课程",
            "code": "CS101",
            "teacher": "李老师",
            "status": 1,
        },
    )
    body = duplicate.json()
    assert body["code"] != 200
    assert "课程代码已存在" in body["message"]

    updated = client.put(
        f"/api/course/{course['id']}",
        headers=admin_headers,
        json={"name": "数据结构（更新）", "status": 0},
    )
    assert updated.status_code == 200
    assert updated.json()["code"] == 200
    assert updated.json()["data"]["status"] == 0

    deleted = client.delete(
        f"/api/course/{course['id']}", headers=admin_headers
    )
    assert deleted.status_code == 200
    assert deleted.json()["code"] == 200


def test_student_course_list_only_active(
    client, admin_headers, student_headers, course_factory
):
    active = course_factory(code="CS201", name="操作系统", status=1)
    course_factory(code="CS202", name="停用课程", status=0)

    admin_list = client.get(
        "/api/course/list?page=1&page_size=20", headers=admin_headers
    )
    assert admin_list.json()["data"]["total"] == 2

    student_list = client.get(
        "/api/course/list?page=1&page_size=20", headers=student_headers
    )
    body = student_list.json()
    assert body["code"] == 200
    assert body["data"]["total"] == 1
    assert body["data"]["list"][0]["id"] == active["id"]


def test_student_cannot_create_course(client, student_headers):
    response = client.post(
        "/api/course",
        headers=student_headers,
        json={
            "name": "越权课程",
            "code": "CS999",
            "teacher": "老师",
            "status": 1,
        },
    )
    assert response.status_code == 200
    assert response.json()["code"] == 403

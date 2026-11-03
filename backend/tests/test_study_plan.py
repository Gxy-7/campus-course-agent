def create_plan(client, headers, title="期末复习计划"):
    response = client.post(
        "/api/study-plan",
        headers=headers,
        json={
            "title": title,
            "goal": "复习课程内容",
            "start_date": "2026-11-01",
            "end_date": "2026-11-20",
            "status": 0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body
    return body["data"]


def test_study_plan_crud_and_ownership(
    client,
    admin_headers,
    student_headers,
    other_student_headers,
):
    plan = create_plan(client, student_headers)

    listed = client.get("/api/study-plan/list", headers=student_headers)
    assert listed.json()["code"] == 200
    assert listed.json()["data"][0]["id"] == plan["id"]

    admin_list = client.get(
        "/api/study-plan/list", headers=admin_headers
    )
    assert admin_list.json()["code"] == 403

    other_update = client.put(
        f"/api/study-plan/{plan['id']}",
        headers=other_student_headers,
        json={
            "title": "越权修改",
            "goal": "",
            "start_date": "2026-11-01",
            "end_date": "2026-11-20",
            "status": 0,
        },
    )
    assert other_update.json()["code"] != 200

    updated = client.put(
        f"/api/study-plan/{plan['id']}",
        headers=student_headers,
        json={
            "title": "期末复习计划（已更新）",
            "goal": "更新后的目标",
            "start_date": "2026-11-02",
            "end_date": "2026-11-18",
            "status": 1,
        },
    )
    assert updated.json()["data"]["status"] == 1

    deleted = client.delete(
        f"/api/study-plan/{plan['id']}", headers=student_headers
    )
    assert deleted.json()["code"] == 200


def test_study_plan_invalid_dates(client, student_headers):
    response = client.post(
        "/api/study-plan",
        headers=student_headers,
        json={
            "title": "日期错误",
            "goal": "",
            "start_date": "2026-11-20",
            "end_date": "2026-11-01",
            "status": 0,
        },
    )
    assert response.status_code == 422

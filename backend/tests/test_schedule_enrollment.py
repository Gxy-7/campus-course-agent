def test_student_can_enroll_and_query_my_schedule(
    client, student_headers, course_factory, schedule_factory
):
    course = course_factory()
    schedule_factory(course["id"])

    enrolled = client.post(
        f"/api/enrollment/{course['id']}", headers=student_headers
    )
    assert enrolled.json()["code"] == 200

    my_schedule = client.get("/api/schedule/my", headers=student_headers)
    assert my_schedule.status_code == 200
    body = my_schedule.json()
    assert body["code"] == 200
    assert len(body["data"]) == 1
    assert body["data"][0]["course_code"] == "CS101"


def test_enrollment_conflict_is_blocked(
    client, student_headers, course_factory, schedule_factory
):
    course_a = course_factory(code="CS301", name="课程A")
    course_b = course_factory(code="CS302", name="课程B")
    schedule_factory(course_a["id"])
    schedule_factory(course_b["id"])

    first = client.post(
        f"/api/enrollment/{course_a['id']}", headers=student_headers
    )
    assert first.json()["code"] == 200

    conflict = client.post(
        f"/api/enrollment/{course_b['id']}", headers=student_headers
    )
    assert conflict.status_code == 200
    assert conflict.json()["code"] != 200
    assert "时间冲突" in conflict.json()["message"]


def test_student_cannot_create_schedule(
    client, student_headers, course_factory
):
    course = course_factory()
    response = client.post(
        "/api/schedule",
        headers=student_headers,
        json={
            "course_id": course["id"],
            "weekday": 1,
            "start_section": 1,
            "end_section": 2,
            "start_week": 1,
            "end_week": 16,
            "week_type": 0,
            "classroom": "A101",
        },
    )
    assert response.status_code == 200
    assert response.json()["code"] == 403

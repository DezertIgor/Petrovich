from __future__ import annotations

from typing import Any

import allure
from pytest_check import check

from src import test_data
from src.api_client import Api, ExpectedCondition

pytestmark = [
    allure.suite("Студенты"),
]


def _contains_student(students: Any, expected_student: dict[str, Any]) -> bool:
    """Проверить наличие студента с ожидаемыми данными в списке."""
    if not isinstance(students, list):
        return False
    return any(
        isinstance(student, dict) and all(student.get(key) == value for key, value in expected_student.items())
        for student in students
    )


@allure.title("Управление данными студента")
def test_student_crud(api_client: Api) -> None:
    create_student_data = {
        "name": test_data.student_name,
        "email": test_data.student_email,
        "phone_no": test_data.student_phone_no,
        "gender": test_data.student_gender,
        "status": test_data.student_status,
    }
    update_student_data = {
        "name": test_data.updated_student_name,
        "email": test_data.updated_student_email,
        "gender": test_data.updated_student_gender,
        "status": test_data.updated_student_status,
    }
    with allure.step("Создание нового студента"):
        create_response = api_client.request(
            method="POST",
            url=".",
            expected_body={
                "status": 1,
                "message": "Student created successfully",
                "student": {
                    "id": ExpectedCondition(
                        description="Целое число больше 0",
                        predicate=lambda value: type(value) is int and value > 0,
                    ),
                    **create_student_data,
                },
            },
            json=create_student_data,
        )
        student_id = create_response.json()["student"]["id"]

    created_student = {"id": student_id, **create_student_data}

    with check:
        with allure.step("Получение списка студентов"):
            api_client.request(
                url=".",
                expected_body={
                    "status": 1,
                    "students": ExpectedCondition(
                        description=[created_student],
                        predicate=lambda students: _contains_student(students, created_student),
                    ),
                },
            )

    with check:
        with allure.step("Получение студента по ID"):
            api_client.request(
                url=str(student_id),
                expected_body={
                    "status": 1,
                    "student": created_student,
                },
            )

    updated_student = {
        "id": student_id,
        **update_student_data,
        "phone_no": test_data.student_phone_no,
    }

    with check:
        with allure.step("Обновление данных студента"):
            api_client.request(
                method="PUT",
                url=str(student_id),
                expected_body={
                    "status": 1,
                    "message": "Student updated successfully",
                    "student": updated_student,
                },
                json=update_student_data,
            )

    with allure.step("Удаление студента"):
        api_client.request(
            method="DELETE",
            url=str(student_id),
            expected_body={
                "status": 1,
                "message": "Student deleted successfully",
            },
        )

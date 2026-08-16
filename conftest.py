from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

import allure
import pytest

from src.api_client import Api

PROJECT_ROOT = Path(__file__).resolve().parent
ALLURE_RESULTS_DIR = PROJECT_ROOT / "artifacts" / "allure-results"
ALLURE_REPORT_DIR = PROJECT_ROOT / "artifacts" / "allure-report"


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Убрать родительский раздел Allure для всех тестов."""
    for item in items:
        item.add_marker(allure.parent_suite(""), append=False)


@pytest.fixture
def api_client() -> Iterator[Api]:
    """Создание API-клиента для теста и закрытие его после завершения."""
    base_url = os.getenv("API_URL")
    if not base_url:
        pytest.fail("Переменная API_URL отсутствует в окружении")

    client = Api(base_url=base_url)
    yield client
    client.close()


def _patch_allure_results() -> list[Path]:
    """Поправить отображение тестов в raw Allure results."""
    result_files = list(ALLURE_RESULTS_DIR.glob("*-result.json"))
    for result_file in result_files:
        result = json.loads(result_file.read_text(encoding="utf-8"))

        def mark_parent_steps_failed(steps: list[dict[str, object]]) -> None:
            for step in steps:
                child_steps = step.get("steps", [])
                if isinstance(child_steps, list):
                    mark_parent_steps_failed(child_steps)
                    if any(child.get("status") in {"failed", "broken"} for child in child_steps):
                        step["status"] = "failed"
                        step.pop("statusDetails", None)

        steps = result.get("steps", [])
        if isinstance(steps, list):
            mark_parent_steps_failed(steps)

        if any(step.get("status") in {"failed", "broken"} for step in steps):
            result.pop("statusDetails", None)

        result["labels"] = [
            label
            for label in result.get("labels", [])
            if not (label.get("name") == "parentSuite" and not label.get("value"))
        ]
        result["attachments"] = [
            attachment for attachment in result.get("attachments", []) if attachment.get("name") != "stdout"
        ]
        result_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")

    for container_file in ALLURE_RESULTS_DIR.glob("*-container.json"):
        container = json.loads(container_file.read_text(encoding="utf-8"))
        container["afters"] = [
            finalizer for finalizer in container.get("afters", []) if finalizer.get("status") in {"failed", "broken"}
        ]
        container_file.write_text(json.dumps(container, ensure_ascii=False), encoding="utf-8")

    return result_files


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Сгенерировать и открыть локальный Allure-отчёт."""
    del exitstatus

    if session.config.option.collectonly:
        return
    result_files = _patch_allure_results()
    if not result_files:
        return

    subprocess.run(
        [
            "allure",
            "generate",
            str(ALLURE_RESULTS_DIR),
            "--clean",
            "--lang",
            "ru",
            "-o",
            str(ALLURE_REPORT_DIR),
        ],
        check=True,
    )
    subprocess.Popen(
        ["allure", "open", str(ALLURE_REPORT_DIR)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

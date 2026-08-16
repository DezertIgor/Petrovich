from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import allure
import httpx
from pytest_check import check

MAX_RESPONSE_TIME_SECONDS = 3.0
MAX_RESPONSE_SIZE_KB = 501.0


@dataclass(frozen=True)
class ExpectedCondition:
    """Условие проверки и его информативное представление в Allure."""

    description: Any
    predicate: Callable[[Any], bool]


def _prepare_expected_value(expected_value: Any) -> Any:
    """Подготовить ожидаемое значение для JSON-вложения Allure."""
    if isinstance(expected_value, ExpectedCondition):
        return _prepare_expected_value(expected_value.description)
    if callable(expected_value):
        raise TypeError("Для проверки по условию используйте ExpectedCondition с информативным описанием")
    if isinstance(expected_value, dict):
        return {key: _prepare_expected_value(value) for key, value in expected_value.items()}
    if isinstance(expected_value, list):
        return [_prepare_expected_value(value) for value in expected_value]
    return expected_value


def _format_response_info(metadata: dict[str, Any], body: dict[str, Any]) -> str:
    """Сформировать JSON с одной пустой строкой между метаданными и телом."""
    return (
        "{\n"
        + ",\n\n".join(
            json.dumps(section, ensure_ascii=False, indent=2).split("\n", maxsplit=1)[1].rsplit("\n", maxsplit=1)[0]
            for section in (metadata, body)
        )
        + "\n}"
    )


def _assert_expected_value(actual_value: Any, expected_value: Any) -> None:
    """Рекурсивная проверка ожидаемых полей и значений."""
    if isinstance(expected_value, ExpectedCondition):
        assert expected_value.predicate(actual_value)
    elif callable(expected_value):
        raise TypeError("Для проверки по условию используйте ExpectedCondition с информативным описанием")
    elif isinstance(expected_value, dict):
        assert isinstance(actual_value, dict)
        for key, nested_expected_value in expected_value.items():
            assert key in actual_value
            _assert_expected_value(actual_value[key], nested_expected_value)
    else:
        assert actual_value == expected_value


class Api:
    """Класс для методов взаимодействия с API."""

    def __init__(self, base_url: str) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=61.0)

    def request(
        self,
        url: str,
        expected_body: dict[str, Any],
        method: str = "GET",
        expected_status_code: int = 200,
        expected_response_time_seconds: float = MAX_RESPONSE_TIME_SECONDS,
        expected_response_size_kb: float = MAX_RESPONSE_SIZE_KB,
        **kwargs: Any,
    ) -> httpx.Response:
        """Отправить запрос и проверить статус-код, время и ожидаемые поля тела ответа.

        :param url: Относительный путь API, который добавляется к базовому URL клиента.
        :param expected_body: Ожидаемые поля и значения в JSON-теле ответа.
        :param method: HTTP-метод запроса. По умолчанию ``GET``.
        :param expected_status_code: Ожидаемый статус-код. По умолчанию ``200``.
        :param expected_response_time_seconds: Максимальное допустимое время ответа в секундах.
        :param expected_response_size_kb: Максимальный допустимый размер ответа в килобайтах.
        :param kwargs: Дополнительные именованные аргументы для ``httpx.Client.request``, например ``data``,
            ``json``, ``params`` или ``headers``.
        :return: Полученный объект ``httpx.Response``.
        """
        response = self._client.request(method, url, **kwargs)
        request = response.request

        request_body: Any = None
        if request.content:
            request_body = request.content.decode("utf-8", errors="replace")

        try:
            response_body = response.json()
        except json.JSONDecodeError:
            response_body = response.text

        if isinstance(response_body, dict):
            response_body_info = response_body
        else:
            response_body_info = {"response": response_body}

        response_metadata = {
            "status_code": response.status_code,
            "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
            "response_size_kb": round(len(response.content) / 1024, 2),
        }
        expected_response_info = json.dumps(
            _prepare_expected_value(expected_body),
            ensure_ascii=False,
            indent=2,
        )
        actual_response_info = _format_response_info(response_metadata, response_body_info)

        allure.attach(
            json.dumps(
                {
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "body": request_body,
                },
                ensure_ascii=False,
                indent=2,
            ),
            "Запрос",
            allure.attachment_type.JSON,
        )
        allure.attach(
            expected_response_info,
            "Ожидаемый ответ",
            allure.attachment_type.JSON,
        )
        allure.attach(
            actual_response_info,
            "Фактический ответ",
            allure.attachment_type.JSON,
        )

        with allure.step(f"Статус-код: {expected_status_code}"):
            assert response.status_code == expected_status_code

        response_time_seconds = response.elapsed.total_seconds()
        with check:
            with allure.step(f"Время ответа менее {expected_response_time_seconds:g} с"):
                assert response_time_seconds <= expected_response_time_seconds

        response_size_kb = len(response.content) / 1024
        with check:
            with allure.step(f"Размер ответа менее {expected_response_size_kb:g} Кб"):
                assert response_size_kb < expected_response_size_kb

        with allure.step("Тело ответа"):
            assert isinstance(response_body, dict)
            for key, expected_value in expected_body.items():
                assert key in response_body
                _assert_expected_value(response_body[key], expected_value)

        return response

    def close(self) -> None:
        """Закрытие HTTP-соединения клиента."""
        self._client.close()

from __future__ import annotations

import json
from typing import Any

import allure
import httpx
from pytest_check import check

MAX_RESPONSE_TIME_SECONDS = 3.0
MAX_RESPONSE_SIZE_KB = 501.0


def _assert_expected_value(actual_value: Any, expected_value: Any) -> None:
    """Рекурсивная проверка ожидаемых полей и значений."""
    if callable(expected_value):
        assert expected_value(actual_value)
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

        response_headers_info = {}
        for header_name in ("id", "Server-Timing", "traceparent"):
            header_value = response.headers.get(header_name)
            response_headers_info[header_name] = "Поле не найдено" if header_value is None else header_value

        response_sections = [response_metadata, response_headers_info]
        if response_body_info:
            response_sections.append(response_body_info)
        response_info = (
            "{\n"
            + ",\n\n".join(
                json.dumps(section, ensure_ascii=False, indent=2).split("\n", maxsplit=1)[1].rsplit("\n", maxsplit=1)[0]
                for section in response_sections
            )
            + "\n}"
        )

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
            response_info,
            "Ответ",
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

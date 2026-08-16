# Петрович Тех

API-автотесты методов работы со студентами.

## Что необходимо установить

- Python 3.13;
- Java и [Allure Commandline](https://allurereport.org/docs/install/);
- зависимости проекта из `requirements.txt`.

Подготовка окружения:

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Запуск автотестов

```bash
API_URL=http://93.77.188.34/student .venv/bin/pytest
```

После выполнения тестов Allure-отчёт генерируется и открывается автоматически.

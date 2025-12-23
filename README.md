# Система учёта продаж магазина бытовой техники — Starter

Учебный проект на **FastAPI** для лабораторной работы.  
Реализован учёт товаров, клиентов и продаж, а также полный цикл тестирования:
unit, BDD, GUI и нагрузочное.

---

## Функциональные возможности

- **Товары**
  - добавление, редактирование, удаление
  - поиск по названию, артикулу и категории
- **Продажи**
  - оформление продажи
  - автоматический расчёт `total_amount`
  - фильтрация по диапазону дат
- **GUI**
  - простой веб-интерфейс (HTML / CSS / JavaScript)
- **Тестирование**
  - unit-тесты
  - BDD-сценарии
  - GUI-тесты 
  - нагрузочное тестирование

---

## Быстрый старт

### 1) Создание виртуального окружения

**Windows (PowerShell):**

python -m venv .venv
.venv\Scripts\Activate.ps1



Linux / macOS:

python3 -m venv .venv
source .venv/bin/activate

2. Установка зависимостей
pip install -r requirements.txt

3. Инициализация базы данных и демо-данных

Создаст файл sales.db и заполнит его начальными данными.

python -m app.seed

4. Запуск API
uvicorn app.main:app --reload


После запуска:

Swagger UI:
http://127.0.0.1:8000/

Статический интерфейс:
http://127.0.0.1:8000/static/index.html

(порт может отличаться — см. вывод Uvicorn running on ...)

Структура проекта
app/
  main.py            # Точка входа FastAPI
  database.py        # Подключение к SQLite
  models.py          # SQLAlchemy модели
  schemas.py         # Pydantic схемы
  crud.py            # Логика работы с БД
  seed.py            # Инициализация БД
  routers/
    products.py
    sales.py
  static/
    index.html
    style.css
    script.js

tests/
  test_smoke.py      # Unit / smoke тесты
  bdd/               # BDD тесты (pytest-bdd)
  ui/                # GUI static тесты 
  load/              # Нагрузочные тесты (Locust)


Тестирование
1. Unit / интеграционные тесты

Используется pytest.

pytest

2. BDD-тестирование (поведенческое)

Используется pytest-bdd.
Проверяются сценарии из .feature файлов:

создание товаров

ошибки дубликатов

оформление продаж

обработка невалидных данных

pytest tests/bdd

3. GUI-тестирование 

Проверяется:

наличие элементов интерфейса

корректные id

привязка кнопок к обработчикам

наличие addEventListener

тестируется статическая связка HTML + JS.

pytest tests/ui

4. Нагрузочное тестирование

Используется Locust.

Запуск:

locust -f tests/load/locustfile.py


После запуска открыть:

http://localhost:8089


Проверяются:

/api/products

/api/customers

/api/sales

Доступны метрики:

Summary

Requests per second

Response time

Ошибки по эндпоинтам

Инструменты тестирования 

5.2. Инструменты тестирования

Юнит-тесты: pytest

BDD-тестирование: pytest-bdd

GUI-тестирование: статический анализ HTML/JS


Нагрузочное тестирование: Locust
(возможные альтернативы: k6, Apache JMeter)

Полезные Git-команды
git init
git add .
git commit -m "feat: initial scaffold for appliance store sales system"

# Ветки
git checkout -b dev
git checkout -b student

# Слияния
git checkout dev
git merge student
git checkout master
git merge dev

# Публикация
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin --all

Итог

Проект демонстрирует полный цикл разработки учебного API-приложения:
от проектирования структуры и API до автоматического тестирования и нагрузочной проверки.
Система готова к защите, расширению и дальнейшему развитию.

Идеи для развития

Авторизация и роли (JWT)

Отчёты по продажам

Аналитика (средний чек, ABC/XYZ)

Скидки и акции

Экспорт в CSV / Excel
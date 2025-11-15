# Система учёта продаж магазина бытовой техники — Starter

Минимальный FastAPI‑проект для ЛР №3: выбор платформы, декомпозиция и Git.

## Быстрый старт

```bash
# 1) Создать и активировать виртуальное окружение (Windows PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux/macOS:
python3 -m venv .venv
source .venv/bin/activate

# 2) Установить зависимости
pip install -r requirements.txt

# 3) Инициализировать БД и демо‑данные (создаст файл sales.db)
python -m app.seed

# 4) Запустить API
uvicorn app.main:app --reload
```

Откройте Swagger UI: http://127.0.0.1:8000/

## Структура

```
app/
  main.py            # Точки входа и маршруты
  database.py        # Подключение к SQLite и базовые сущности ORM
  models.py          # SQLAlchemy‑модели
  schemas.py         # Pydantic‑схемы
  crud.py            # Операции с БД
  seed.py            # Инициализация/демо‑данные
  routers/
    products.py
    sales.py
tests/
  test_smoke.py      # Мини‑проверка, что приложение стартует
```

## Полезные команды Git (кратко)

```bash
git init
git add .
git commit -m "feat: initial scaffold for appliance store sales system"

# Ветки по учебному флоу:
git checkout -b dev
git checkout -b student

# Слияния:
git checkout dev
git merge student
git checkout master
git merge dev

# Подключение и отправка на GitHub:
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin --all
```

## Заметки по дальнейшему развитию

- Добавить авторизацию (JWT), роли (кассир/менеджер).
- Отчёты: продажи по дням/категориям/товарам, средний чек, ABC/XYZ‑анализ.
- Инвентаризация/остатки, возвраты, скидки/акции.
- Экспорт в CSV/Excel.

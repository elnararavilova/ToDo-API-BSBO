# ToDo API — матрица Эйзенхауэра

Проект представляет собой **REST API для управления задачами** с автоматической классификацией по **матрице Эйзенхауэра (Q1–Q4)** и **Telegram-бот** в роли пользовательского интерфейса для работы с API.

- **API**: FastAPI + PostgreSQL (Supabase) + SQLAlchemy Async  
- **UI**: Telegram Bot (aiogram)  
- **Логика матрицы**: срочность вычисляется по дедлайну, квадрант определяется автоматически на основе важности и срочности.

---

## Возможности

### API
- Регистрация и вход (JWT)
- CRUD задач (создание / просмотр / обновление / удаление)
- Автоматическое вычисление:
  - `is_urgent` (срочность)
  - `quadrant` (Q1–Q4)
  - `days_until_deadline` (сколько дней до дедлайна)
- Поиск, фильтры, задачи на сегодня
- Статистика по задачам
- Роли пользователей (user/admin)

### Telegram Bot (UI)
- Регистрация / вход прямо в Telegram
- Просмотр списка задач + inline-кнопки:
  - ✅ выполнить
  - 🗑 удалить
  - ✏️ редактировать
- Создание задач пошаговым диалогом
- Статистика и задачи на сегодня
- Поиск по задачам

---

## Технологии

- FastAPI
- PostgreSQL (Supabase)
- SQLAlchemy (async)
- APScheduler
- aiogram
- httpx
- python-dotenv

---

## Архитектура

- API отвечает за бизнес-логику, БД и авторизацию
- Telegram-бот является клиентом и работает через HTTP-запросы
- JWT используется для авторизации пользователя

---

## Эндпоинты API (v3)

Базовый префикс: `/api/v3`

### Основные
- `GET /`
- `GET /health`

### Авторизация (`/auth`)
- `POST /auth/register`
- `POST /auth/login`
- `PATCH /auth/change-password`
- `GET /auth/me`

### Задачи (`/tasks`)
- `GET /tasks`
- `GET /tasks/{task_id}`
- `GET /tasks/quadrant/{quadrant}`
- `GET /tasks/status/{status}`
- `GET /tasks/search?q=`
- `POST /tasks`
- `PUT /tasks/{task_id}`
- `PATCH /tasks/{task_id}/complete`
- `DELETE /tasks/{task_id}`

### Статистика (`/stats`)
- `GET /stats`
- `GET /stats/timing`
- `GET /stats/today`

---

## Установка и запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Переменные окружения (.env)
```env
DATABASE_URL=postgresql+asyncpg://postgres:<password>@db.<project>.supabase.co:5432/postgres?sslmode=require
SECRET_KEY=your_secret_key
BOT_TOKEN=telegram_bot_token
API_BASE_URL=http://127.0.0.1:8000
```

### 3. Запуск API и Telegram bot
```bash
uvicorn main:app
```

Документация:
- `/docs`
- `/redoc`

## Автор

Равилова Эльнара Надировна

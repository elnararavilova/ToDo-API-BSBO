# ToDo API — матрица Эйзенхауэра

- REST API для управления задачами с классификацией по матрице Эйзенхауэра.

## Технологии
- FastAPI  
- Python  
- PostgreSQL (Supabase)  
- SQLAlchemy (async)
- APScheduler (планировщик фоновых задач)

## Эндпоинты

### Основные
- `GET /` — информация о приложении  
- `GET /health` — состояние API и БД

### Авторизация (`/api/v2/auth`)
- `POST /auth/register` — регистрация пользователя
- `POST /auth/login` — вход (JWT токен)
- `PATCH /auth/change-password` — смена пароля 
- `GET /auth/me` — текущий пользователь

### Администрирование (`/api/v2/auth/admin`)
- `GET /admin/users` — список всех пользователей с количеством их задач (только для админа)

### Задачи (`/api/v2/tasks`)
- `GET /tasks` — список задач  
- `GET /tasks/{task_id}` — задача по ID  
- `GET /tasks/quadrant/{quadrant}` — фильтр по Q1–Q4  
- `GET /tasks/status/{status}` — completed / pending  
- `GET /tasks/search?q=` — поиск
- `GET /tasks/today` — задачи, срок которых истекает сегодня 
- `POST /tasks` — создание (передаются важность и дедлайн, срочность и квадрант считаются автоматически)
- `PUT /tasks/{task_id}` — обновление (при изменении важности или дедлайна пересчитываются срочность и квадрант) 
- `PATCH /tasks/{task_id}/complete` — отметить выполненной  
- `DELETE /tasks/{task_id}` — удалить  

### Статистика (`/api/v2/stats`)
- `GET /stats` — общее количество, по квадрантам и по статусам
- `GET /stats/deadlines` — невыполненные задачи с дедлайнами и количеством дней до дедлайна
- `GET /stats/timing` — агрегированная статистика по срокам (вовремя / с опозданием / в работе / просрочены)


## Запуск проекта

1. Установить зависимости:
pip install -r requirements.txt

### 2. Создать файл `.env`:
DATABASE_URL=postgresql+asyncpg://postgres:<password>@db.<project>.supabase.co:5432/postgres?sslmode=require
SECRET_KEY = 'ваш_ключ'

### 3. Запустить сервер:
uvicorn main:app --reload

### 4. Документация:
- Swagger UI → `/docs`  
- ReDoc → `/redoc`

## Автор
Равилова Эльнара Надировна

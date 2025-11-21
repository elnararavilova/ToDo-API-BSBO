# ToDo API — матрица Эйзенхауэра

- REST API для управления задачами с классификацией по матрице Эйзенхауэра.

## Технологии
- FastAPI  
- Python  
- PostgreSQL (Supabase)  
- SQLAlchemy (async)

## Эндпоинты

### Основные
- `GET /` — информация о приложении  
- `GET /health` — состояние API и БД  

### Задачи (`/api/v2/tasks`)
- `GET /tasks` — список задач  
- `GET /tasks/{task_id}` — задача по ID  
- `GET /tasks/quadrant/{quadrant}` — фильтр по Q1–Q4  
- `GET /tasks/status/{status}` — completed / pending  
- `GET /tasks/search?q=` — поиск  
- `POST /tasks` — создание  
- `PUT /tasks/{task_id}` — обновление  
- `PATCH /tasks/{task_id}/complete` — отметить выполненной  
- `DELETE /tasks/{task_id}` — удалить  

### Статистика (`/api/v2/stats`)
- `GET /stats` — общее количество, по квадрантам и по статусам

## Запуск проекта

1. Установить зависимости:
pip install -r requirements.txt

### 2. Создать файл `.env`:
DATABASE_URL=postgresql+asyncpg://postgres:<password>@db.<project>.supabase.co:5432/postgres?sslmode=require

### 3. Запустить сервер:
uvicorn main:app --reload

### 4. Документация:
- Swagger UI → `/docs`  
- ReDoc → `/redoc`

## Автор
Равилова Эльнара Надировна

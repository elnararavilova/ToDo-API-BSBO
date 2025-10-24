# Главный файл приложения
from fastapi import FastAPI, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime

app = FastAPI(
    title="ToDo лист API",
    description="API для управления задачами с использованием матрицы Эйзенхауэра",
    version="1.0.0",
    contact = {"name": "Равилова Эльнара Надировна"}
)

# Временное хранилище (позже будет заменено на PostgreSQL)
tasks_db: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Сдать проект по FastAPI",
        "description": "Завершить разработку API и написать документацию",
        "is_important": True,
        "is_urgent": True,
        "quadrant": "Q1",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "title": "Изучить SQLAlchemy",
        "description": "Прочитать документацию и попробовать примеры",
        "is_important": True,
        "is_urgent": False,
        "quadrant": "Q2",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 3,
        "title": "Сходить на лекцию",
        "description": None,
        "is_important": False,
        "is_urgent": True,
        "quadrant": "Q3",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 4,
        "title": "Посмотреть сериал",
        "description": "Новый сезон любимого сериала",
        "is_important": False,
        "is_urgent": False,
        "quadrant": "Q4",
        "completed": True,
        "created_at": datetime.now()
    },
]



@app.get("/")
async def welcome() -> dict:
    app_info = {
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "contact": app.contact,
    }
    return {"message": "Привет, студент!", "app_info": app_info}



@app.get("/tasks")
async def get_all_tasks() -> dict:
    return {
        "count": len(tasks_db), # считает количество записей в хранилище
        "tasks": tasks_db # выводит всё, чта есть в хранилище
    }

@app.get("/tasks/quadrant/{quadrant}")
async def get_tasks_by_quadrant(quadrant: str) -> dict:
    if quadrant not in ["Q1", "Q2", "Q3", "Q4"]:
        raise HTTPException( #специальный класс в FastAPI для возврата HTTP ошибок. Не забудьте добавть его вызов в 1 строке
            status_code=400,
            detail="Неверный квадрант. Используйте: Q1, Q2, Q3, Q4" #текст, который будет выведен пользователю
        )
    
    filtered_tasks = [
        task # ЧТО добавляем в список
        for task in tasks_db # ОТКУДА берем элементы
        if task["quadrant"] == quadrant # УСЛОВИЕ фильтрации
    ]
    
    return {
        "quadrant": quadrant,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }


@app.get("/tasks/stats")
async def get_tasks_stats() -> dict:
    # Общее количество задач
    total_tasks = len(tasks_db)
    
    # Количество задач по квадрантам
    by_quadrant = {
        "Q1": len([task for task in tasks_db if task["quadrant"] == "Q1"]),
        "Q2": len([task for task in tasks_db if task["quadrant"] == "Q2"]),
        "Q3": len([task for task in tasks_db if task["quadrant"] == "Q3"]),
        "Q4": len([task for task in tasks_db if task["quadrant"] == "Q4"])
    }
    
    # Количество задач по статусу выполнения
    completed_tasks = len([task for task in tasks_db if task["completed"]])
    pending_tasks = len([task for task in tasks_db if not task["completed"]])
    
    by_status = {
        "completed": completed_tasks,
        "pending": pending_tasks
    }
    
    return {
        "total_tasks": total_tasks,
        "by_quadrant": by_quadrant,
        "by_status": by_status
    }


@app.get("/tasks/search")
async def search_tasks(q: str = "") -> dict:
    # Проверяем длину ключевого слова
    if len(q) < 2:
        raise HTTPException(
            status_code=400,
            detail="Ключевое слово должно содержать минимум 2 символа"
        )
    
    # Приводим к нижнему регистру для регистронезависимого поиска
    query_lower = q.lower()
    
    # Ищем задачи по названию или описанию
    filtered_tasks = [
        task
        for task in tasks_db
        if (task["title"] and query_lower in task["title"].lower()) or 
           (task["description"] and query_lower in task["description"].lower())
    ]
    
    return {
        "query": q,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }


@app.get("/tasks/{task_id}")
async def get_task_by_id(task_id: int) -> dict:
    # Ищем задачу по ID
    task = next((task for task in tasks_db if task["id"] == task_id), None)
    
    # Если задача не найдена, возвращаем ошибку 404
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с ID {task_id} не найдена"
        )
    
    # Возвращаем найденную задачу
    return {"task": task}


@app.get("/tasks/status/{status}")
async def get_tasks_by_status(status: str) -> dict:
    # Проверяем валидность статуса
    if status not in ["completed", "pending"]:
        raise HTTPException(
            status_code=400,  # или status.HTTP_400_BAD_REQUEST
            detail="Неверный статус. Используйте: 'completed' или 'pending'"
        )
    
    # Определяем булево значение для фильтрации
    is_completed = (status == "completed")
    
    # Фильтруем задачи по статусу
    filtered_tasks = [
        task
        for task in tasks_db
        if task["completed"] == is_completed
    ]
    
    return {
        "status": status,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }

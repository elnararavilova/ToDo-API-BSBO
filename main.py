# Главный файл приложения
from fastapi import FastAPI
from routers import tasks

app = FastAPI(
    title="ToDo лист API",
    description="API для управления задачами с использованием матрицы Эйзенхауэра",
    version="1.0.0",
    contact = {"name": "Равилова Эльнара Надировна"}
)

app.include_router(tasks.router) # подключение роутера к приложению

@app.get("/")
async def welcome() -> dict:
    app_info = {
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "contact": app.contact,
    }
    return {"message": "Привет, студент!", "app_info": app_info}

@app.post("/tasks")
async def create_task(task: dict):
    return {"message": "Запись успешно создана!", "task": task}
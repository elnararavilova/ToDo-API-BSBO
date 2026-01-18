import os
import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

import httpx
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


# =========================
# Config
# =========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is empty. Put it into .env")

API_PREFIX = "/api/v3"  # у тебя роутеры подключены с prefix="/api/v3"

# Простое in-memory хранилище токенов: tg_user_id -> token
TOKENS: Dict[int, str] = {}


# =========================
# Helpers (API)
# =========================
@dataclass
class ApiClient:
    base_url: str

    def _headers(self, token: Optional[str]) -> Dict[str, str]:
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    async def register(self, nickname: str, email: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}{API_PREFIX}/auth/register"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, json={"nickname": nickname, "email": email, "password": password})
            r.raise_for_status()
            return r.json()

    async def login(self, email: str, password: str) -> str:
        # login ждёт OAuth2PasswordRequestForm => form-data: username, password
        url = f"{self.base_url}{API_PREFIX}/auth/login"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, data={"username": email, "password": password})
            r.raise_for_status()
            data = r.json()
            return data["access_token"]

    async def me(self, token: str) -> Dict[str, Any]:
        url = f"{self.base_url}{API_PREFIX}/auth/me"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=self._headers(token))
            r.raise_for_status()
            return r.json()

    async def tasks_list(self, token: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}{API_PREFIX}/tasks"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=self._headers(token))
            r.raise_for_status()
            return r.json()

    async def tasks_search(self, token: str, q: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}{API_PREFIX}/tasks/search"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, params={"q": q}, headers=self._headers(token))
            r.raise_for_status()
            return r.json()

    async def task_create(
        self,
        token: str,
        title: str,
        description: Optional[str],
        is_important: bool,
        deadline_at_iso: Optional[str],
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{API_PREFIX}/tasks/"
        payload: Dict[str, Any] = {
            "title": title,
            "description": description,
            "is_important": is_important,
            "deadline_at": deadline_at_iso,
        }
        if deadline_at_iso is None:
            payload.pop("deadline_at", None)

        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, json=payload, headers=self._headers(token))
            r.raise_for_status()
            return r.json()

    async def task_complete(self, token: str, task_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}{API_PREFIX}/tasks/{task_id}/complete"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.patch(url, headers=self._headers(token))
            r.raise_for_status()
            return r.json()

    async def task_update(
        self,
        token: str,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        deadline_at_iso: Optional[str] = None,
        is_important: Optional[bool] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{API_PREFIX}/tasks/{task_id}"

        payload: Dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if is_important is not None:
            payload["is_important"] = is_important

        if deadline_at_iso is not None:
            payload["deadline_at"] = (deadline_at_iso or None)

        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.put(url, json=payload, headers=self._headers(token))
            r.raise_for_status()
            return r.json()


    async def task_delete(self, token: str, task_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}{API_PREFIX}/tasks/{task_id}"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.delete(url, headers=self._headers(token))
            r.raise_for_status()
            return r.json()

    async def stats(self, token: str) -> Dict[str, Any]:
        url = f"{self.base_url}{API_PREFIX}/stats/"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=self._headers(token))
            r.raise_for_status()
            return r.json()

    async def timing(self, token: str) -> Dict[str, Any]:
        url = f"{self.base_url}{API_PREFIX}/stats/timing"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=self._headers(token))
            r.raise_for_status()
            return r.json()

    async def today(self, token: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}{API_PREFIX}/stats/today"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=self._headers(token))
            r.raise_for_status()
            return r.json()


api = ApiClient(API_BASE_URL)


def get_token(user_id: int) -> Optional[str]:
    return TOKENS.get(user_id)


def require_login_message() -> str:
    return "Нужно войти. Используй /login (или /register)."


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Задачи"), KeyboardButton(text="➕ Добавить")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🧭 Сегодня")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🚪 Выйти")],
        ],
        resize_keyboard=True,
        selective=True,
    )


def fmt_task(t: Dict[str, Any]) -> str:
    status = "✅" if t.get("completed") else "🕒"
    quad = t.get("quadrant", "?")
    imp = "важная" if t.get("is_important") else "неважная"
    urg = "срочная" if t.get("is_urgent") else "несрочная"
    title = t.get("title", "")
    desc = (t.get("description") or "").strip()
    tid = t.get("id", "?")
    days = t.get("days_until_deadline", None)
    msg = t.get("status_message", None)
    deadline = t.get("deadline_at", None)

    extra = []
    if deadline:
        extra.append(f"дедлайн: {deadline}")
    if days is not None:
        extra.append(f"до дедлайна: {days} дн.")
    if msg:
        extra.append(msg)

    extra_s = ""
    if extra:
        extra_s = "\n   " + " | ".join(extra)

    desc_s = ""
    if desc:
        desc_s = f"\n📝 {desc}"

    return f"{status} #{tid} [{quad}] {title}{desc_s}\n   {imp}, {urg}{extra_s}"


def task_keyboard(task_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Выполнить", callback_data=f"done:{task_id}")
    kb.button(text="🗑 Удалить", callback_data=f"del:{task_id}")
    kb.button(text="✏️ Редактировать", callback_data=f"edit:{task_id}")
    kb.adjust(2, 1)
    return kb.as_markup()


def tasks_filter_kb(selected_status: str = "all", selected_q: str = "all"):
    kb = InlineKeyboardBuilder()

    # статус
    kb.button(text=("✅ Все" if selected_status == "all" else "Все"),
              callback_data=f"flt:st:all:q:{selected_q}")
    kb.button(text=("✅ В работе" if selected_status == "pending" else "В работе"),
              callback_data=f"flt:st:pending:q:{selected_q}")
    kb.button(text=("✅ Выполнено" if selected_status == "completed" else "Выполнено"),
              callback_data=f"flt:st:completed:q:{selected_q}")
    kb.adjust(3)

    # квадрант
    kb.button(text=("✅ Q1" if selected_q == "Q1" else "Q1"),
              callback_data=f"flt:st:{selected_status}:q:Q1")
    kb.button(text=("✅ Q2" if selected_q == "Q2" else "Q2"),
              callback_data=f"flt:st:{selected_status}:q:Q2")
    kb.button(text=("✅ Q3" if selected_q == "Q3" else "Q3"),
              callback_data=f"flt:st:{selected_status}:q:Q3")
    kb.button(text=("✅ Q4" if selected_q == "Q4" else "Q4"),
              callback_data=f"flt:st:{selected_status}:q:Q4")
    kb.button(text=("✅ Все Q" if selected_q == "all" else "Все Q"),
              callback_data=f"flt:st:{selected_status}:q:all")
    kb.adjust(3, 2)

    kb.button(text="🔄 Обновить", callback_data=f"flt:st:{selected_status}:q:{selected_q}")
    kb.adjust(1)

    return kb.as_markup()


def apply_filters(tasks: List[Dict[str, Any]], st: str, q: str) -> List[Dict[str, Any]]:
    res = tasks

    if st == "pending":
        res = [t for t in res if not t.get("completed")]
    elif st == "completed":
        res = [t for t in res if t.get("completed")]

    if q != "all":
        res = [t for t in res if t.get("quadrant") == q]

    return res


async def send_tasks_page(m: Message, tasks: List[Dict[str, Any]], st: str, q: str):
    filtered = apply_filters(tasks, st, q)

    await m.answer(
        f"📋 Задачи (фильтры: статус={st}, квадрант={q})\n"
        f"Найдено: {len(filtered)}",
        reply_markup=tasks_filter_kb(st, q)
    )

    if not filtered:
        await m.answer("Пусто по фильтрам. Попробуй другие фильтры или добавь задачу: /add",
                       reply_markup=main_menu_kb())
        return

    for t in filtered[:10]:
        await m.answer(fmt_task(t), reply_markup=task_keyboard(int(t["id"])))


# =========================
# FSM States
# =========================
class LoginFlow(StatesGroup):
    email = State()
    password = State()


class RegisterFlow(StatesGroup):
    nickname = State()
    email = State()
    password = State()


class AddTaskFlow(StatesGroup):
    title = State()
    description = State()
    important = State()
    deadline = State()


class EditTaskFlow(StatesGroup):
    title = State()
    description = State()
    important = State()
    deadline = State()


# =========================
# Bot handlers
# =========================
dp = Dispatcher()


@dp.message(Command("start"))
async def start(m: Message):
    await m.answer(
        "🤖 ToDo Bot (матрица Эйзенхауэра)\n\n"
        "Быстрые действия — на кнопках снизу.\n"
        "Если ещё не входил: /register или /login",
        reply_markup=main_menu_kb()
    )


@dp.message(Command("logout"))
async def logout(m: Message):
    TOKENS.pop(m.from_user.id, None)
    await m.answer("Ок, вышел. Токен удалён.", reply_markup=main_menu_kb())


@dp.message(Command("me"))
async def me(m: Message):
    token = get_token(m.from_user.id)
    if not token:
        await m.answer(require_login_message(), reply_markup=main_menu_kb())
        return
    try:
        u = await api.me(token)
        await m.answer(
            f"👤 Профиль:\n"
            f"Ник: {u.get('nickname')}\n"
            f"Email: {u.get('email')}\n"
            f"Роль: {u.get('role')}",
            reply_markup=main_menu_kb()
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            TOKENS.pop(m.from_user.id, None)
            await m.answer("Сессия истекла/токен неверный. Войди снова: /login", reply_markup=main_menu_kb())
        else:
            await m.answer(f"Ошибка API: {e.response.status_code} {e.response.text}", reply_markup=main_menu_kb())


# -------- Menu buttons --------
@dp.message(F.text == "🚪 Выйти")
async def menu_logout(m: Message):
    await logout(m)


@dp.message(F.text == "👤 Профиль")
async def menu_profile(m: Message):
    await me(m)


@dp.message(F.text == "📋 Задачи")
async def menu_tasks(m: Message):
    await tasks_list(m)


@dp.message(F.text == "➕ Добавить")
async def menu_add(m: Message, state: FSMContext):
    await add_start(m, state)


@dp.message(F.text == "📊 Статистика")
async def menu_stats(m: Message):
    await stats(m)


@dp.message(F.text == "🧭 Сегодня")
async def menu_today(m: Message):
    await today(m)


# -------- Register --------
@dp.message(Command("register"))
async def register_start(m: Message, state: FSMContext):
    await state.set_state(RegisterFlow.nickname)
    await m.answer("Регистрация. Введи никнейм (min 3 символа):", reply_markup=main_menu_kb())


@dp.message(RegisterFlow.nickname)
async def register_nickname(m: Message, state: FSMContext):
    await state.update_data(nickname=m.text.strip())
    await state.set_state(RegisterFlow.email)
    await m.answer("Теперь email:", reply_markup=main_menu_kb())


@dp.message(RegisterFlow.email)
async def register_email(m: Message, state: FSMContext):
    await state.update_data(email=m.text.strip())
    await state.set_state(RegisterFlow.password)
    await m.answer("Теперь пароль (min 6 символов):", reply_markup=main_menu_kb())


@dp.message(RegisterFlow.password)
async def register_password(m: Message, state: FSMContext):
    data = await state.get_data()
    nickname = data["nickname"]
    email = data["email"]
    password = m.text.strip()

    try:
        u = await api.register(nickname, email, password)
        await state.clear()
        await m.answer(
            f"✅ Зарегистрирован: {u.get('nickname')} ({u.get('email')}). Теперь /login",
            reply_markup=main_menu_kb()
        )
    except httpx.HTTPStatusError as e:
        await state.clear()
        await m.answer(f"Ошибка регистрации: {e.response.status_code}\n{e.response.text}",
                       reply_markup=main_menu_kb())


# -------- Login --------
@dp.message(Command("login"))
async def login_start(m: Message, state: FSMContext):
    await state.set_state(LoginFlow.email)
    await m.answer("Вход. Введи email:", reply_markup=main_menu_kb())


@dp.message(LoginFlow.email)
async def login_email(m: Message, state: FSMContext):
    await state.update_data(email=m.text.strip())
    await state.set_state(LoginFlow.password)
    await m.answer("Теперь пароль:", reply_markup=main_menu_kb())


@dp.message(LoginFlow.password)
async def login_password(m: Message, state: FSMContext):
    data = await state.get_data()
    email = data["email"]
    password = m.text.strip()

    try:
        token = await api.login(email, password)
        TOKENS[m.from_user.id] = token
        await state.clear()
        await m.answer("✅ Вошёл! Жми кнопки снизу.", reply_markup=main_menu_kb())
    except httpx.HTTPStatusError as e:
        await state.clear()
        await m.answer(f"Ошибка входа: {e.response.status_code}\n{e.response.text}",
                       reply_markup=main_menu_kb())


# -------- Tasks list --------
@dp.message(Command("tasks"))
async def tasks_list(m: Message):
    token = get_token(m.from_user.id)
    if not token:
        await m.answer(require_login_message(), reply_markup=main_menu_kb())
        return

    try:
        tasks = await api.tasks_list(token)
        if not tasks:
            await m.answer("Список пуст. Добавь задачу: /add", reply_markup=main_menu_kb())
            return

        await send_tasks_page(m, tasks, st="all", q="all")
    except httpx.HTTPStatusError as e:
        await m.answer(f"Ошибка API: {e.response.status_code}\n{e.response.text}", reply_markup=main_menu_kb())


# -------- Search --------
@dp.message(Command("search"))
async def tasks_search(m: Message, command: CommandObject):
    token = get_token(m.from_user.id)
    if not token:
        await m.answer(require_login_message(), reply_markup=main_menu_kb())
        return

    q = (command.args or "").strip()
    if len(q) < 2:
        await m.answer("Использование: /search <текст (min 2 символа)>", reply_markup=main_menu_kb())
        return

    try:
        tasks = await api.tasks_search(token, q)
        if not tasks:
            await m.answer("Ничего не найдено.", reply_markup=main_menu_kb())
            return
        for t in tasks[:10]:
            await m.answer(fmt_task(t), reply_markup=task_keyboard(int(t["id"])))
    except httpx.HTTPStatusError as e:
        await m.answer(f"Ошибка поиска: {e.response.status_code}\n{e.response.text}", reply_markup=main_menu_kb())


# -------- Add task (FSM) --------
@dp.message(Command("add"))
async def add_start(m: Message, state: FSMContext):
    token = get_token(m.from_user.id)
    if not token:
        await m.answer(require_login_message(), reply_markup=main_menu_kb())
        return

    await state.set_state(AddTaskFlow.title)
    await m.answer("Добавление задачи.\nВведи название (3–100 символов):", reply_markup=main_menu_kb())


@dp.message(AddTaskFlow.title)
async def add_title(m: Message, state: FSMContext):
    await state.update_data(title=m.text.strip())
    await state.set_state(AddTaskFlow.description)
    await m.answer("Описание (можно '-' если не нужно):", reply_markup=main_menu_kb())


@dp.message(AddTaskFlow.description)
async def add_description(m: Message, state: FSMContext):
    text = m.text.strip()
    await state.update_data(description=None if text == "-" else text)
    await state.set_state(AddTaskFlow.important)
    await m.answer("Задача важная? (да/нет):", reply_markup=main_menu_kb())


@dp.message(AddTaskFlow.important)
async def add_important(m: Message, state: FSMContext):
    ans = m.text.strip().lower()
    if ans not in ("да", "нет", "yes", "no", "y", "n"):
        await m.answer("Ответь 'да' или 'нет'.", reply_markup=main_menu_kb())
        return
    is_important = ans in ("да", "yes", "y")
    await state.update_data(is_important=is_important)
    await state.set_state(AddTaskFlow.deadline)
    await m.answer(
        "Дедлайн (опционально).\n"
        "Формат: YYYY-MM-DD или YYYY-MM-DD HH:MM\n"
        "Примеры: 2026-01-20 18:00 или 2026-01-20\n"
        "Если без дедлайна — напиши '-'",
        reply_markup=main_menu_kb()
    )


@dp.message(AddTaskFlow.deadline)
async def add_deadline(m: Message, state: FSMContext):
    token = get_token(m.from_user.id)
    if not token:
        await state.clear()
        await m.answer(require_login_message(), reply_markup=main_menu_kb())
        return

    raw = m.text.strip()
    deadline_iso: Optional[str] = None

    if raw != "-":
        try:
            if len(raw) == 10:
                deadline_iso = f"{raw}T00:00:00"
            else:
                date_part, time_part = raw.split()
                if len(time_part) == 5:
                    deadline_iso = f"{date_part}T{time_part}:00"
                else:
                    deadline_iso = f"{date_part}T{time_part}"
        except Exception:
            await m.answer("Не понял формат. Напиши YYYY-MM-DD или YYYY-MM-DD HH:MM, либо '-'",
                           reply_markup=main_menu_kb())
            return

    data = await state.get_data()
    title = data["title"]
    description = data.get("description")
    is_important = bool(data["is_important"])

    try:
        created = await api.task_create(token, title, description, is_important, deadline_iso)
        await state.clear()
        await m.answer("✅ Создано:\n" + fmt_task(created), reply_markup=task_keyboard(int(created["id"])))
    except httpx.HTTPStatusError as e:
        await state.clear()
        await m.answer(f"Ошибка создания: {e.response.status_code}\n{e.response.text}", reply_markup=main_menu_kb())


# -------- Edit task (FSM via inline button) --------
@dp.callback_query(F.data.startswith("edit:"))
async def cb_edit(c: CallbackQuery, state: FSMContext):
    token = get_token(c.from_user.id)
    if not token:
        await c.message.answer(require_login_message(), reply_markup=main_menu_kb())
        await c.answer()
        return

    task_id = int(c.data.split(":")[1])
    await state.update_data(edit_task_id=task_id)
    await state.set_state(EditTaskFlow.title)

    await c.message.answer(
        f"✏️ Редактирование задачи #{task_id}\n"
        "Введи новое название (или '-' чтобы не менять):"
    )
    await c.answer("Редактирование")


@dp.message(EditTaskFlow.title)
async def edit_title(m: Message, state: FSMContext):
    text = m.text.strip()
    title = None if text == "-" else text
    await state.update_data(edit_title=title)

    await state.set_state(EditTaskFlow.description)
    await m.answer("Введи новое описание (или '-' чтобы не менять):")


@dp.message(EditTaskFlow.description)
async def edit_description(m: Message, state: FSMContext):
    text = m.text.strip()
    description = None if text == "-" else text
    await state.update_data(edit_description=description)

    await state.set_state(EditTaskFlow.important)
    await m.answer("Важность:\n— '-' оставить как есть\n— 'да' сделать важной\n— 'нет' сделать неважной")

@dp.message(EditTaskFlow.important)
async def edit_important(m: Message, state: FSMContext):
    raw = m.text.strip().lower()

    if raw == "-":
        is_important = None   # не менять
    elif raw in ("да", "yes", "y"):
        is_important = True
    elif raw in ("нет", "no", "n"):
        is_important = False
    else:
        await m.answer("Не понял. Ответь: '-', 'да' или 'нет'.")
        return

    await state.update_data(edit_is_important=is_important)

    await state.set_state(EditTaskFlow.deadline)
    await m.answer(
        "Дедлайн:\n"
        "— '-' оставить как есть\n"
        "— '0' удалить дедлайн\n"
        "— или введи дату: YYYY-MM-DD или YYYY-MM-DD HH:MM\n"
        "Пример: 2026-01-20 18:00"
    )




def parse_deadline_input(raw: str) -> Optional[str]:
    raw = raw.strip()
    if raw == "-":
        return None  # не менять
    if raw == "0":
        return ""  # очистить дедлайн

    # новый дедлайн
    if len(raw) == 10:
        return f"{raw}T00:00:00"

    date_part, time_part = raw.split()
    if len(time_part) == 5:
        return f"{date_part}T{time_part}:00"
    return f"{date_part}T{time_part}"


@dp.message(EditTaskFlow.deadline)
async def edit_deadline(m: Message, state: FSMContext):
    token = get_token(m.from_user.id)
    if not token:
        await state.clear()
        await m.answer(require_login_message(), reply_markup=main_menu_kb())
        return

    raw = m.text.strip()
    try:
        deadline_iso = parse_deadline_input(raw)
    except Exception:
        await m.answer("Не понял формат. Варианты: '-', '0', YYYY-MM-DD, YYYY-MM-DD HH:MM")
        return

    data = await state.get_data()
    task_id = int(data["edit_task_id"])
    title = data.get("edit_title")
    description = data.get("edit_description")
    is_important = data.get("edit_is_important")

    try:
        updated = await api.task_update(
            token,
            task_id,
            title=title,
            description=description,
            deadline_at_iso=deadline_iso,
            is_important=is_important,
        )
        await state.clear()
        await m.answer("✅ Обновлено:\n" + fmt_task(updated), reply_markup=task_keyboard(int(updated["id"])))
    except httpx.HTTPStatusError as e:
        await state.clear()
        await m.answer(f"Ошибка редактирования: {e.response.status_code}\n{e.response.text}",
                       reply_markup=main_menu_kb())


# -------- Inline callbacks (done/del/filter) --------
@dp.callback_query(F.data.startswith("done:"))
async def cb_done(c: CallbackQuery):
    token = get_token(c.from_user.id)
    if not token:
        await c.message.answer(require_login_message(), reply_markup=main_menu_kb())
        await c.answer()
        return

    task_id = int(c.data.split(":")[1])
    try:
        t = await api.task_complete(token, task_id)
        await c.message.edit_text("✅ Выполнено!\n" + fmt_task(t))
        await c.answer("Готово")
    except httpx.HTTPStatusError as e:
        await c.message.answer(f"Ошибка: {e.response.status_code}\n{e.response.text}", reply_markup=main_menu_kb())
        await c.answer("Ошибка")


@dp.callback_query(F.data.startswith("del:"))
async def cb_del(c: CallbackQuery):
    token = get_token(c.from_user.id)
    if not token:
        await c.message.answer(require_login_message(), reply_markup=main_menu_kb())
        await c.answer()
        return

    task_id = int(c.data.split(":")[1])
    try:
        res = await api.task_delete(token, task_id)
        await c.message.edit_text(f"🗑 Удалено: #{res.get('id')} {res.get('title')}")
        await c.answer("Удалено")
    except httpx.HTTPStatusError as e:
        await c.message.answer(f"Ошибка: {e.response.status_code}\n{e.response.text}", reply_markup=main_menu_kb())
        await c.answer("Ошибка")


@dp.callback_query(F.data.startswith("flt:"))
async def cb_filter(c: CallbackQuery):
    token = get_token(c.from_user.id)
    if not token:
        await c.message.answer(require_login_message(), reply_markup=main_menu_kb())
        await c.answer()
        return

    parts = c.data.split(":")
    st = parts[2]
    q = parts[4]

    try:
        tasks = await api.tasks_list(token)
        await c.message.answer("🔎 Применяю фильтры…", reply_markup=main_menu_kb())
        await send_tasks_page(c.message, tasks, st=st, q=q)
        await c.answer("Готово")
    except httpx.HTTPStatusError as e:
        await c.message.answer(f"Ошибка: {e.response.status_code}\n{e.response.text}", reply_markup=main_menu_kb())
        await c.answer("Ошибка")


# -------- Stats --------
@dp.message(Command("stats"))
async def stats(m: Message):
    token = get_token(m.from_user.id)
    if not token:
        await m.answer(require_login_message(), reply_markup=main_menu_kb())
        return

    try:
        s = await api.stats(token)
        by_q = s.get("by_quadrant", {})
        by_st = s.get("by_status", {})
        await m.answer(
            "📊 Статистика:\n"
            f"Всего задач: {s.get('total_tasks')}\n\n"
            f"Квадранты: Q1={by_q.get('Q1', 0)} | Q2={by_q.get('Q2', 0)} | Q3={by_q.get('Q3', 0)} | Q4={by_q.get('Q4', 0)}\n"
            f"Статус: выполнено={by_st.get('completed', 0)} | в работе={by_st.get('pending', 0)}",
            reply_markup=main_menu_kb()
        )
    except httpx.HTTPStatusError as e:
        await m.answer(f"Ошибка stats: {e.response.status_code}\n{e.response.text}", reply_markup=main_menu_kb())


@dp.message(Command("timing"))
async def timing(m: Message):
    token = get_token(m.from_user.id)
    if not token:
        await m.answer(require_login_message(), reply_markup=main_menu_kb())
        return

    try:
        t = await api.timing(token)
        await m.answer(
            "⏱ По дедлайнам:\n"
            f"В срок: {t.get('completed_on_time', 0)}\n"
            f"С опозданием: {t.get('completed_late', 0)}\n"
            f"В работе по плану: {t.get('on_plan_pending', 0)}\n"
            f"Просрочены: {t.get('overtime_pending', 0)}",
            reply_markup=main_menu_kb()
        )
    except httpx.HTTPStatusError as e:
        await m.answer(f"Ошибка timing: {e.response.status_code}\n{e.response.text}", reply_markup=main_menu_kb())


@dp.message(Command("today"))
async def today(m: Message):
    token = get_token(m.from_user.id)
    if not token:
        await m.answer(require_login_message(), reply_markup=main_menu_kb())
        return

    try:
        tasks = await api.today(token)
        if not tasks:
            await m.answer("Сегодня нет невыполненных задач с дедлайном на сегодня.", reply_markup=main_menu_kb())
            return
        for t in tasks[:10]:
            await m.answer("📌 Сегодня:\n" + fmt_task(t), reply_markup=task_keyboard(int(t["id"])))
    except httpx.HTTPStatusError as e:
        await m.answer(f"Ошибка today: {e.response.status_code}\n{e.response.text}", reply_markup=main_menu_kb())


# =========================
# Run
# =========================
async def start_bot():
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


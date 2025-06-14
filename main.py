import json
import asyncio
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from dotenv import load_dotenv
import random

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

with open("results.json", "r", encoding="utf-8") as f:
    results = json.load(f)

class QuizState(StatesGroup):
    current = State()
    answers = State()

@dp.message(F.text.lower() == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Начать хронику", callback_data="start_quiz")]
    ])
    await message.answer(
        "Ты стоишь у трибуны старого Сената. Вокруг — шёпот историй. Хочешь ли ты узнать, кем бы ты стал в великой хронике мировой политики?",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "start_quiz")
async def start_quiz(callback, state: FSMContext):
    await state.update_data(current=0, answers=[])
    await send_question(callback.message, state)
    await callback.answer()

async def send_question(message: Message, state: FSMContext):
    data = await state.get_data()
    current = data["current"]
    q = questions[current]
    keyboard = InlineKeyboardBuilder()
    for i, opt in enumerate(q["options"], 1):
        keyboard.button(text=str(i), callback_data=f"answer_{i-1}")
    keyboard.adjust(len(q["options"]))
    text = (
        f"<b>Вопрос {current+1} из {len(questions)}</b>\n\n"
        f"{q['text']}\n\n" +
        "\n".join([f"<b>{i+1}.</b> {opt['text']}" for i, opt in enumerate(q['options'])])
    )
    await message.answer(text, reply_markup=keyboard.as_markup())

@dp.callback_query(F.data.startswith("answer_"))
async def handle_answer(callback, state: FSMContext):
    data = await state.get_data()
    if "current" not in data or "answers" not in data:
        await callback.answer("Сессия устарела. Пожалуйста, начни тест заново.", show_alert=True)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📜 Начать хронику", callback_data="start_quiz")]
        ])
        await callback.message.answer("🔁 Нажми кнопку ниже, чтобы начать заново:", reply_markup=keyboard)
        return
    current = data["current"]
    selected = int(callback.data.split("_")[1])
    q = questions[current]
    # Проверка структуры вопроса
    if "options" not in q or not isinstance(q["options"], list):
        await callback.answer("Ошибка в вопросе.", show_alert=True)
        return
    # Проверка выбранного индекса
    if selected < 0 or selected >= len(q["options"]):
        await callback.answer("Некорректный выбор.", show_alert=True)
        return
    answer = q["options"][selected]
    answers = data["answers"]
    answers.append({"scale": answer["scale"], "value": answer["value"]})
    await state.update_data(answers=answers)

    if current + 1 >= len(questions):
        await show_result(callback, state)
    else:
        await state.update_data(current=current + 1)
        await send_question(callback.message, state)
    await callback.answer()

async def show_result(callback, state: FSMContext):
    data = await state.get_data()
    answers = data["answers"]
    scores = {"IE": 0, "SN": 0, "TF": 0, "JP": 0}
    for ans in answers:
        scores[ans["scale"]] += ans["value"]

    result_type = ""
    result_type += "I" if scores["IE"] < 0 else "E"
    result_type += "S" if scores["SN"] < 0 else "N"
    result_type += "T" if scores["TF"] < 0 else "F"
    result_type += "J" if scores["JP"] < 0 else "P"

    result = results[result_type]

    # Отправляем результат типа
    await callback.message.answer(
        f"<b>📘 Тип личности: {result_type}</b>\n"
        f"<b>{result['title']}</b>\n\n"
        f"{result['description']}"
    )

    # Формируем список исторических фигур
    notable = result.get("notable_politicians", [])

    def count_match(a, b):
        return sum(1 for x, y in zip(a, b) if x == y)

    sorted_leaders = sorted(
        notable,
        key=lambda pol: count_match(pol["type"], result_type),
        reverse=True
    )
    if sorted_leaders:
        leaders_text = "🔎 Ближайшие к тебе исторические фигуры:\n\n"
        for pol in sorted_leaders:
            match_score = count_match(pol["type"], result_type)
            match_percent = match_score * 25
            leaders_text += f"• {pol['name_ru']} — {pol['reason']} (совпадение {match_percent}%)\n"
        await callback.message.answer(leaders_text)

    user = callback.from_user
    await bot.send_message(
        ADMIN_ID,
        f"🗳 Новый тест политического типа\n"
        f"Тип: {result_type} — {result['title']}\n"
        f"Пользователь: @{user.username or user.full_name} ({user.id})"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Пройти хронику заново", callback_data="start_quiz")]
    ])
    await callback.message.answer("Пожелаешь пройти путь заново?", reply_markup=keyboard)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import json

def parse_file(filename):
    universities = []
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)  
        for line in f:
            parts = line.strip().split(';')
            if len(parts) >= 6:
                data = {
                    "id": parts[0],
                    "name": parts[1].replace('\n', ' '),
                    "subjects": parts[2],
                    "score": parts[3],
                    "places": parts[4],
                    "price": parts[5]
                }
                universities.append(data)
    
    with open('data.json', 'w', encoding='utf-8') as jf:
        json.dump(universities, jf, ensure_ascii=False, indent=4)

parse_file('sixseven.txt')

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


TOKEN = "6909186904:AAFnebPVQrDMYZctuN4Ell5r1d9XkCL1ViY"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    waiting_for_subjects = State()
    waiting_for_score = State()

def load_data():
    universities = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'sixseven.txt')
    
    if not os.path.exists(file_path):
        logging.error(f"ФАЙЛ НЕ НАЙДЕН: {file_path}")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith('№;'):
                    continue
                
                parts = line.split(';')
                if len(parts) >= 6:
                    universities.append({
                        "name": parts[1].strip(),
                        "subjects": parts[2].lower(),
                        "score_raw": parts[3],
                        "places": parts[4],
                        "price": parts[5]
                    })
    except Exception as e:
        logging.error(f"Ошибка чтения: {e}")
    
    return universities

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Подобрать вуз"))
    await message.answer(
        "Привет! Я помогу найти вуз Москвы по твоим баллам ЕГЭ.",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@dp.message(F.text == "Подобрать вуз")
async def ask_subjects(message: types.Message, state: FSMContext):
    await message.answer("Введите 3 предмета через запятую (например: Рус, Мат, Физ):")
    await state.set_state(Form.waiting_for_subjects)

@dp.message(Form.waiting_for_subjects)
async def process_subjects(message: types.Message, state: FSMContext):
    await state.update_data(subjects=message.text.lower())
    await message.answer("Введите вашу общую сумму баллов за 3 предмета:")
    await state.set_state(Form.waiting_for_score)

@dp.message(Form.waiting_for_score)
async def process_score(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число (например: 260).")
        return

    user_score = int(message.text)
    user_data = await state.get_data()
    user_subjects = [s.strip()[:4] for s in user_data['subjects'].split(',')]
    
    all_unis = load_data()
    matches = []

    for uni in all_unis:
        try:
            min_score_str = uni['score_raw'].split('-')[0].split(' ')[0].replace('+', '')
            if min_score_str.isdigit():
                min_score = int(min_score_str)

                if user_score >= min_score:
                
                    if any(s in uni['subjects'] for s in user_subjects):
                        matches.append(uni)
        except:
            continue

    if not matches:
        await message.answer("К сожалению, подходящих вузов не найдено. Попробуйте ввести другие предметы.")
    else:
        res = "✅ **Вузы, куда вы можете пройти:**\n\n"
        for uni in matches[:10]: 
            res += f"🏛 **{uni['name']}**\n"
            res += f"📊 Балл: {uni['score_raw']} | Мест: {uni['places']}\n"
            res += f"💰 Цена: {uni['price']}\n\n"
        
        await message.answer(res, parse_mode="Markdown")
    
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from utils.food_api import get_food_info

router = Router()


class FoodStates(StatesGroup):
    """Состояния для логирования еды"""
    waiting_for_grams = State()


@router.message(Command("log_food"))
async def cmd_log_food(message: Message, command: CommandObject, state: FSMContext):
    """Записать съеденную еду"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        await message.answer(
            "❌ Сначала настройте профиль с помощью /set_profile"
        )
        return
    
    # Проверяем, указан ли продукт
    if not command.args:
        await message.answer(
            "🍎 <b>Запись еды</b>\n\n"
            "Укажите название продукта:\n"
            "<code>/log_food банан</code>\n\n"
            "Примеры:\n"
            "• /log_food яблоко\n"
            "• /log_food курица\n"
            "• /log_food пицца\n"
            "• /log_food овсянка",
            parse_mode="HTML"
        )
        return
    
    product_name = command.args.strip()
    
    # Показываем, что ищем продукт
    searching_msg = await message.answer(f"🔍 Ищу информацию о '{product_name}'...")
    
    # Получаем информацию о продукте
    food_info = await get_food_info(product_name)
    
    if not food_info:
        await searching_msg.edit_text(
            f"❌ Продукт '{product_name}' не найден.\n\n"
            "💡 Попробуйте:\n"
            "• Использовать другое название\n"
            "• Написать на английском\n"
            "• Использовать более общее название\n\n"
            "Примеры: банан, яблоко, курица, рис, хлеб"
        )
        return
    
    # Сохраняем информацию о продукте в состоянии
    await state.update_data(
        food_name=food_info["name"],
        food_calories_per_100g=food_info["calories"],
        food_emoji=food_info.get("emoji", "🍽️")
    )
    await state.set_state(FoodStates.waiting_for_grams)
    
    await searching_msg.edit_text(
        f"{food_info.get('emoji', '🍽️')} <b>{food_info['name']}</b>\n"
        f"Калорийность: {food_info['calories']} ккал на 100 г\n\n"
        f"Сколько грамм вы съели?\n"
        f"<i>Пример: 150</i>",
        parse_mode="HTML"
    )


@router.message(FoodStates.waiting_for_grams)
async def process_food_grams(message: Message, state: FSMContext):
    """Обработка количества съеденной еды"""
    try:
        grams = float(message.text.replace(",", "."))
        if grams <= 0:
            await message.answer("❌ Количество должно быть положительным числом")
            return
        if grams > 5000:
            await message.answer("❌ Слишком большое количество. Введите реальное значение (до 5000 г)")
            return
        
        # Получаем данные о продукте из состояния
        data = await state.get_data()
        food_name = data["food_name"]
        calories_per_100g = data["food_calories_per_100g"]
        emoji = data.get("food_emoji", "🍽️")
        
        # Рассчитываем калории
        calories = (calories_per_100g * grams) / 100
        
        # Записываем в базу
        db.log_food(message.from_user.id, food_name, calories, grams)
        
        # Получаем статистику за день
        today_calories = db.get_today_calories_consumed(message.from_user.id)
        today_burned = db.get_today_calories_burned(message.from_user.id)
        
        user = db.get_user(message.from_user.id)
        calorie_goal = user.get("calorie_goal", 2000)
        
        # Баланс калорий
        balance = today_calories - today_burned
        remaining = max(0, calorie_goal - balance)
        
        # Определяем статус
        if balance >= calorie_goal:
            status = "⚠️ Дневная норма превышена"
            percent = min(150, int(balance / calorie_goal * 100))
        else:
            status = f"✅ Осталось: {int(remaining)} ккал"
            percent = int(balance / calorie_goal * 100)
        
        filled = min(10, percent // 10)
        progress_bar = "█" * filled + "░" * (10 - filled) + f" {percent}%"
        
        await state.clear()
        
        await message.answer(
            f"{emoji} <b>Записано: {food_name}</b>\n"
            f"📝 {grams:.0f} г = {calories:.1f} ккал\n\n"
            f"📊 <b>Прогресс за сегодня:</b>\n"
            f"Потреблено: {int(today_calories)} ккал\n"
            f"Сожжено: {int(today_burned)} ккал\n"
            f"Баланс: {int(balance)} / {int(calorie_goal)} ккал\n"
            f"[{progress_bar}]\n\n"
            f"{status}",
            parse_mode="HTML"
        )
        
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите число.\n"
            "Например: 150"
        )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отменить текущее действие"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.")
        return
    
    await state.clear()
    await message.answer("❌ Действие отменено.")



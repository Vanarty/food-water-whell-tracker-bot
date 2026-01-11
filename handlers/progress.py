from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command

import database as db
from utils.weather import get_weather
from utils.calculations import (
    calculate_water_goal, 
    get_workout_recommendations
)
from utils.food_api import (
    get_low_calorie_recommendations,
    get_high_protein_recommendations
)
from utils.charts import create_combined_progress_chart


router = Router()


@router.message(Command("check_progress"))
async def cmd_check_progress(message: Message):
    """Показать текущий прогресс"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        await message.answer(
            "❌ Сначала настройте профиль с помощью /set_profile"
        )
        return
    
    # Получаем данные за сегодня
    today_water = db.get_today_water(message.from_user.id)
    today_calories = db.get_today_calories_consumed(message.from_user.id)
    today_burned = db.get_today_calories_burned(message.from_user.id)
    today_extra_water = db.get_today_extra_water(message.from_user.id)
    
    # Рассчитываем нормы с учётом погоды
    weather = await get_weather(user["city"]) if user.get("city") else None
    water_calc = calculate_water_goal(
        user["weight"],
        user["activity_minutes"],
        weather["temp"] if weather else None
    )
    
    # Общая цель воды с учётом тренировок
    water_goal = water_calc["total"] + today_extra_water
    calorie_goal = user.get("calorie_goal", 2000)
    
    # Расчёт прогресса по воде
    water_remaining = max(0, water_goal - today_water)
    water_percent = min(100, int(today_water / water_goal * 100)) if water_goal > 0 else 0
    water_filled = water_percent // 10
    water_bar = "█" * water_filled + "░" * (10 - water_filled)
    
    # Расчёт прогресса по калориям
    calorie_balance = today_calories - today_burned
    calorie_remaining = max(0, calorie_goal - calorie_balance)
    calorie_percent = min(150, int(calorie_balance / calorie_goal * 100)) if calorie_goal > 0 else 0
    calorie_filled = min(10, calorie_percent // 10)
    calorie_bar = "█" * calorie_filled + "░" * (10 - calorie_filled)
    
    # Статусы
    if today_water >= water_goal:
        water_status = "🎉 Цель достигнута!"
    else:
        water_status = f"💧 Осталось: {water_remaining} мл"
    
    if calorie_balance <= calorie_goal:
        calorie_status = f"✅ Осталось: {int(calorie_remaining)} ккал"
    else:
        excess = int(calorie_balance - calorie_goal)
        calorie_status = f"⚠️ Превышение на {excess} ккал"
    
    # Информация о погоде
    weather_info = ""
    if weather:
        weather_info = f"🌡️ {weather['city_name']}: {weather['temp']:.1f}°C\n\n"
    
    response = (
        f"📊 <b>Ваш прогресс за сегодня</b>\n\n"
        f"{weather_info}"
        f"<b>💧 Вода:</b>\n"
        f"Выпито: {today_water} мл из {water_goal} мл\n"
        f"[{water_bar}] {water_percent}%\n"
        f"{water_status}\n\n"
        f"<b>🔥 Калории:</b>\n"
        f"Потреблено: {int(today_calories)} ккал\n"
        f"Сожжено: {int(today_burned)} ккал\n"
        f"Баланс: {int(calorie_balance)} / {int(calorie_goal)} ккал\n"
        f"[{calorie_bar}] {calorie_percent}%\n"
        f"{calorie_status}\n\n"
        f"📈 /show_charts — графики за неделю\n"
        f"💡 /recommendations — советы"
    )
    
    await message.answer(response, parse_mode="HTML")


@router.message(Command("show_charts"))
async def cmd_show_charts(message: Message):
    """Показать графики прогресса"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        await message.answer(
            "❌ Сначала настройте профиль с помощью /set_profile"
        )
        return
    
    await message.answer("📊 Генерирую графики...")
    
    # Получаем историю
    water_history = db.get_water_history(message.from_user.id, 7)
    food_history = db.get_food_history(message.from_user.id, 7)
    workout_history = db.get_workout_history(message.from_user.id, 7)
    
    # Текущие данные
    today_water = db.get_today_water(message.from_user.id)
    today_consumed = db.get_today_calories_consumed(message.from_user.id)
    today_burned = db.get_today_calories_burned(message.from_user.id)
    today_extra_water = db.get_today_extra_water(message.from_user.id)
    
    # Нормы
    weather = await get_weather(user["city"]) if user.get("city") else None
    water_calc = calculate_water_goal(
        user["weight"],
        user["activity_minutes"],
        weather["temp"] if weather else None
    )
    water_goal = water_calc["total"] + today_extra_water
    calorie_goal = user.get("calorie_goal", 2000)
    
    # Создаём комбинированный график
    chart_buf = create_combined_progress_chart(
        water_history,
        food_history,
        workout_history,
        water_goal,
        calorie_goal,
        today_water,
        today_consumed,
        today_burned
    )
    
    # Отправляем как фото
    photo = BufferedInputFile(chart_buf.read(), filename="progress.png")
    await message.answer_photo(
        photo,
        caption="📊 <b>Ваш прогресс за последнюю неделю</b>\n\n"
                "💧 Вода: синий цвет - не достигнута цель, зелёный - достигнута\n"
                "🔥 Калории: красный - потреблено, зелёный - сожжено",
        parse_mode="HTML"
    )


@router.message(Command("recommendations"))
async def cmd_recommendations(message: Message):
    """Показать рекомендации по питанию и тренировкам"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        await message.answer(
            "❌ Сначала настройте профиль с помощью /set_profile"
        )
        return
    
    # Получаем текущий прогресс
    today_calories = db.get_today_calories_consumed(message.from_user.id)
    today_burned = db.get_today_calories_burned(message.from_user.id)
    calorie_goal = user.get("calorie_goal", 2000)
    
    balance = today_calories - today_burned
    
    response = "💡 <b>Рекомендации для вас</b>\n\n"
    
    # Если превышен лимит калорий - рекомендуем тренировки
    if balance > calorie_goal:
        excess = balance - calorie_goal
        response += f"⚠️ <b>Вы превысили норму калорий на {int(excess)} ккал</b>\n\n"
        response += "<b>🏃 Рекомендуемые тренировки для сжигания:</b>\n"
        
        workout_recs = get_workout_recommendations(
            today_calories, calorie_goal, today_burned, user["weight"]
        )
        
        if workout_recs:
            for rec in workout_recs:
                response += f"{rec['emoji']} {rec['workout']}: {rec['duration']} мин (~{rec['calories']} ккал)\n"
        else:
            response += "• Бег 30 мин\n• Плавание 45 мин\n• Велосипед 40 мин\n"
        
        response += "\n"
    
    # Рекомендации по низкокалорийным продуктам
    response += "<b>🥗 Низкокалорийные продукты (до 50 ккал/100г):</b>\n"
    low_cal = get_low_calorie_recommendations()
    for product in low_cal[:5]:
        response += f"{product['emoji']} {product['name']}: {product['calories']} ккал\n"
    
    response += "\n<b>💪 Белковые продукты для мышц:</b>\n"
    protein = get_high_protein_recommendations()
    for product in protein[:5]:
        response += f"{product['emoji']} {product['name']}: {product['calories']} ккал ({product['protein']}г белка)\n"
    
    # Общие советы
    response += "\n<b>📝 Общие советы:</b>\n"
    response += "• Пейте воду перед едой\n"
    response += "• Ешьте медленно и осознанно\n"
    response += "• Выбирайте цельные продукты\n"
    response += "• Тренируйтесь регулярно\n"
    
    await message.answer(response, parse_mode="HTML")



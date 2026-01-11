from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

import database as db
from utils.weather import get_weather
from utils.calculations import calculate_water_goal

router = Router()


@router.message(Command("log_water"))
async def cmd_log_water(message: Message, command: CommandObject):
    """Записать выпитую воду"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        await message.answer(
            "❌ Сначала настройте профиль с помощью /set_profile"
        )
        return
    
    # Проверяем, указано ли количество воды
    if not command.args:
        await message.answer(
            "💧 <b>Запись воды</b>\n\n"
            "Укажите количество воды в мл:\n"
            "<code>/log_water 250</code>\n\n"
            "Примеры:\n"
            "• Стакан воды: /log_water 250\n"
            "• Бутылка 0.5л: /log_water 500\n"
            "• Чашка чая: /log_water 200",
            parse_mode="HTML"
        )
        return
    
    try:
        amount = int(command.args)
        if amount <= 0:
            await message.answer("❌ Количество воды должно быть положительным числом")
            return
        if amount > 5000:
            await message.answer("❌ Слишком большое количество. Введите реальное значение (до 5000 мл)")
            return
        
        # Записываем воду в базу
        db.log_water(message.from_user.id, amount)
        
        # Получаем текущую статистику
        today_water = db.get_today_water(message.from_user.id)
        today_extra_water = db.get_today_extra_water(message.from_user.id)
        
        # Рассчитываем норму с учётом погоды
        weather = await get_weather(user["city"]) if user.get("city") else None
        water_calc = calculate_water_goal(
            user["weight"],
            user["activity_minutes"],
            weather["temp"] if weather else None
        )
        
        # Общая цель = базовая норма + дополнительная вода от тренировок
        total_goal = water_calc["total"] + today_extra_water
        remaining = max(0, total_goal - today_water)
        
        # Определяем статус
        if today_water >= total_goal:
            status = "🎉 Цель достигнута!"
            progress_bar = "██████████ 100%"
        else:
            percent = min(100, int(today_water / total_goal * 100))
            filled = percent // 10
            progress_bar = "█" * filled + "░" * (10 - filled) + f" {percent}%"
            status = f"💪 Осталось: {remaining} мл"
        
        response = (
            f"💧 <b>Записано: {amount} мл воды</b>\n\n"
            f"📊 <b>Прогресс за сегодня:</b>\n"
            f"Выпито: {today_water} мл из {total_goal} мл\n"
            f"[{progress_bar}]\n\n"
            f"{status}"
        )
        
        if today_extra_water > 0:
            response += f"\n\n💡 Включая +{today_extra_water} мл от тренировок"
        
        await message.answer(response, parse_mode="HTML")
        
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите число.\n"
            "Пример: /log_water 250"
        )



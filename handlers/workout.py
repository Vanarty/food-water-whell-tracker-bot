from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

import database as db
from utils.calculations import calculate_workout_calories

router = Router()


@router.message(Command("log_workout"))
async def cmd_log_workout(message: Message, command: CommandObject):
    """Записать тренировку"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        await message.answer(
            "❌ Сначала настройте профиль с помощью /set_profile"
        )
        return
    
    # Проверяем аргументы
    if not command.args:
        await message.answer(
            "🏃 <b>Запись тренировки</b>\n\n"
            "Укажите тип тренировки и время в минутах:\n"
            "<code>/log_workout бег 30</code>\n\n"
            "<b>Доступные типы тренировок:</b>\n\n"
            "🏃 <b>Кардио:</b>\n"
            "бег, ходьба, велосипед, плавание, скакалка, танцы, аэробика\n\n"
            "🏋️ <b>Силовые:</b>\n"
            "силовая, кроссфит, воркаут, качалка, отжимания, приседания\n\n"
            "⚽ <b>Спорт:</b>\n"
            "футбол, баскетбол, волейбол, теннис, бокс\n\n"
            "🧘 <b>Другое:</b>\n"
            "йога, пилатес, растяжка",
            parse_mode="HTML"
        )
        return
    
    # Парсим аргументы
    args = command.args.strip().split()
    
    if len(args) < 2:
        await message.answer(
            "❌ Укажите тип тренировки и время.\n"
            "Пример: /log_workout бег 30"
        )
        return
    
    # Тип тренировки - все слова кроме последнего
    workout_type = " ".join(args[:-1])
    
    try:
        duration = int(args[-1])
        if duration <= 0:
            await message.answer("❌ Время тренировки должно быть положительным числом")
            return
        if duration > 480:
            await message.answer("❌ Слишком длинная тренировка. Введите реальное значение (до 480 минут)")
            return
        
        # Рассчитываем калории
        workout_result = calculate_workout_calories(
            workout_type,
            duration,
            user["weight"]
        )
        
        # Записываем в базу
        db.log_workout(
            message.from_user.id,
            workout_result["type"],
            duration,
            workout_result["calories_burned"],
            workout_result["extra_water"]
        )
        
        # Получаем статистику за день
        today_burned = db.get_today_calories_burned(message.from_user.id)
        today_consumed = db.get_today_calories_consumed(message.from_user.id)
        today_extra_water = db.get_today_extra_water(message.from_user.id)
        
        calorie_goal = user.get("calorie_goal", 2000)
        balance = today_consumed - today_burned
        
        await message.answer(
            f"{workout_result['emoji']} <b>{workout_result['type']}</b> - {duration} мин\n\n"
            f"🔥 Сожжено: <b>{workout_result['calories_burned']:.0f} ккал</b>\n"
            f"💧 Выпейте дополнительно: <b>{workout_result['extra_water']} мл воды</b>\n\n"
            f"📊 <b>Статистика за сегодня:</b>\n"
            f"• Потреблено: {int(today_consumed)} ккал\n"
            f"• Сожжено: {int(today_burned)} ккал\n"
            f"• Баланс: {int(balance)} / {int(calorie_goal)} ккал\n"
            f"• Доп. вода от тренировок: +{today_extra_water} мл\n\n"
            f"💪 Отличная работа!",
            parse_mode="HTML"
        )
        
    except ValueError:
        await message.answer(
            "❌ Последним аргументом должно быть число минут.\n"
            "Пример: /log_workout бег 30"
        )



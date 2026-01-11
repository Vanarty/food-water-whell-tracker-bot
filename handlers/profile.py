from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import database as db
from utils.weather import get_weather
from utils.calculations import calculate_water_goal, calculate_calorie_goal

router = Router()


class ProfileStates(StatesGroup):
    """Состояния для настройки профиля"""
    waiting_for_weight = State()
    waiting_for_height = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_activity = State()
    waiting_for_city = State()
    waiting_for_calorie_goal = State()


@router.message(Command("set_profile"))
async def cmd_set_profile(message: Message, state: FSMContext):
    """Начать настройку профиля"""
    await state.set_state(ProfileStates.waiting_for_weight)
    await message.answer(
        "👤 <b>Настройка профиля</b>\n\n"
        "Шаг 1/6: Введите ваш <b>вес</b> (в кг):\n"
        "<i>Пример: 70</i>",
        parse_mode="HTML"
    )


@router.message(ProfileStates.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    """Обработка веса"""
    try:
        weight = float(message.text.replace(",", "."))
        if weight < 20 or weight > 300:
            await message.answer("❌ Введите реальный вес (от 20 до 300 кг)")
            return
        
        await state.update_data(weight=weight)
        await state.set_state(ProfileStates.waiting_for_height)
        await message.answer(
            "✅ Вес сохранён!\n\n"
            "Шаг 2/6: Введите ваш <b>рост</b> (в см):\n"
            "<i>Пример: 175</i>",
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число. Например: 70")


@router.message(ProfileStates.waiting_for_height)
async def process_height(message: Message, state: FSMContext):
    """Обработка роста"""
    try:
        height = float(message.text.replace(",", "."))
        if height < 100 or height > 250:
            await message.answer("❌ Введите реальный рост (от 100 до 250 см)")
            return
        
        await state.update_data(height=height)
        await state.set_state(ProfileStates.waiting_for_age)
        await message.answer(
            "✅ Рост сохранён!\n\n"
            "Шаг 3/6: Введите ваш <b>возраст</b>:\n"
            "<i>Пример: 25</i>",
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число. Например: 175")


@router.message(ProfileStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    """Обработка возраста"""
    try:
        age = int(message.text)
        if age < 10 or age > 120:
            await message.answer("❌ Введите реальный возраст (от 10 до 120 лет)")
            return
        
        await state.update_data(age=age)
        await state.set_state(ProfileStates.waiting_for_gender)
        
        # Клавиатура для выбора пола
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="👨 Мужской", callback_data="gender_male"),
                InlineKeyboardButton(text="👩 Женский", callback_data="gender_female")
            ]
        ])
        
        await message.answer(
            "✅ Возраст сохранён!\n\n"
            "Шаг 4/6: Выберите ваш <b>пол</b>:",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число. Например: 25")


@router.callback_query(F.data.startswith("gender_"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    """Обработка пола"""
    gender = "male" if callback.data == "gender_male" else "female"
    await state.update_data(gender=gender)
    await state.set_state(ProfileStates.waiting_for_activity)
    
    await callback.message.edit_text(
        f"✅ Пол сохранён: {'👨 Мужской' if gender == 'male' else '👩 Женский'}\n\n"
        "Шаг 5/6: Сколько <b>минут физической активности</b> у вас обычно в день?\n"
        "<i>Пример: 30</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(ProfileStates.waiting_for_activity)
async def process_activity(message: Message, state: FSMContext):
    """Обработка уровня активности"""
    try:
        activity = int(message.text)
        if activity < 0 or activity > 480:
            await message.answer("❌ Введите реалистичное значение (от 0 до 480 минут)")
            return
        
        await state.update_data(activity_minutes=activity)
        await state.set_state(ProfileStates.waiting_for_city)
        await message.answer(
            "✅ Активность сохранена!\n\n"
            "Шаг 6/6: В каком <b>городе</b> вы находитесь?\n"
            "<i>Пример: Москва</i>\n\n"
            "💡 Это нужно для учёта погоды в расчёте нормы воды.",
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число. Например: 30")


@router.message(ProfileStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    """Обработка города"""
    city = message.text.strip()
    
    # Проверяем город через API погоды
    weather = await get_weather(city)
    if not weather:
        await message.answer(
            f"❌ Город '{city}' не найден. Попробуйте ввести название на английском "
            "или выберите крупный ближайший город.\n"
            "<i>Пример: Moscow, Saint Petersburg</i>",
            parse_mode="HTML"
        )
        return
    
    await state.update_data(city=weather["city_name"])
    
    # Получаем все данные и рассчитываем нормы
    data = await state.get_data()
    
    # Расчёт нормы воды с учётом погоды
    water_calc = calculate_water_goal(
        data["weight"], 
        data["activity_minutes"],
        weather["temp"]
    )
    
    # Расчёт нормы калорий
    calorie_calc = calculate_calorie_goal(
        data["weight"],
        data["height"],
        data["age"],
        data["gender"],
        data["activity_minutes"]
    )
    
    await state.update_data(
        water_goal=water_calc["total"],
        calorie_goal_calculated=calorie_calc["total"]
    )
    
    # Предлагаем установить свою цель калорий или использовать рассчитанную
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"✅ Использовать {int(calorie_calc['total'])} ккал", 
            callback_data="use_calculated_calories"
        )],
        [InlineKeyboardButton(
            text="✏️ Установить свою цель", 
            callback_data="set_custom_calories"
        )]
    ])
    
    await message.answer(
        f"✅ Город сохранён: {weather['city_name']}\n"
        f"🌡️ Текущая температура: {weather['temp']:.1f}°C ({weather['description']})\n\n"
        f"📊 <b>Рассчитанные нормы:</b>\n\n"
        f"💧 <b>Вода:</b> {water_calc['total']} мл/день\n"
        f"   • Базовая норма: {water_calc['base']} мл\n"
        f"   • За активность: +{water_calc['activity']} мл\n"
        f"   • За погоду: +{water_calc['weather']} мл\n\n"
        f"🔥 <b>Калории:</b> {int(calorie_calc['total'])} ккал/день\n"
        f"   • Базовый метаболизм: {int(calorie_calc['bmr'])} ккал\n"
        f"   • Уровень активности: {calorie_calc['activity_level']}\n\n"
        "Хотите использовать рассчитанную норму калорий или установить свою?",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "use_calculated_calories")
async def use_calculated_calories(callback: CallbackQuery, state: FSMContext):
    """Использовать рассчитанную норму калорий"""
    data = await state.get_data()
    
    # Сохраняем профиль в базу данных
    db.create_or_update_user(
        callback.from_user.id,
        weight=data["weight"],
        height=data["height"],
        age=data["age"],
        gender=data["gender"],
        activity_minutes=data["activity_minutes"],
        city=data["city"],
        calorie_goal=data["calorie_goal_calculated"]
    )
    
    await state.clear()
    
    await callback.message.edit_text(
        "🎉 <b>Профиль успешно сохранён!</b>\n\n"
        f"💧 Дневная норма воды: {data['water_goal']} мл\n"
        f"🔥 Дневная норма калорий: {int(data['calorie_goal_calculated'])} ккал\n\n"
        "Теперь вы можете:\n"
        "• /log_water — записать воду\n"
        "• /log_food — записать еду\n"
        "• /log_workout — записать тренировку\n"
        "• /check_progress — проверить прогресс",
        parse_mode="HTML"
    )
    await callback.answer("✅ Профиль сохранён!")


@router.callback_query(F.data == "set_custom_calories")
async def set_custom_calories(callback: CallbackQuery, state: FSMContext):
    """Установить свою цель калорий"""
    await state.set_state(ProfileStates.waiting_for_calorie_goal)
    await callback.message.edit_text(
        "✏️ Введите вашу <b>цель по калориям</b> (ккал/день):\n"
        "<i>Пример: 2000</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(ProfileStates.waiting_for_calorie_goal)
async def process_calorie_goal(message: Message, state: FSMContext):
    """Обработка пользовательской цели калорий"""
    try:
        calorie_goal = float(message.text)
        if calorie_goal < 800 or calorie_goal > 5000:
            await message.answer("❌ Введите реалистичное значение (от 800 до 5000 ккал)")
            return
        
        data = await state.get_data()
        
        # Сохраняем профиль в базу данных
        db.create_or_update_user(
            message.from_user.id,
            weight=data["weight"],
            height=data["height"],
            age=data["age"],
            gender=data["gender"],
            activity_minutes=data["activity_minutes"],
            city=data["city"],
            calorie_goal=calorie_goal
        )
        
        await state.clear()
        
        await message.answer(
            "🎉 <b>Профиль успешно сохранён!</b>\n\n"
            f"💧 Дневная норма воды: {data['water_goal']} мл\n"
            f"🔥 Дневная норма калорий: {int(calorie_goal)} ккал\n\n"
            "Теперь вы можете:\n"
            "• /log_water — записать воду\n"
            "• /log_food — записать еду\n"
            "• /log_workout — записать тренировку\n"
            "• /check_progress — проверить прогресс",
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число. Например: 2000")


@router.message(Command("my_profile"))
async def cmd_my_profile(message: Message):
    """Показать текущий профиль"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        await message.answer(
            "❌ Профиль не найден.\n\n"
            "Используйте /set_profile чтобы настроить профиль."
        )
        return
    
    # Получаем текущую погоду
    weather_info = ""
    if user.get("city"):
        weather = await get_weather(user["city"])
        if weather:
            weather_info = f"🌡️ Погода: {weather['temp']:.1f}°C ({weather['description']})\n"
    
    # Пересчитываем норму воды с учётом текущей погоды
    water_calc = calculate_water_goal(
        user["weight"],
        user["activity_minutes"],
        weather["temp"] if weather else None
    )
    
    gender_text = "👨 Мужской" if user.get("gender") == "male" else "👩 Женский"
    
    await message.answer(
        f"👤 <b>Ваш профиль:</b>\n\n"
        f"⚖️ Вес: {user['weight']} кг\n"
        f"📏 Рост: {user['height']} см\n"
        f"🎂 Возраст: {user['age']} лет\n"
        f"🚻 Пол: {gender_text}\n"
        f"🏃 Активность: {user['activity_minutes']} мин/день\n"
        f"📍 Город: {user.get('city', 'Не указан')}\n"
        f"{weather_info}\n"
        f"<b>Дневные нормы:</b>\n"
        f"💧 Вода: {water_calc['total']} мл\n"
        f"🔥 Калории: {int(user.get('calorie_goal', 0))} ккал\n\n"
        "📝 Чтобы изменить профиль: /set_profile",
        parse_mode="HTML"
    )



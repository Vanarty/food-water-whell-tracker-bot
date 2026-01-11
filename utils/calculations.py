"""
Модуль для расчёта норм воды и калорий
"""
from typing import Dict, Any, Optional


# Коэффициенты сжигания калорий для разных типов тренировок (ккал/мин на кг веса)
WORKOUT_CALORIES = {
    # Кардио
    "бег": 0.13,
    "бег трусцой": 0.10,
    "спринт": 0.18,
    "ходьба": 0.05,
    "быстрая ходьба": 0.07,
    "велосипед": 0.08,
    "велотренажер": 0.07,
    "плавание": 0.10,
    "прыжки": 0.12,
    "скакалка": 0.14,
    "танцы": 0.08,
    "аэробика": 0.09,
    "степ": 0.10,
    "эллипс": 0.08,
    "гребля": 0.09,
    
    # Силовые
    "силовая": 0.05,
    "тренажерный зал": 0.05,
    "качалка": 0.05,
    "штанга": 0.06,
    "гантели": 0.05,
    "кроссфит": 0.12,
    "воркаут": 0.08,
    "отжимания": 0.07,
    "приседания": 0.06,
    "планка": 0.04,
    
    # Спортивные игры
    "футбол": 0.10,
    "баскетбол": 0.09,
    "волейбол": 0.06,
    "теннис": 0.08,
    "бадминтон": 0.07,
    "хоккей": 0.10,
    "бокс": 0.12,
    "борьба": 0.11,
    
    # Другое
    "йога": 0.04,
    "пилатес": 0.04,
    "растяжка": 0.03,
    "медитация": 0.01,
}


def calculate_water_goal(weight: float, activity_minutes: int, 
                         temperature: Optional[float] = None) -> Dict[str, int]:
    """
    Рассчитать дневную норму воды
    
    Формула:
    - Базовая норма: вес × 30 мл/кг
    - + 500 мл за каждые 30 минут активности
    - + 500-1000 мл при жаркой погоде (> 25°C)
    
    Returns:
        Dict с breakdown расчёта
    """
    # Базовая норма
    base_water = weight * 30
    
    # Дополнительная вода за активность
    activity_water = (activity_minutes // 30) * 500
    
    # Дополнительная вода за погоду
    weather_water = 0
    if temperature:
        if temperature > 35:
            weather_water = 1000
        elif temperature > 30:
            weather_water = 750
        elif temperature > 25:
            weather_water = 500
    
    total = int(base_water + activity_water + weather_water)
    
    return {
        "base": int(base_water),
        "activity": activity_water,
        "weather": weather_water,
        "total": total
    }


def calculate_calorie_goal(weight: float, height: float, age: int, 
                           gender: str = "male", 
                           activity_minutes: int = 0) -> Dict[str, float]:
    """
    Рассчитать дневную норму калорий по формуле Миффлина-Сан Жеора
    
    Формула:
    Мужчины: BMR = 10 × вес + 6.25 × рост - 5 × возраст + 5
    Женщины: BMR = 10 × вес + 6.25 × рост - 5 × возраст - 161
    
    Множитель активности:
    - Минимальная активность (0-15 мин): 1.2
    - Лёгкая активность (15-30 мин): 1.375
    - Умеренная активность (30-60 мин): 1.55
    - Высокая активность (60-90 мин): 1.725
    - Очень высокая активность (>90 мин): 1.9
    
    Returns:
        Dict с breakdown расчёта
    """
    # Базовый метаболизм (BMR)
    if gender.lower() in ["male", "м", "мужской", "мужчина"]:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    # Коэффициент активности
    if activity_minutes < 15:
        activity_multiplier = 1.2
        activity_level = "минимальная"
    elif activity_minutes < 30:
        activity_multiplier = 1.375
        activity_level = "лёгкая"
    elif activity_minutes < 60:
        activity_multiplier = 1.55
        activity_level = "умеренная"
    elif activity_minutes < 90:
        activity_multiplier = 1.725
        activity_level = "высокая"
    else:
        activity_multiplier = 1.9
        activity_level = "очень высокая"
    
    total = bmr * activity_multiplier
    
    return {
        "bmr": round(bmr, 1),
        "activity_multiplier": activity_multiplier,
        "activity_level": activity_level,
        "total": round(total, 1)
    }


def calculate_workout_calories(workout_type: str, duration_minutes: int, 
                                weight: float) -> Dict[str, Any]:
    """
    Рассчитать сожжённые калории за тренировку
    
    Returns:
        Dict с типом тренировки, калориями и дополнительной водой
    """
    workout_lower = workout_type.lower().strip()
    
    # Ищем коэффициент для типа тренировки
    cal_per_min_per_kg = None
    matched_type = workout_type
    
    for key, value in WORKOUT_CALORIES.items():
        if key in workout_lower or workout_lower in key:
            cal_per_min_per_kg = value
            matched_type = key
            break
    
    # Если не нашли - используем среднее значение
    if cal_per_min_per_kg is None:
        cal_per_min_per_kg = 0.07  # Среднее значение
        matched_type = workout_type
    
    # Расчёт калорий
    calories_burned = cal_per_min_per_kg * duration_minutes * weight
    
    # Дополнительная вода: 200 мл за каждые 30 минут тренировки
    extra_water = (duration_minutes // 30 + (1 if duration_minutes % 30 > 0 else 0)) * 200
    
    # Эмодзи для типа тренировки
    emoji_map = {
        "бег": "🏃‍♂️",
        "ходьба": "🚶‍♂️",
        "велосипед": "🚴‍♂️",
        "плавание": "🏊‍♂️",
        "силовая": "🏋️‍♂️",
        "йога": "🧘‍♂️",
        "танцы": "💃",
        "футбол": "⚽",
        "баскетбол": "🏀",
        "теннис": "🎾",
        "бокс": "🥊",
    }
    
    emoji = "💪"
    for key, value in emoji_map.items():
        if key in workout_lower:
            emoji = value
            break
    
    return {
        "type": matched_type.capitalize(),
        "duration": duration_minutes,
        "calories_burned": round(calories_burned, 1),
        "extra_water": extra_water,
        "emoji": emoji
    }


def get_workout_recommendations(current_calories: float, goal_calories: float,
                                 burned_calories: float, weight: float) -> list:
    """
    Получить рекомендации по тренировкам для достижения баланса калорий
    """
    balance = current_calories - burned_calories
    excess = balance - goal_calories
    
    recommendations = []
    
    if excess > 0:
        # Нужно сжечь лишние калории
        workouts_to_suggest = [
            ("бег", "🏃‍♂️"),
            ("плавание", "🏊‍♂️"),
            ("велосипед", "🚴‍♂️"),
            ("скакалка", "⏱️"),
        ]
        
        for workout, emoji in workouts_to_suggest:
            cal_rate = WORKOUT_CALORIES.get(workout, 0.07)
            minutes_needed = excess / (cal_rate * weight)
            
            if minutes_needed <= 90:  # Реалистичное время тренировки
                recommendations.append({
                    "workout": workout.capitalize(),
                    "duration": round(minutes_needed),
                    "calories": round(excess),
                    "emoji": emoji
                })
    
    return recommendations[:3]  # Возвращаем топ-3 варианта



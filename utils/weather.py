"""
Модуль для получения данных о погоде через OpenWeatherMap API
"""
import aiohttp
from typing import Optional, Dict, Any
from config import WEATHER_API_KEY


async def get_weather(city: str) -> Optional[Dict[str, Any]]:
    """
    Получить данные о погоде для указанного города
    
    Returns:
        Dict с ключами: temp, feels_like, description, humidity
        или None если город не найден
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",  # Температура в Цельсиях
        "lang": "ru"  # Описание на русском
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "temp": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "description": data["weather"][0]["description"],
                        "humidity": data["main"]["humidity"],
                        "city_name": data["name"]
                    }
                elif response.status == 404:
                    return None
                else:
                    print(f"Ошибка API погоды: {response.status}")
                    return None
    except Exception as e:
        print(f"Ошибка при получении погоды: {e}")
        return None


def get_extra_water_for_weather(temperature: float) -> int:
    """
    Рассчитать дополнительную норму воды в зависимости от температуры
    
    > 25°C: +500 мл
    > 30°C: +750 мл
    > 35°C: +1000 мл
    """
    if temperature > 35:
        return 1000
    elif temperature > 30:
        return 750
    elif temperature > 25:
        return 500
    return 0



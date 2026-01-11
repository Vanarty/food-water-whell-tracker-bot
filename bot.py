import asyncio
import logging
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN
from handlers import all_routers


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """Middleware для логирования входящих сообщений"""
    
    async def __call__(self, handler, event, data):
        # Логируем информацию о сообщении
        if hasattr(event, 'from_user') and hasattr(event, 'text'):
            user = event.from_user
            logger.info(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"User: {user.id} (@{user.username or 'no_username'}) | "
                f"Message: {event.text[:100] if event.text else 'No text'}"
            )
        elif hasattr(event, 'from_user') and hasattr(event, 'data'):
            user = event.from_user
            logger.info(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"User: {user.id} (@{user.username or 'no_username'}) | "
                f"Callback: {event.data}"
            )
        
        return await handler(event, data)


async def set_bot_commands(bot: Bot):
    """Определение списка команд бота в меню"""
    commands = [
        BotCommand(command="start", description="🚀 Начать работу с ботом"),
        BotCommand(command="help", description="📚 Помощь по командам"),
        BotCommand(command="set_profile", description="👤 Настроить профиль"),
        BotCommand(command="my_profile", description="📋 Мой профиль"),
        BotCommand(command="log_water", description="💧 Записать воду"),
        BotCommand(command="log_food", description="🍎 Записать еду"),
        BotCommand(command="log_workout", description="🏃 Записать тренировку"),
        BotCommand(command="check_progress", description="📊 Проверить прогресс"),
        BotCommand(command="show_charts", description="📈 Графики за неделю"),
        BotCommand(command="recommendations", description="💡 Рекомендации"),
    ]
    await bot.set_my_commands(commands)


async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    logger.info("=" * 50)
    logger.info("🚀 Бот запускается...")
    await set_bot_commands(bot)
    logger.info("✅ Команды бота установлены")
    
    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"🤖 Бот: @{bot_info.username} (ID: {bot_info.id})")
    logger.info("=" * 50)
    logger.info("✅ Бот успешно запущен и готов к работе!")
    logger.info("=" * 50)


async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    logger.info("=" * 50)
    logger.info("🛑 Бот останавливается...")
    logger.info("=" * 50)


async def main():
    """Основная функция запуска бота"""
    # Создаём бота с настройками по умолчанию
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Создаём диспетчер с хранилищем состояний в памяти
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрируем middleware для логирования
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    # Регистрируем все роутеры
    for router in all_routers:
        dp.include_router(router)
    
    # Регистрируем обработчики startup и shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        # Удаляем webhook и запускаем polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🔄 Запуск polling...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise



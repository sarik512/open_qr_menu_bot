import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import config

# Настройка логирования из конфигурации
logging.basicConfig(
    format=config.LOG_FORMAT,
    level=getattr(logging, config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)


# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Асинхронный обработчик команды /start
    Отправляет приветственное сообщение с 4 инлайн кнопками
    """
    user = update.effective_user
    logger.info(f"Пользователь {user.id} ({user.username}) запустил команду /start")
    
    # Создаем инлайн клавиатуру из конфигурации
    keyboard = [
        [InlineKeyboardButton(btn["text"], url=btn["url"]) for btn in row]
        for row in config.BUTTONS
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Асинхронно отправляем сообщение с кнопками
    await update.message.reply_text(
        config.WELCOME_MESSAGE.format(first_name=user.first_name),
        reply_markup=reply_markup
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Асинхронный обработчик ошибок
    """
    logger.error(f"Произошла ошибка: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(config.ERROR_MESSAGE)


async def post_init(application: Application) -> None:
    """
    Функция, вызываемая после инициализации приложения
    """
    logger.info("🤖 Бот успешно инициализирован и готов к работе!")

async def post_shutdown(application: Application) -> None:
    """
    Функция, вызываемая при остановке приложения
    """
    logger.info("🛑 Бот остановлен")

async def main() -> None:
    """
    Главная асинхронная функция для запуска бота
    """
    if not BOT_TOKEN:
        logger.error("❌ Ошибка: BOT_TOKEN не найден в .env файле!")
        return
    
    # Создаем асинхронное приложение с оптимизированными настройками
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)  # Включаем параллельную обработку обновлений
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_error_handler(error_handler)
    
    # Запускаем бота асинхронно
    logger.info("🚀 Запуск бота...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True  # Игнорируем старые обновления при запуске
    )
    
    # Держим бота запущенным
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("⏹️ Получен сигнал остановки...")
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")

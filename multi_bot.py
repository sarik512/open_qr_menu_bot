"""
Главный файл для запуска мульти-организационного бота
Запускает отдельные экземпляры ботов для каждой организации
"""
import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.request import HTTPXRequest
from dotenv import load_dotenv
from database import Database
from admin_handlers import AdminHandlers, MAIN_MENU, ORG_MENU, ORG_CREATE_NAME, ORG_CREATE_TOKEN, ORG_CREATE_WELCOME, BUTTON_MENU, BUTTON_ADD_TEXT, BUTTON_ADD_URL, BUTTON_EDIT_SELECT, BUTTON_DELETE_SELECT
import config

# Настройка логирования
logging.basicConfig(
    format=config.LOG_FORMAT,
    level=getattr(logging, config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# ID главного админа (укажите свой Telegram ID)
ADMIN_TELEGRAM_ID = int(os.getenv('ADMIN_TELEGRAM_ID', '0'))

# База данных
db = Database()

class BotManager:
    """Менеджер для управления несколькими ботами"""
    
    def __init__(self):
        self.applications = {}  # {org_id: Application}
        self.admin_app = None
    
    async def start_user_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE, org_id: int) -> None:
        """
        Обработчик команды /start для обычных пользователей
        Показывает кнопки организации
        """
        user = update.effective_user
        org = db.get_organization_by_id(org_id)
        
        if not org:
            await update.message.reply_text("❌ Организация не найдена")
            return
        
        logger.info(f"Пользователь {user.id} ({user.username}) запустил бота организации '{org['name']}'")
        
        # Получаем кнопки организации
        buttons_data = db.get_buttons_for_organization(org_id)
        
        if not buttons_data:
            await update.message.reply_text(
                "⚠️ Кнопки еще не настроены. Обратитесь к администратору."
            )
            return
        
        # Группируем кнопки по рядам
        rows = {}
        for btn in buttons_data:
            row_num = btn['row_number']
            if row_num not in rows:
                rows[row_num] = []
            rows[row_num].append(btn)
        
        # Создаем клавиатуру
        keyboard = []
        for row_num in sorted(rows.keys()):
            row_buttons = sorted(rows[row_num], key=lambda x: x['position_in_row'])
            keyboard.append([
                InlineKeyboardButton(btn['button_text'], url=btn['button_url'])
                for btn in row_buttons
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Используем приветственное сообщение из БД или дефолтное
        welcome_msg = org.get('welcome_message') or config.WELCOME_MESSAGE
        
        await update.message.reply_text(
            welcome_msg.format(first_name=user.first_name),
            reply_markup=reply_markup
        )
    
    async def create_org_application(self, org: dict) -> Application:
        """Создать Application для организации"""
        org_id = org['id']
        bot_token = org['bot_token']
        
        # Настраиваем HTTPXRequest
        request_kwargs = {
            'connection_pool_size': 8,
            'connect_timeout': config.NETWORK_TIMEOUT['connect'],
            'read_timeout': config.NETWORK_TIMEOUT['read'],
            'write_timeout': config.NETWORK_TIMEOUT['write'],
            'pool_timeout': config.NETWORK_TIMEOUT['pool']
        }
        
        if config.PROXY_URL:
            request_kwargs['proxy'] = config.PROXY_URL
        
        request = HTTPXRequest(**request_kwargs)
        
        # Создаем Application
        application = (
            Application.builder()
            .token(bot_token)
            .request(request)
            .concurrent_updates(True)
            .build()
        )
        
        # Добавляем обработчик /start для этой организации
        async def start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await self.start_user_handler(update, context, org_id)
        
        application.add_handler(CommandHandler("start", start_wrapper))
        
        logger.info(f"✅ Создан бот для организации '{org['name']}' (ID: {org_id})")
        
        return application
    
    async def start_all_org_bots(self):
        """Запустить ботов для всех организаций"""
        organizations = db.get_all_organizations()
        
        if not organizations:
            logger.warning("⚠️ Нет активных организаций")
            return
        
        for org in organizations:
            try:
                app = await self.create_org_application(org)
                await app.initialize()
                await app.start()
                await app.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True
                )
                self.applications[org['id']] = app
                logger.info(f"🚀 Бот организации '{org['name']}' запущен")
            except Exception as e:
                logger.error(f"❌ Ошибка запуска бота для '{org['name']}': {e}")
    
    async def stop_all_org_bots(self):
        """Остановить всех ботов организаций"""
        for org_id, app in self.applications.items():
            try:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
                logger.info(f"🛑 Бот организации ID {org_id} остановлен")
            except Exception as e:
                logger.error(f"❌ Ошибка остановки бота ID {org_id}: {e}")
        
        self.applications.clear()
    
    async def setup_admin_bot(self):
        """Настроить админ-бота"""
        admin_token = os.getenv('ADMIN_BOT_TOKEN')
        
        if not admin_token:
            logger.error("❌ ADMIN_BOT_TOKEN не найден в .env файле!")
            return None
        
        # Добавляем админа в БД если его еще нет
        if ADMIN_TELEGRAM_ID:
            db.add_admin(ADMIN_TELEGRAM_ID)
        
        # Настраиваем HTTPXRequest
        request_kwargs = {
            'connection_pool_size': 8,
            'connect_timeout': config.NETWORK_TIMEOUT['connect'],
            'read_timeout': config.NETWORK_TIMEOUT['read'],
            'write_timeout': config.NETWORK_TIMEOUT['write'],
            'pool_timeout': config.NETWORK_TIMEOUT['pool']
        }
        
        if config.PROXY_URL:
            request_kwargs['proxy'] = config.PROXY_URL
        
        request = HTTPXRequest(**request_kwargs)
        
        # Создаем Application для админа
        application = (
            Application.builder()
            .token(admin_token)
            .request(request)
            .concurrent_updates(True)
            .build()
        )
        
        # Создаем обработчики админки
        admin_handlers = AdminHandlers(db, ADMIN_TELEGRAM_ID)
        
        # ConversationHandler для админ-панели
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", admin_handlers.admin_start)],
            states={
                MAIN_MENU: [
                    CallbackQueryHandler(admin_handlers.org_manage, pattern="^org_manage$"),
                    CallbackQueryHandler(admin_handlers.show_stats, pattern="^stats$"),
                ],
                ORG_MENU: [
                    CallbackQueryHandler(admin_handlers.org_create_start, pattern="^org_create$"),
                    CallbackQueryHandler(admin_handlers.org_create_skip_welcome, pattern="^org_create_skip_welcome$"),
                    CallbackQueryHandler(admin_handlers.org_view, pattern="^org_view_"),
                    CallbackQueryHandler(admin_handlers.org_delete, pattern="^org_delete_"),
                    CallbackQueryHandler(admin_handlers.button_manage_for_org, pattern="^org_buttons_"),
                    CallbackQueryHandler(admin_handlers.show_main_menu, pattern="^main_menu$"),
                    CallbackQueryHandler(admin_handlers.org_manage, pattern="^org_manage$"),
                ],
                ORG_CREATE_NAME: [
                    CallbackQueryHandler(admin_handlers.org_manage, pattern="^org_manage$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.org_create_name)
                ],
                ORG_CREATE_TOKEN: [
                    CallbackQueryHandler(admin_handlers.org_manage, pattern="^org_manage$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.org_create_token)
                ],
                ORG_CREATE_WELCOME: [
                    CallbackQueryHandler(admin_handlers.org_create_skip_welcome, pattern="^org_create_skip_welcome$"),
                    CallbackQueryHandler(admin_handlers.org_manage, pattern="^org_manage$"),
                    MessageHandler(filters.TEXT, admin_handlers.org_create_welcome)
                ],
                BUTTON_MENU: [
                    CallbackQueryHandler(admin_handlers.button_add_start, pattern="^btn_add_"),
                    CallbackQueryHandler(admin_handlers.button_edit_select, pattern="^btn_edit_"),
                    CallbackQueryHandler(admin_handlers.button_delete_select, pattern="^btn_delete_"),
                    CallbackQueryHandler(admin_handlers.org_view, pattern="^org_view_"),
                    CallbackQueryHandler(admin_handlers.button_manage_for_org, pattern="^org_buttons_"),
                    CallbackQueryHandler(admin_handlers.show_main_menu, pattern="^main_menu$"),
                ],
                BUTTON_ADD_TEXT: [
                    CallbackQueryHandler(admin_handlers.button_manage_for_org, pattern="^org_buttons_"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.button_add_text)
                ],
                BUTTON_ADD_URL: [
                    CallbackQueryHandler(admin_handlers.button_manage_for_org, pattern="^org_buttons_"),
                    CallbackQueryHandler(admin_handlers.show_main_menu, pattern="^main_menu$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.button_add_url)
                ],
                BUTTON_EDIT_SELECT: [
                    CallbackQueryHandler(admin_handlers.button_manage_for_org, pattern="^org_buttons_"),
                    CallbackQueryHandler(admin_handlers.show_main_menu, pattern="^main_menu$"),
                ],
                BUTTON_DELETE_SELECT: [
                    CallbackQueryHandler(admin_handlers.button_delete_confirm, pattern="^btn_delete_confirm_"),
                    CallbackQueryHandler(admin_handlers.button_manage_for_org, pattern="^org_buttons_"),
                    CallbackQueryHandler(admin_handlers.show_main_menu, pattern="^main_menu$"),
                ],
            },
            fallbacks=[CommandHandler("cancel", admin_handlers.cancel)],
        )
        
        application.add_handler(conv_handler)
        
        logger.info("✅ Админ-бот настроен")
        return application
    
    async def start_admin_bot(self):
        """Запустить админ-бота"""
        self.admin_app = await self.setup_admin_bot()
        
        if not self.admin_app:
            return
        
        try:
            await self.admin_app.initialize()
            await self.admin_app.start()
            await self.admin_app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            logger.info("🚀 Админ-бот запущен")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска админ-бота: {e}")
    
    async def stop_admin_bot(self):
        """Остановить админ-бота"""
        if self.admin_app:
            try:
                await self.admin_app.updater.stop()
                await self.admin_app.stop()
                await self.admin_app.shutdown()
                logger.info("🛑 Админ-бот остановлен")
            except Exception as e:
                logger.error(f"❌ Ошибка остановки админ-бота: {e}")

async def main():
    """Главная функция"""
    logger.info("🚀 Запуск системы мульти-организационных ботов...")
    
    manager = BotManager()
    
    try:
        # Запускаем админ-бота
        await manager.start_admin_bot()
        
        # Запускаем ботов для всех организаций
        await manager.start_all_org_bots()
        
        logger.info("✅ Все боты запущены и работают")
        
        # Держим ботов запущенными
        await asyncio.Event().wait()
        
    except (KeyboardInterrupt, SystemExit):
        logger.info("⏹️ Получен сигнал остановки...")
    finally:
        await manager.stop_admin_bot()
        await manager.stop_all_org_bots()
        logger.info("👋 Все боты остановлены")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Система остановлена пользователем")

"""
Обработчики команд для админ-панели
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import Database

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
(MAIN_MENU, 
 ORG_MENU, ORG_CREATE_NAME, ORG_CREATE_TOKEN, ORG_CREATE_WELCOME,
 BUTTON_MENU, BUTTON_ADD_TEXT, BUTTON_ADD_URL, BUTTON_EDIT_SELECT, BUTTON_EDIT_TEXT, BUTTON_EDIT_URL,
 BUTTON_DELETE_SELECT) = range(12)

class AdminHandlers:
    def __init__(self, db: Database, admin_id: int):
        self.db = db
        self.admin_id = admin_id
    
    async def admin_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Главное меню админ-панели"""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ У вас нет доступа к админ-панели")
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton("🏢 Управление организациями", callback_data="org_manage")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🔐 <b>Админ-панель</b>\n\nВыберите действие:"
        
        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        
        return MAIN_MENU
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показать главное меню (для callback)"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🏢 Управление организациями", callback_data="org_manage")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🔐 <b>Админ-панель</b>\n\nВыберите действие:"
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        
        return MAIN_MENU
    
    async def org_manage(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Меню управления организациями"""
        query = update.callback_query
        await query.answer()
        
        organizations = self.db.get_all_organizations()
        
        keyboard = []
        for org in organizations:
            keyboard.append([InlineKeyboardButton(
                f"📁 {org['name']}", 
                callback_data=f"org_view_{org['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("➕ Создать организацию", callback_data="org_create")])
        keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🏢 <b>Управление организациями</b>\n\n"
        if organizations:
            text += f"Всего организаций: {len(organizations)}\n\nВыберите организацию для просмотра:"
        else:
            text += "Организаций пока нет. Создайте первую!"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ORG_MENU
    
    async def org_create_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало создания организации"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="org_manage")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➕ <b>Создание новой организации</b>\n\n"
            "Шаг 1/3: Введите название организации:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return ORG_CREATE_NAME
    
    async def org_create_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение названия организации"""
        name = update.message.text.strip()
        context.user_data['new_org_name'] = name
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="org_manage")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Название: <b>{name}</b>\n\n"
            f"Шаг 2/3: Введите токен бота для этой организации:\n"
            f"(Получите токен у @BotFather)",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return ORG_CREATE_TOKEN
    
    async def org_create_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение токена бота"""
        token = update.message.text.strip()
        context.user_data['new_org_token'] = token
        
        keyboard = [
            [InlineKeyboardButton("⏭️ Пропустить", callback_data="org_create_skip_welcome")],
            [InlineKeyboardButton("❌ Отмена", callback_data="org_manage")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Токен получен\n\n"
            f"Шаг 3/3: Введите приветственное сообщение для пользователей:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return ORG_CREATE_WELCOME
    
    async def org_create_skip_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Пропустить приветственное сообщение"""
        query = update.callback_query
        await query.answer()
        
        name = context.user_data.get('new_org_name')
        token = context.user_data.get('new_org_token')
        
        org_id = self.db.add_organization(name, token, None)
        
        if org_id:
            keyboard = [
                [InlineKeyboardButton("🔘 Добавить кнопки", callback_data=f"org_buttons_{org_id}")],
                [InlineKeyboardButton("◀️ К организациям", callback_data="org_manage")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ <b>Организация создана!</b>\n\n"
                f"📁 Название: {name}\n"
                f"🆔 ID: {org_id}\n"
                f"🤖 Токен: {token[:20]}...\n\n"
                f"Теперь вы можете добавить кнопки для этой организации.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="org_manage")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ Ошибка создания организации. Возможно, такое название или токен уже существует.",
                reply_markup=reply_markup
            )
        
        # Очистка данных
        context.user_data.clear()
        return ORG_MENU
    
    async def org_create_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение приветственного сообщения и создание организации"""
        welcome_msg = update.message.text.strip()
        
        name = context.user_data.get('new_org_name')
        token = context.user_data.get('new_org_token')
        
        org_id = self.db.add_organization(name, token, welcome_msg)
        
        keyboard = [
            [InlineKeyboardButton("🔘 Добавить кнопки", callback_data=f"org_buttons_{org_id}")],
            [InlineKeyboardButton("◀️ К организациям", callback_data="org_manage")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if org_id:
            await update.message.reply_text(
                f"✅ <b>Организация создана!</b>\n\n"
                f"📁 Название: {name}\n"
                f"🆔 ID: {org_id}\n"
                f"🤖 Токен: {token[:20]}...\n\n"
                f"Теперь вы можете добавить кнопки для этой организации.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="org_manage")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ Ошибка создания организации. Возможно, такое название или токен уже существует.",
                reply_markup=reply_markup
            )
        
        # Очистка данных
        context.user_data.clear()
        return ORG_MENU
    
    async def org_view(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Просмотр информации об организации"""
        query = update.callback_query
        await query.answer()
        
        org_id = int(query.data.split('_')[2])
        org = self.db.get_organization_by_id(org_id)
        
        if not org:
            await query.edit_message_text("❌ Организация не найдена")
            return await self.org_manage(update, context)
        
        buttons = self.db.get_buttons_for_organization(org_id)
        
        text = (
            f"📁 <b>{org['name']}</b>\n\n"
            f"🆔 ID: {org['id']}\n"
            f"🤖 Токен: {org['bot_token'][:20]}...\n"
            f"🔘 Кнопок: {len(buttons)}\n"
            f"📅 Создана: {org['created_at']}\n\n"
        )
        
        if org['welcome_message']:
            text += f"💬 Приветствие:\n{org['welcome_message'][:100]}...\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔘 Управление кнопками", callback_data=f"org_buttons_{org_id}")],
            [InlineKeyboardButton("🗑 Удалить организацию", callback_data=f"org_delete_{org_id}")],
            [InlineKeyboardButton("◀️ К организациям", callback_data="org_manage")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ORG_MENU
    
    async def org_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Удаление организации"""
        query = update.callback_query
        await query.answer()
        
        org_id = int(query.data.split('_')[2])
        org = self.db.get_organization_by_id(org_id)
        
        if org and self.db.delete_organization(org_id):
            await query.answer("✅ Организация удалена", show_alert=True)
            return await self.org_manage(update, context)
        else:
            await query.answer("❌ Ошибка удаления", show_alert=True)
            return ORG_MENU
    
    async def button_manage_for_org(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Управление кнопками для конкретной организации"""
        query = update.callback_query
        await query.answer()
        
        org_id = int(query.data.split('_')[2])
        context.user_data['current_org_id'] = org_id
        
        org = self.db.get_organization_by_id(org_id)
        buttons = self.db.get_buttons_for_organization(org_id)
        
        text = f"🔘 <b>Кнопки организации: {org['name']}</b>\n\n"
        
        if buttons:
            text += "Текущие кнопки:\n\n"
            for btn in buttons:
                text += f"• {btn['button_text']} → {btn['button_url'][:30]}...\n"
        else:
            text += "Кнопок пока нет.\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Добавить кнопку", callback_data=f"btn_add_{org_id}")],
        ]
        
        if buttons:
            keyboard.append([InlineKeyboardButton("✏️ Редактировать кнопку", callback_data=f"btn_edit_{org_id}")])
            keyboard.append([InlineKeyboardButton("🗑 Удалить кнопку", callback_data=f"btn_delete_{org_id}")])
        
        keyboard.append([InlineKeyboardButton("◀️ К организации", callback_data=f"org_view_{org_id}")])
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return BUTTON_MENU
    
    async def button_add_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало добавления кнопки"""
        query = update.callback_query
        await query.answer()
        
        org_id = int(query.data.split('_')[2])
        context.user_data['current_org_id'] = org_id
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data=f"org_buttons_{org_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➕ <b>Добавление новой кнопки</b>\n\n"
            "Шаг 1/2: Введите текст кнопки:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return BUTTON_ADD_TEXT
    
    async def button_add_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение текста кнопки"""
        text = update.message.text.strip()
        context.user_data['new_button_text'] = text
        
        org_id = context.user_data.get('current_org_id')
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data=f"org_buttons_{org_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Текст кнопки: <b>{text}</b>\n\n"
            f"Шаг 2/2: Введите URL (ссылку) для кнопки:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return BUTTON_ADD_URL
    
    async def button_add_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение URL и создание кнопки"""
        url = update.message.text.strip()
        text = context.user_data.get('new_button_text')
        org_id = context.user_data.get('current_org_id')
        
        # Получаем текущее количество кнопок для определения позиции
        buttons = self.db.get_buttons_for_organization(org_id)
        row = len(buttons) // 2  # По 2 кнопки в ряд
        position = len(buttons) % 2
        
        button_id = self.db.add_button(org_id, text, url, row, position)
        
        keyboard = [
            [InlineKeyboardButton("➕ Добавить еще кнопку", callback_data=f"btn_add_{org_id}")],
            [InlineKeyboardButton("◀️ К кнопкам", callback_data=f"org_buttons_{org_id}")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if button_id:
            await update.message.reply_text(
                f"✅ <b>Кнопка добавлена!</b>\n\n"
                f"📝 Текст: {text}\n"
                f"🔗 URL: {url}",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка добавления кнопки",
                reply_markup=reply_markup
            )
        
        # Очистка данных
        context.user_data.pop('new_button_text', None)
        
        return BUTTON_MENU
    
    async def button_edit_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Выбор кнопки для редактирования"""
        query = update.callback_query
        await query.answer()
        
        org_id = int(query.data.split('_')[2])
        buttons = self.db.get_buttons_for_organization(org_id)
        
        keyboard = []
        for btn in buttons:
            keyboard.append([InlineKeyboardButton(
                f"{btn['button_text']}", 
                callback_data=f"btn_edit_selected_{btn['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"org_buttons_{org_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "✏️ Выберите кнопку для редактирования:",
            reply_markup=reply_markup
        )
        return BUTTON_EDIT_SELECT
    
    async def button_delete_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Выбор кнопки для удаления"""
        query = update.callback_query
        await query.answer()
        
        org_id = int(query.data.split('_')[2])
        buttons = self.db.get_buttons_for_organization(org_id)
        
        keyboard = []
        for btn in buttons:
            keyboard.append([InlineKeyboardButton(
                f"🗑 {btn['button_text']}", 
                callback_data=f"btn_delete_confirm_{btn['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"org_buttons_{org_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🗑 Выберите кнопку для удаления:",
            reply_markup=reply_markup
        )
        return BUTTON_DELETE_SELECT
    
    async def button_delete_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Подтверждение удаления кнопки"""
        query = update.callback_query
        await query.answer()
        
        button_id = int(query.data.split('_')[3])
        button = self.db.get_button_by_id(button_id)
        
        if button and self.db.delete_button(button_id):
            await query.answer("✅ Кнопка удалена", show_alert=True)
            org_id = button['organization_id']
            context.user_data['current_org_id'] = org_id
            
            # Создаем фейковый callback_data для перехода
            class FakeQuery:
                def __init__(self, data):
                    self.data = data
            
            update.callback_query.data = f"org_buttons_{org_id}"
            return await self.button_manage_for_org(update, context)
        else:
            await query.answer("❌ Ошибка удаления", show_alert=True)
            return BUTTON_MENU
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показать статистику"""
        query = update.callback_query
        await query.answer()
        
        organizations = self.db.get_all_organizations()
        total_buttons = 0
        
        for org in organizations:
            buttons = self.db.get_buttons_for_organization(org['id'])
            total_buttons += len(buttons)
        
        text = (
            "📊 <b>Статистика</b>\n\n"
            f"🏢 Организаций: {len(organizations)}\n"
            f"🔘 Всего кнопок: {total_buttons}\n"
        )
        
        keyboard = [[InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return MAIN_MENU
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена операции"""
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ Операция отменена",
            reply_markup=reply_markup
        )
        context.user_data.clear()
        return MAIN_MENU

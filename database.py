"""
Модуль для работы с базой данных
Управление организациями и кнопками
"""
import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для работы с подключением к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка БД: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Инициализация базы данных"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица организаций
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    bot_token TEXT NOT NULL UNIQUE,
                    welcome_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Таблица кнопок
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS buttons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_id INTEGER NOT NULL,
                    button_text TEXT NOT NULL,
                    button_url TEXT NOT NULL,
                    row_number INTEGER DEFAULT 0,
                    position_in_row INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
                )
            """)
            
            # Таблица админов (для хранения ID главного админа)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL UNIQUE,
                    username TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("✅ База данных инициализирована")
    
    # === Методы для работы с админами ===
    
    def add_admin(self, telegram_id: int, username: str = None) -> bool:
        """Добавить главного админа"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO admins (telegram_id, username) VALUES (?, ?)",
                    (telegram_id, username)
                )
                logger.info(f"✅ Админ {telegram_id} добавлен")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Админ {telegram_id} уже существует")
            return False
    
    def is_admin(self, telegram_id: int) -> bool:
        """Проверить, является ли пользователь админом"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM admins WHERE telegram_id = ?", (telegram_id,))
            return cursor.fetchone() is not None
    
    def get_all_admins(self) -> List[Dict]:
        """Получить список всех админов"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT telegram_id, username, created_at FROM admins")
            return [dict(row) for row in cursor.fetchall()]
    
    # === Методы для работы с организациями ===
    
    def add_organization(self, name: str, bot_token: str, welcome_message: str = None) -> Optional[int]:
        """Добавить новую организацию"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO organizations (name, bot_token, welcome_message) VALUES (?, ?, ?)",
                    (name, bot_token, welcome_message)
                )
                org_id = cursor.lastrowid
                logger.info(f"✅ Организация '{name}' добавлена (ID: {org_id})")
                return org_id
        except sqlite3.IntegrityError as e:
            logger.error(f"❌ Ошибка добавления организации: {e}")
            return None
    
    def get_organization_by_token(self, bot_token: str) -> Optional[Dict]:
        """Получить организацию по токену бота"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM organizations WHERE bot_token = ? AND is_active = 1",
                (bot_token,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_organization_by_id(self, org_id: int) -> Optional[Dict]:
        """Получить организацию по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM organizations WHERE id = ?", (org_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_organizations(self) -> List[Dict]:
        """Получить список всех организаций"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM organizations WHERE is_active = 1 ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_organization(self, org_id: int, name: str = None, welcome_message: str = None) -> bool:
        """Обновить данные организации"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if name:
                    cursor.execute("UPDATE organizations SET name = ? WHERE id = ?", (name, org_id))
                if welcome_message is not None:
                    cursor.execute("UPDATE organizations SET welcome_message = ? WHERE id = ?", (welcome_message, org_id))
                logger.info(f"✅ Организация {org_id} обновлена")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка обновления организации: {e}")
            return False
    
    def delete_organization(self, org_id: int) -> bool:
        """Удалить организацию (мягкое удаление)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE organizations SET is_active = 0 WHERE id = ?", (org_id,))
                logger.info(f"✅ Организация {org_id} деактивирована")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления организации: {e}")
            return False
    
    # === Методы для работы с кнопками ===
    
    def add_button(self, org_id: int, text: str, url: str, row: int = 0, position: int = 0) -> Optional[int]:
        """Добавить кнопку для организации"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO buttons (organization_id, button_text, button_url, row_number, position_in_row)
                       VALUES (?, ?, ?, ?, ?)""",
                    (org_id, text, url, row, position)
                )
                button_id = cursor.lastrowid
                logger.info(f"✅ Кнопка '{text}' добавлена для организации {org_id}")
                return button_id
        except Exception as e:
            logger.error(f"❌ Ошибка добавления кнопки: {e}")
            return None
    
    def get_buttons_for_organization(self, org_id: int) -> List[Dict]:
        """Получить все кнопки организации"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM buttons 
                   WHERE organization_id = ? 
                   ORDER BY row_number, position_in_row""",
                (org_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_button_by_id(self, button_id: int) -> Optional[Dict]:
        """Получить кнопку по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM buttons WHERE id = ?", (button_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_button(self, button_id: int, text: str = None, url: str = None) -> bool:
        """Обновить кнопку"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if text:
                    cursor.execute("UPDATE buttons SET button_text = ? WHERE id = ?", (text, button_id))
                if url:
                    cursor.execute("UPDATE buttons SET button_url = ? WHERE id = ?", (url, button_id))
                logger.info(f"✅ Кнопка {button_id} обновлена")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка обновления кнопки: {e}")
            return False
    
    def delete_button(self, button_id: int) -> bool:
        """Удалить кнопку"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM buttons WHERE id = ?", (button_id,))
                logger.info(f"✅ Кнопка {button_id} удалена")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления кнопки: {e}")
            return False
    
    def reorder_buttons(self, button_positions: List[Tuple[int, int, int]]) -> bool:
        """
        Изменить порядок кнопок
        button_positions: список кортежей (button_id, row_number, position_in_row)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for button_id, row, position in button_positions:
                    cursor.execute(
                        "UPDATE buttons SET row_number = ?, position_in_row = ? WHERE id = ?",
                        (row, position, button_id)
                    )
                logger.info(f"✅ Порядок кнопок обновлен")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка изменения порядка кнопок: {e}")
            return False

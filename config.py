"""
Конфигурация для бота
Здесь вы можете настроить кнопки и сообщения
"""

# Текст приветственного сообщения
WELCOME_MESSAGE = "👋 Добро пожаловать в New York Burger!\n\nВыберите ближайший наш филиал:\n\n\n👋 New York Burger’ga xush kelibsiz!\n\n eng yaqin filialimizni tanlang:"

# Конфигурация кнопок
# Формат: [{"text": "Текст кнопки", "url": "https://ссылка"}]
BUTTONS = [
    # Первый ряд кнопок
    [
        {"text": "Family Park", "url": "https://qr.alipos.uz/new-york-burger-family-park"},
        {"text": "Sibirskiy", "url": "https://qr.alipos.uz/new-york-burger-sibirskiy"},
    ],
    # Второй ряд кнопок
    [
        {"text": "Makon mall", "url": "https://qr.alipos.uz/new-york-burger-makon-mall"},
        {"text": "Toyloq", "url": "https://qr.alipos.uz/new-york-burger-toyloq"},
    ]
]

# Сообщение об ошибке
ERROR_MESSAGE = "😔 Произошла ошибка при обработке вашего запроса. Попробуйте позже."

# Настройки логирования
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL

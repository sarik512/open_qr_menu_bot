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

# Настройки сети
NETWORK_TIMEOUT = {
    'connect': 10.0,  # Таймаут на установку соединения (секунды)
    'read': 20.0,     # Таймаут на чтение ответа (секунды)
    'write': 20.0,    # Таймаут на запись запроса (секунды)
    'pool': 10.0      # Таймаут на получение соединения из пула (секунды)
}

# Настройки повторных попыток при ошибках сети
MAX_RETRIES = 3           # Максимальное количество попыток подключения
RETRY_DELAY = 5           # Начальная задержка между попытками (секунды)

# Настройки прокси (опционально)
# Раскомментируйте и настройте, если Telegram заблокирован в вашем регионе
# PROXY_URL = "http://proxy_address:proxy_port"
# PROXY_URL = "socks5://proxy_address:proxy_port"
PROXY_URL = None  # Оставьте None, если прокси не нужен

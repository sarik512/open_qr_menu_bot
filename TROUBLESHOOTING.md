# 🔧 Руководство по устранению неполадок / Troubleshooting Guide

## Проблема: Timeout при запуске бота

### Симптомы
```
telegram.error.TimedOut: Timed out
httpcore.ReadTimeout
```

### Причины
1. **Медленное интернет-соединение** - Сервер не может быстро подключиться к Telegram API
2. **Блокировка Telegram** - В некоторых регионах доступ к Telegram API может быть ограничен
3. **Проблемы с DNS** - Неправильная настройка DNS может замедлять подключение
4. **Перегрузка сети** - Высокая нагрузка на сетевое соединение

### Решения

#### 1. Увеличение таймаутов (уже реализовано)
Бот теперь использует увеличенные таймауты из файла `config.py`:
```python
NETWORK_TIMEOUT = {
    'connect': 10.0,  # Таймаут на установку соединения
    'read': 20.0,     # Таймаут на чтение ответа
    'write': 20.0,    # Таймаут на запись запроса
    'pool': 10.0      # Таймаут на получение соединения из пула
}
```

Вы можете увеличить эти значения, если проблема сохраняется.

#### 2. Использование прокси
Если Telegram заблокирован в вашем регионе, настройте прокси в `config.py`:

```python
# HTTP прокси
PROXY_URL = "http://proxy_address:proxy_port"

# SOCKS5 прокси
PROXY_URL = "socks5://proxy_address:proxy_port"
```

#### 3. Проверка интернет-соединения
```bash
# Проверка доступности Telegram API
ping api.telegram.org

# Проверка DNS
nslookup api.telegram.org
```

#### 4. Использование VPN
Если прокси не помогает, попробуйте использовать VPN для обхода блокировок.

#### 5. Увеличение количества попыток
В `config.py` можно увеличить количество попыток подключения:
```python
MAX_RETRIES = 5      # Увеличить с 3 до 5
RETRY_DELAY = 10     # Увеличить задержку с 5 до 10 секунд
```

## Проблема: Конфликт обновлений (409 Conflict)

### Симптомы
```
telegram.error.Conflict: Conflict: terminated by other getUpdates request
```

### Причины
Другой экземпляр бота уже запущен и получает обновления.

### Решения
1. Остановите все запущенные экземпляры бота:
```bash
# Linux
ps aux | grep bot.py
kill <PID>

# Windows
tasklist | findstr python
taskkill /F /PID <PID>
```

2. Используйте webhook вместо polling (для продакшена)

## Проблема: Неверный токен

### Симптомы
```
telegram.error.InvalidToken: Invalid token
```

### Решения
1. Проверьте файл `.env`:
```bash
cat .env
```

2. Убедитесь, что токен правильный (получите новый от @BotFather)

3. Проверьте, что нет лишних пробелов:
```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

## Дополнительные советы

### Логирование
Для более подробной информации включите DEBUG режим в `config.py`:
```python
LOG_LEVEL = 'DEBUG'
```

### Мониторинг
Используйте `systemd` (Linux) или `nssm` (Windows) для автоматического перезапуска бота при сбоях.

### Тестирование соединения
Создайте простой тест-скрипт:
```python
import asyncio
from telegram import Bot

async def test():
    bot = Bot(token="YOUR_TOKEN")
    me = await bot.get_me()
    print(f"Бот работает: @{me.username}")

asyncio.run(test())
```

## Контакты для поддержки
Если проблема не решена, проверьте:
- [Telegram Bot API Status](https://core.telegram.org/bots/api)
- [python-telegram-bot GitHub Issues](https://github.com/python-telegram-bot/python-telegram-bot/issues)

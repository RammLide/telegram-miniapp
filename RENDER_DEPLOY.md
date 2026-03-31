# 🚀 Деплой бота на Render

## Вариант 1: Только Web App (текущий)

Сейчас на Render развернут только веб-сервер для Mini App.

**Procfile:**
```
web: python web_app_only.py
```

## Вариант 2: Полный бот + Web App (рекомендуется)

Чтобы развернуть полного бота с админ-панелью на Render:

### Шаг 1: Создайте новый файл start.sh

```bash
#!/bin/bash
python main.py
```

### Шаг 2: Измените Procfile

```
web: python main.py
```

### Шаг 3: Настройте переменные окружения на Render

1. Зайдите на https://dashboard.render.com
2. Выберите ваш сервис
3. Перейдите в **Environment**
4. Добавьте переменные:
   - `BOT_TOKEN` = ваш токен от BotFather
   - `ADMIN_ID` = ваш Telegram ID (например: 1121167993)

### Шаг 4: Обновите main.py для работы на Render

Нужно изменить порт и убрать прокси:

```python
# В main.py найдите строку с портом и измените на:
PORT = int(os.getenv('PORT', 8080))

# И в функции start_web_server:
site = web.TCPSite(runner, '0.0.0.0', PORT)
```

### Шаг 5: Обновите WEBAPP_URL в keyboards.py

```python
WEBAPP_URL = "https://ваш-домен.onrender.com/webapp/index.html"
```

## Вариант 3: Два отдельных сервиса (лучший вариант)

### Сервис 1: Web App (уже есть)
- Репозиторий: https://github.com/RammLide/telegram-miniapp.git
- Procfile: `web: python web_app_only.py`
- URL: https://telegram-miniapp-h5ei.onrender.com

### Сервис 2: Telegram Bot (новый)
1. Создайте новый Web Service на Render
2. Подключите тот же репозиторий
3. Настройте:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Environment Variables:**
     - `BOT_TOKEN` = ваш токен
     - `ADMIN_ID` = ваш ID
     - `PORT` = 8080

## Рекомендация

Используйте **Вариант 3** (два отдельных сервиса):
- ✅ Web App работает независимо
- ✅ Бот работает независимо
- ✅ Если один упадет, второй продолжит работать
- ✅ Легче масштабировать

## Текущая настройка

Сейчас у вас:
- ✅ Web App на Render: https://telegram-miniapp-h5ei.onrender.com
- ❌ Бот работает локально

Чтобы бот тоже работал на Render, следуйте инструкциям выше.

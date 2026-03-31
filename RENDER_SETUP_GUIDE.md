# 📝 Пошаговая инструкция: Деплой бота на Render

## 🎯 Цель
Развернуть Telegram бота на Render, чтобы он работал 24/7 без необходимости держать компьютер включенным.

## 📋 Что у вас уже есть
- ✅ Web App на Render: https://telegram-miniapp-h5ei.onrender.com
- ✅ Код на GitHub: https://github.com/RammLide/telegram-miniapp.git
- ❌ Бот работает только локально (нужно исправить)

## 🚀 Вариант 1: Один сервис (Бот + Web App вместе)

### Шаг 1: Обновите Procfile
Измените файл `Procfile`:
```
web: python main.py
```

### Шаг 2: Настройте переменные окружения на Render
1. Зайдите на https://dashboard.render.com
2. Найдите ваш сервис `telegram-miniapp`
3. Перейдите в **Environment** (слева в меню)
4. Нажмите **Add Environment Variable**
5. Добавьте:
   - **Key:** `BOT_TOKEN`
   - **Value:** `5739651381:AAFxltHlWYOR-Z4rymbZ4Fnlr1l26ypnGPo`
6. Добавьте еще одну:
   - **Key:** `ADMIN_ID`
   - **Value:** `1121167993`
7. Нажмите **Save Changes**

### Шаг 3: Обновите WEBAPP_URL
В файле `keyboards.py` измените:
```python
WEBAPP_URL = "https://telegram-miniapp-h5ei.onrender.com/webapp/index.html"
```

### Шаг 4: Закоммитьте и запушьте изменения
```bash
git add .
git commit -m "Configure for Render deployment"
git push origin main
```

### Шаг 5: Дождитесь деплоя
Render автоматически подхватит изменения и перезапустит сервис (1-2 минуты).

### ✅ Готово!
Теперь бот работает на Render 24/7!

---

## 🚀 Вариант 2: Два отдельных сервиса (РЕКОМЕНДУЕТСЯ)

Этот вариант лучше, потому что:
- Web App и бот работают независимо
- Если один упадет, второй продолжит работать
- Легче масштабировать и отлаживать

### Сервис 1: Web App (уже настроен)
- URL: https://telegram-miniapp-h5ei.onrender.com
- Procfile: `web: python web_app_only.py`
- Статус: ✅ Работает

### Сервис 2: Telegram Bot (нужно создать)

#### Шаг 1: Создайте новый Web Service на Render
1. Зайдите на https://dashboard.render.com
2. Нажмите **New +** → **Web Service**
3. Подключите репозиторий: `https://github.com/RammLide/telegram-miniapp.git`
4. Настройте:
   - **Name:** `telegram-bot-hamster`
   - **Region:** выберите ближайший к вам
   - **Branch:** `main`
   - **Root Directory:** оставьте пустым
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot_only.py`

#### Шаг 2: Настройте переменные окружения
В разделе **Environment Variables** добавьте:
- `BOT_TOKEN` = `5739651381:AAFxltHlWYOR-Z4rymbZ4Fnlr1l26ypnGPo`
- `ADMIN_ID` = `1121167993`

#### Шаг 3: Выберите план
- **Free** (бесплатно, но засыпает после 15 минут неактивности)
- **Starter** ($7/месяц, работает 24/7)

#### Шаг 4: Нажмите Create Web Service

#### Шаг 5: Дождитесь деплоя
Render установит зависимости и запустит бота (2-3 минуты).

### ✅ Готово!
Теперь у вас:
- Web App: https://telegram-miniapp-h5ei.onrender.com
- Bot: работает на отдельном сервисе

---

## 🔧 Важные настройки

### 1. Убрать прокси из main.py
Если в `main.py` есть настройки прокси, закомментируйте их:

```python
# PROXY_URL = "socks5://127.0.0.1:10809"  # Закомментируйте
# try:
#     connector = ProxyConnector.from_url(PROXY_URL)
#     session = ClientSession(connector=connector)
#     bot = Bot(token=BOT_TOKEN, session=session)
# except:
bot = Bot(token=BOT_TOKEN)  # Используйте без прокси
```

### 2. Проверить WEBAPP_URL
В `keyboards.py` должен быть правильный URL:
```python
WEBAPP_URL = "https://telegram-miniapp-h5ei.onrender.com/webapp/index.html"
```

### 3. Проверить requirements.txt
Убедитесь, что все зависимости указаны:
```
aiogram==3.26.0
python-dotenv==1.2.2
aiosqlite==0.22.1
aiohttp==3.13.3
```

---

## 🐛 Решение проблем

### Проблема: Бот не отвечает
**Решение:**
1. Проверьте логи на Render (вкладка **Logs**)
2. Убедитесь, что BOT_TOKEN правильный
3. Проверьте, что сервис запущен (статус **Live**)

### Проблема: Web App не открывается
**Решение:**
1. Проверьте, что WEBAPP_URL использует HTTPS
2. Убедитесь, что Web App сервис запущен
3. Проверьте URL в keyboards.py

### Проблема: "This site can't be reached"
**Решение:**
1. Дождитесь завершения деплоя (2-3 минуты)
2. Проверьте статус сервиса на Render
3. Попробуйте перезапустить сервис (Manual Deploy)

### Проблема: Бот засыпает (Free план)
**Решение:**
1. Используйте платный план Starter ($7/месяц)
2. Или используйте сервис для пинга (например, UptimeRobot)

---

## 📊 Проверка работы

### 1. Проверьте логи на Render
```
Logs → должны быть сообщения:
✅ База данных инициализирована
✅ 🤖 Бот запущен и готов к работе!
✅ 🌐 Веб-сервер запущен на порту 8080
```

### 2. Проверьте бота в Telegram
1. Откройте бота
2. Напишите /start
3. Должно прийти приветствие
4. Нажмите "🎁 Открыть кейсы"
5. Должно открыться Mini App

### 3. Проверьте админ-панель
1. Напишите /admin
2. Должна открыться админ-панель
3. Проверьте статистику
4. Попробуйте рассылку

---

## 💡 Рекомендации

1. **Используйте Вариант 2** (два отдельных сервиса) - надежнее
2. **Включите автоматический деплой** на Render при пуше в GitHub
3. **Настройте уведомления** о падении сервиса
4. **Регулярно проверяйте логи** на наличие ошибок
5. **Делайте бэкапы базы данных** (bot_users.db)

---

## 🎯 Следующие шаги

После успешного деплоя:
1. ✅ Проверьте работу бота
2. ✅ Проверьте работу Mini App
3. ✅ Проверьте админ-панель
4. ✅ Проверьте рассылку
5. ✅ Проверьте сохранение прогресса

---

**Дата:** 31.03.2026  
**Версия:** 3.1  
**Репозиторий:** https://github.com/RammLide/telegram-miniapp.git

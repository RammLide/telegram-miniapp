# Инструкция по запуску Mini App локально

## Шаг 1: Установка ngrok

1. Скачайте ngrok с https://ngrok.com/download
2. Распакуйте и добавьте в PATH (или запускайте из папки)

## Шаг 2: Запуск бота

1. Откройте первый терминал и запустите бота:
```bash
python main.py
```

Бот запустится и веб-сервер будет доступен на http://localhost:8080

## Шаг 3: Запуск ngrok

2. Откройте второй терминал и запустите ngrok:
```bash
ngrok http 8080
```

Вы увидите что-то вроде:
```
Forwarding  https://1234-5678-90ab-cdef.ngrok-free.app -> http://localhost:8080
```

## Шаг 4: Обновление URL

3. Скопируйте HTTPS URL из ngrok (например: https://1234-5678-90ab-cdef.ngrok-free.app)

4. Откройте файл `keyboards.py` и замените строку 6:
```python
WEBAPP_URL = "https://1234-5678-90ab-cdef.ngrok-free.app/webapp/index.html"
```

5. Перезапустите бота (Ctrl+C и снова `python main.py`)

## Шаг 5: Тестирование

6. Откройте бота в Telegram
7. Нажмите кнопку "🎁 Открыть кейсы"
8. Mini App должно открыться!

## Альтернатива: Без ngrok (только для тестирования UI)

Если хотите просто посмотреть интерфейс без интеграции с ботом:
1. Запустите `python main.py`
2. Откройте в браузере: http://localhost:8080/webapp/index.html

Но учтите, что Telegram Web App API работать не будет без Telegram.

## Примечание

- ngrok URL меняется при каждом перезапуске (в бесплатной версии)
- Для продакшена нужен постоянный домен с HTTPS
- Локальный URL (localhost) не работает в Telegram Mini App

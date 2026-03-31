# 🔧 ИСПРАВЛЕНИЕ Build Command на Render

## Проблема:
Render использует `pip install -r runtime.txt` вместо `pip install -r requirements.txt`

## Решение:

### На Render Dashboard:

1. Зайдите на https://dashboard.render.com
2. Откройте сервис **bot**
3. Нажмите **Settings**
4. Найдите **Build Command**
5. Измените на: `pip install -r requirements.txt`
6. Нажмите **Save Changes**
7. Нажмите **Manual Deploy** → **Clear build cache & deploy**

---

## ИЛИ используйте Docker (РЕКОМЕНДУЕТСЯ):

1. В **Settings** найдите **Environment**
2. Нажмите **Edit**
3. Выберите **Docker** вместо **Python**
4. **Docker Command:** оставьте пустым
5. Нажмите **Save Changes**
6. Нажмите **Manual Deploy** → **Clear build cache & deploy**

Docker использует Dockerfile и Python 3.11 - проблем не будет!

---

**Время:** 2 минуты  
**Результат:** Бот задеплоится! ✅

import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from database import (
    init_db, add_user, get_all_users, get_users_count,
    add_admin, remove_admin, is_admin as check_is_admin, get_all_admins, get_admins_count,
    log_event, get_users_today, get_users_week, get_users_month, 
    get_active_users_today, get_user_info, get_broadcast_stats
)
from keyboards import (
    get_main_keyboard, 
    get_admin_keyboard, 
    get_broadcast_confirm_keyboard,
    get_cancel_keyboard,
    get_back_to_admin_keyboard,
    get_pagination_keyboard,
    get_admin_management_keyboard,
    get_admin_list_keyboard,
    get_stats_keyboard
)

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")

# Настройка прокси (если используется)
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector

# Укажите ваш прокси, если он есть
PROXY_URL = "socks5://127.0.0.1:10809"  # Измените на ваш прокси

try:
    connector = ProxyConnector.from_url(PROXY_URL)
    session = ClientSession(connector=connector)
    bot = Bot(token=BOT_TOKEN, session=session)
    logger.info(f"Бот инициализирован с прокси: {PROXY_URL}")
except Exception as e:
    logger.warning(f"Не удалось подключиться через прокси: {e}. Пробуем без прокси...")
    bot = Bot(token=BOT_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ID администратора (замените на свой)
ADMIN_ID = 1121167993  # Укажите ваш Telegram ID


class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    confirm_broadcast = State()


class AdminStates(StatesGroup):
    waiting_for_admin_id = State()


async def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    if user_id == ADMIN_ID:  # Главный админ
        return True
    return await check_is_admin(user_id)


async def is_super_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь главным администратором"""
    return user_id == ADMIN_ID


# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    welcome_text = (
        f"👋 <b>Добро пожаловать, {message.from_user.first_name}!</b>\n\n"
        "🎮 <b>Case Clicker - Hamster Kombat Style</b>\n\n"
        "🎁 Открывай кейсы и получай предметы\n"
        "👆 Кликай и зарабатывай монеты\n"
        "⬆️ Улучшай свои способности\n"
        "🏆 Получай достижения\n\n"
        "🚀 Нажми <b>\"🎁 Открыть кейсы\"</b> чтобы начать!"
    )
    
    if await is_admin(message.from_user.id):
        welcome_text += "\n\n🔑 <b>Вы вошли как администратор</b>"
        await message.answer(welcome_text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    else:
        await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="HTML")


@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Переход в админ панель"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ панели.")
        return
    
    admin_text = (
        "🔐 <b>Панель администратора</b>\n\n"
        "Выберите действие из меню ниже:"
    )
    await message.answer(admin_text, reply_markup=get_admin_keyboard(), parse_mode="HTML")


# ==================== ОБРАБОТЧИКИ КНОПОК ====================

@dp.message(F.text == "📊 Статистика")
async def button_stats(message: Message):
    """Статистика пользователей"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    count = await get_users_count()
    today = await get_users_today()
    week = await get_users_week()
    month = await get_users_month()
    active_today = await get_active_users_today()
    admins_count = await get_admins_count()
    broadcast_stats = await get_broadcast_stats()
    
    stats_text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{count}</b>\n"
        f"📈 Активных сегодня: <b>{active_today}</b>\n\n"
        f"📅 <b>Новые пользователи:</b>\n"
        f"  • Сегодня: <b>{today}</b>\n"
        f"  • За неделю: <b>{week}</b>\n"
        f"  • За месяц: <b>{month}</b>\n\n"
        f"👨‍💼 Администраторов: <b>{admins_count}</b>\n"
        f"📢 Всего рассылок: <b>{broadcast_stats['total']}</b>\n\n"
        f"📅 Дата: <code>{datetime.now().strftime('%d.%m.%Y %H:%M')}</code>\n"
        f"🤖 Статус: <b>Активен</b>"
    )
    
    await message.answer(stats_text, reply_markup=get_stats_keyboard(), parse_mode="HTML")


@dp.message(F.text == "📢 Рассылка")
async def button_broadcast(message: Message, state: FSMContext):
    """Начало рассылки"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    broadcast_text = (
        "📢 <b>Создание рассылки</b>\n\n"
        "📝 Отправьте сообщение, которое нужно разослать всем пользователям.\n\n"
        "💡 Вы можете отправить:\n"
        "• Текст\n"
        "• Фото с подписью\n"
        "• Видео с подписью\n"
        "• Документы\n"
        "• И многое другое!\n\n"
        "❌ Для отмены нажмите кнопку ниже."
    )
    
    await message.answer(broadcast_text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await state.set_state(BroadcastStates.waiting_for_message)


@dp.message(F.text == "👥 Список пользователей")
async def button_users_list(message: Message):
    """Список пользователей с пагинацией"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    users = await get_all_users()
    total_users = len(users)
    
    if total_users == 0:
        await message.answer("📭 Пользователей пока нет.")
        return
    
    # Показываем первые 10 пользователей
    page = 1
    per_page = 10
    total_pages = (total_users + per_page - 1) // per_page
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_users = users[start_idx:end_idx]
    
    users_text = (
        f"👥 <b>Список пользователей</b>\n"
        f"📄 Страница {page}/{total_pages}\n"
        f"👤 Всего: {total_users}\n\n"
    )
    
    for idx, user_id in enumerate(page_users, start=start_idx + 1):
        users_text += f"{idx}. ID: <code>{user_id}</code>\n"
    
    if total_pages > 1:
        await message.answer(users_text, reply_markup=get_pagination_keyboard(page, total_pages), parse_mode="HTML")
    else:
        await message.answer(users_text, reply_markup=get_back_to_admin_keyboard(), parse_mode="HTML")


@dp.message(F.text == "⚙️ Настройки")
async def button_settings(message: Message):
    """Настройки бота"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    settings_text = (
        "⚙️ <b>Настройки бота</b>\n\n"
        f"🆔 ID главного админа: <code>{ADMIN_ID}</code>\n"
        f"🤖 Версия: <b>3.1 - Hamster Kombat Style</b>\n"
        f"📅 Дата запуска: <code>{datetime.now().strftime('%d.%m.%Y')}</code>\n"
        f"🎮 Тип: <b>Case Clicker Game Bot</b>\n\n"
        "💡 Для изменения настроек отредактируйте файл конфигурации."
    )
    
    await message.answer(settings_text, parse_mode="HTML")


@dp.message(F.text == "👨‍💼 Управление админами")
async def button_manage_admins(message: Message):
    """Управление администраторами"""
    if not await is_super_admin(message.from_user.id):
        await message.answer("❌ Только главный администратор может управлять админами.")
        return
    
    admins = await get_all_admins()
    admins_count = len(admins)
    
    manage_text = (
        "👨‍💼 <b>Управление администраторами</b>\n\n"
        f"👥 Всего администраторов: <b>{admins_count}</b>\n\n"
        "Выберите действие:"
    )
    
    await message.answer(manage_text, reply_markup=get_admin_management_keyboard(), parse_mode="HTML")


@dp.message(F.text == "👤 Режим пользователя")
async def button_user_mode(message: Message):
    """Переключение в режим пользователя"""
    if not await is_admin(message.from_user.id):
        return
    
    user_text = (
        "👤 <b>Режим пользователя</b>\n\n"
        "Вы переключились в обычный режим.\n"
        "Для возврата в админ панель используйте /admin"
    )
    
    await message.answer(user_text, reply_markup=get_main_keyboard(), parse_mode="HTML")


@dp.message(F.text == "ℹ️ О боте")
async def button_about(message: Message):
    """Информация о боте"""
    about_text = (
        "ℹ️ <b>О боте</b>\n\n"
        "🎮 <b>Case Clicker - Hamster Kombat Style</b>\n\n"
        "🎁 Открывай кейсы и получай предметы\n"
        "👆 Кликай и зарабатывай монеты\n"
        "⬆️ Улучшай свои способности\n"
        "🏆 Получай достижения\n"
        "📊 Прокачивай уровень\n\n"
        "📱 Версия: 3.1\n"
        "💻 Разработан на aiogram 3.x\n"
        "🎨 Дизайн в стиле Hamster Kombat\n\n"
        "🚀 Нажми кнопку <b>\"🎁 Открыть кейсы\"</b> чтобы начать играть!"
    )
    
    await message.answer(about_text, parse_mode="HTML")


@dp.message(F.text == "📞 Поддержка")
async def button_support(message: Message):
    """Контакты поддержки"""
    support_text = (
        "📞 <b>Поддержка</b>\n\n"
        "❓ Если у вас возникли вопросы или проблемы,\n"
        "свяжитесь с администратором.\n\n"
        "💡 <b>Как играть:</b>\n"
        "1. Нажми \"🎁 Открыть кейсы\"\n"
        "2. Кликай на иконку и зарабатывай монеты\n"
        "3. Открывай кейсы за монеты\n"
        "4. Улучшай свои способности\n"
        "5. Получай достижения\n\n"
        "📧 Контакт: @admin"
    )
    
    await message.answer(support_text, parse_mode="HTML")


@dp.message(F.text == "❌ Отменить")
async def button_cancel(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    if current_state is None:
        if await is_admin(message.from_user.id):
            await message.answer("✅ Возвращаемся в админ панель.", reply_markup=get_admin_keyboard())
        else:
            await message.answer("✅ Возвращаемся в главное меню.", reply_markup=get_main_keyboard())
        return
    
    await state.clear()
    
    if await is_admin(message.from_user.id):
        await message.answer("❌ Действие отменено.", reply_markup=get_admin_keyboard())
    else:
        await message.answer("❌ Действие отменено.", reply_markup=get_main_keyboard())


# ==================== РАССЫЛКА ====================

@dp.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Обработка сообщения для рассылки"""
    if message.text == "❌ Отменить":
        return
    
    # Сохраняем данные сообщения
    await state.update_data(
        message_id=message.message_id,
        chat_id=message.chat.id
    )
    
    users_count = await get_users_count()
    
    confirm_text = (
        "📢 <b>Подтверждение рассылки</b>\n\n"
        "📝 Ваше сообщение готово к отправке.\n"
        f"👥 Получателей: <b>{users_count}</b>\n\n"
        "❓ Отправить рассылку?"
    )
    
    await message.answer(confirm_text, reply_markup=get_broadcast_confirm_keyboard(), parse_mode="HTML")
    await state.set_state(BroadcastStates.confirm_broadcast)


@dp.callback_query(F.data == "broadcast_confirm")
async def callback_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение рассылки"""
    await callback.answer()
    
    data = await state.get_data()
    message_id = data.get("message_id")
    chat_id = data.get("chat_id")
    
    users = await get_all_users()
    total_users = len(users)
    
    progress_msg = await callback.message.answer(
        f"📤 <b>Рассылка началась...</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"✅ Отправлено: 0\n"
        f"❌ Ошибок: 0",
        parse_mode="HTML"
    )
    
    success_count = 0
    failed_count = 0
    
    for idx, user_id in enumerate(users, 1):
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=chat_id,
                message_id=message_id
            )
            success_count += 1
            
            # Обновляем прогресс каждые 10 сообщений
            if idx % 10 == 0 or idx == total_users:
                try:
                    await progress_msg.edit_text(
                        f"📤 <b>Рассылка в процессе...</b>\n\n"
                        f"👥 Всего пользователей: {total_users}\n"
                        f"✅ Отправлено: {success_count}\n"
                        f"❌ Ошибок: {failed_count}\n"
                        f"📊 Прогресс: {idx}/{total_users}",
                        parse_mode="HTML"
                    )
                except:
                    pass
            
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {user_id}: {e}")
            failed_count += 1
    
    final_text = (
        "✅ <b>Рассылка завершена!</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"✅ Успешно доставлено: <b>{success_count}</b>\n"
        f"❌ Ошибок: <b>{failed_count}</b>\n"
        f"📊 Процент успеха: <b>{round(success_count/total_users*100, 1)}%</b>"
    )
    
    await progress_msg.edit_text(final_text, parse_mode="HTML")
    await callback.message.answer("🏠 Возвращаемся в админ панель.", reply_markup=get_admin_keyboard())
    
    # Логируем рассылку
    await log_event("broadcast", f"Успешно: {success_count}, Ошибок: {failed_count}")
    
    await state.clear()


@dp.callback_query(F.data == "broadcast_cancel")
async def callback_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена рассылки"""
    await callback.answer("❌ Рассылка отменена")
    await state.clear()
    await callback.message.edit_text("❌ <b>Рассылка отменена</b>", parse_mode="HTML")
    await callback.message.answer("🏠 Возвращаемся в админ панель.", reply_markup=get_admin_keyboard())


@dp.callback_query(F.data == "back_to_admin")
async def callback_back_to_admin(callback: CallbackQuery):
    """Возврат в админ панель"""
    await callback.answer()
    await callback.message.answer("🏠 Админ панель", reply_markup=get_admin_keyboard())


@dp.callback_query(F.data.startswith("users_page_"))
async def callback_users_page(callback: CallbackQuery):
    """Пагинация списка пользователей"""
    await callback.answer()
    
    page = int(callback.data.split("_")[-1])
    users = await get_all_users()
    total_users = len(users)
    per_page = 10
    total_pages = (total_users + per_page - 1) // per_page
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_users = users[start_idx:end_idx]
    
    users_text = (
        f"👥 <b>Список пользователей</b>\n"
        f"📄 Страница {page}/{total_pages}\n"
        f"👤 Всего: {total_users}\n\n"
    )
    
    for idx, user_id in enumerate(page_users, start=start_idx + 1):
        users_text += f"{idx}. ID: <code>{user_id}</code>\n"
    
    await callback.message.edit_text(
        users_text, 
        reply_markup=get_pagination_keyboard(page, total_pages),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "current_page")
async def callback_current_page(callback: CallbackQuery):
    """Текущая страница (ничего не делаем)"""
    await callback.answer()


# ==================== УПРАВЛЕНИЕ АДМИНАМИ ====================

@dp.callback_query(F.data == "manage_admins")
async def callback_manage_admins(callback: CallbackQuery):
    """Открытие меню управления админами"""
    await callback.answer()
    
    admins = await get_all_admins()
    admins_count = len(admins)
    
    manage_text = (
        "👨‍💼 <b>Управление администраторами</b>\n\n"
        f"👥 Всего администраторов: <b>{admins_count}</b>\n\n"
        "Выберите действие:"
    )
    
    await callback.message.edit_text(manage_text, reply_markup=get_admin_management_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data == "add_admin")
async def callback_add_admin(callback: CallbackQuery, state: FSMContext):
    """Начало добавления админа"""
    await callback.answer()
    
    add_text = (
        "➕ <b>Добавление администратора</b>\n\n"
        "Отправьте ID пользователя, которого хотите сделать администратором.\n\n"
        "💡 Чтобы узнать ID, попросите пользователя написать боту /start\n\n"
        "❌ Для отмены нажмите кнопку ниже."
    )
    
    await callback.message.edit_text(add_text, parse_mode="HTML")
    await callback.message.answer("Введите ID пользователя:", reply_markup=get_cancel_keyboard())
    await state.set_state(AdminStates.waiting_for_admin_id)


@dp.message(AdminStates.waiting_for_admin_id)
async def process_add_admin(message: Message, state: FSMContext):
    """Обработка добавления админа"""
    if message.text == "❌ Отменить":
        return
    
    try:
        new_admin_id = int(message.text)
        
        # Проверяем, не является ли уже админом
        if await check_is_admin(new_admin_id):
            await message.answer("⚠️ Этот пользователь уже является администратором.")
            return
        
        # Проверяем, существует ли пользователь в базе
        user_info = await get_user_info(new_admin_id)
        if not user_info:
            await message.answer(
                "⚠️ Пользователь не найден в базе данных.\n"
                "Попросите его сначала написать боту /start"
            )
            return
        
        # Добавляем админа
        await add_admin(new_admin_id, message.from_user.id)
        
        user_name = user_info.get('first_name', 'Без имени')
        username = f"@{user_info['username']}" if user_info.get('username') else ""
        
        success_text = (
            "✅ <b>Администратор добавлен!</b>\n\n"
            f"👤 Имя: {user_name} {username}\n"
            f"🆔 ID: <code>{new_admin_id}</code>"
        )
        
        await message.answer(success_text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
        
        # Уведомляем нового админа
        try:
            await bot.send_message(
                new_admin_id,
                "🎉 <b>Поздравляем!</b>\n\n"
                "Вы получили права администратора бота.\n"
                "Используйте /admin для доступа к панели управления.",
                parse_mode="HTML"
            )
        except:
            pass
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите числовой ID пользователя.")


@dp.callback_query(F.data == "remove_admin")
async def callback_remove_admin(callback: CallbackQuery):
    """Показать список админов для удаления"""
    await callback.answer()
    
    admins = await get_all_admins()
    
    if not admins:
        await callback.message.edit_text(
            "📭 <b>Список администраторов пуст</b>\n\n"
            "Нет администраторов для удаления.",
            reply_markup=get_admin_management_keyboard(),
            parse_mode="HTML"
        )
        return
    
    remove_text = (
        "➖ <b>Удаление администратора</b>\n\n"
        "Выберите администратора для удаления:"
    )
    
    await callback.message.edit_text(
        remove_text,
        reply_markup=get_admin_list_keyboard(admins, True),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("del_admin_"))
async def callback_delete_admin(callback: CallbackQuery):
    """Удаление админа"""
    await callback.answer()
    
    admin_id = int(callback.data.split("_")[-1])
    
    # Получаем информацию об админе
    user_info = await get_user_info(admin_id)
    
    # Удаляем админа
    await remove_admin(admin_id)
    
    user_name = user_info.get('first_name', 'Без имени') if user_info else 'Неизвестный'
    username = f"@{user_info['username']}" if user_info and user_info.get('username') else ""
    
    success_text = (
        "✅ <b>Администратор удален!</b>\n\n"
        f"👤 Имя: {user_name} {username}\n"
        f"🆔 ID: <code>{admin_id}</code>"
    )
    
    await callback.message.edit_text(success_text, reply_markup=get_admin_management_keyboard(), parse_mode="HTML")
    
    # Уведомляем бывшего админа
    try:
        await bot.send_message(
            admin_id,
            "ℹ️ <b>Уведомление</b>\n\n"
            "Ваши права администратора были отозваны.",
            parse_mode="HTML"
        )
    except:
        pass


@dp.callback_query(F.data == "list_admins")
async def callback_list_admins(callback: CallbackQuery):
    """Показать список всех админов"""
    await callback.answer()
    
    admins = await get_all_admins()
    
    if not admins:
        await callback.message.edit_text(
            "📭 <b>Список администраторов пуст</b>",
            reply_markup=get_admin_management_keyboard(),
            parse_mode="HTML"
        )
        return
    
    admins_text = "📋 <b>Список администраторов</b>\n\n"
    
    for idx, admin in enumerate(admins, 1):
        name = admin.get('first_name', 'Без имени')
        username = f"@{admin['username']}" if admin.get('username') else ""
        added_at = admin.get('added_at', 'Неизвестно')
        
        admins_text += f"{idx}. {name} {username}\n"
        admins_text += f"   🆔 ID: <code>{admin['user_id']}</code>\n"
        admins_text += f"   📅 Добавлен: {added_at[:10] if added_at != 'Неизвестно' else added_at}\n\n"
    
    await callback.message.edit_text(
        admins_text,
        reply_markup=get_admin_management_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "detailed_stats")
async def callback_detailed_stats(callback: CallbackQuery):
    """Детальная статистика"""
    await callback.answer()
    
    count = await get_users_count()
    today = await get_users_today()
    week = await get_users_week()
    month = await get_users_month()
    active_today = await get_active_users_today()
    admins_count = await get_admins_count()
    broadcast_stats = await get_broadcast_stats()
    
    detailed_text = (
        "📈 <b>Детальная статистика</b>\n\n"
        f"👥 <b>Пользователи:</b>\n"
        f"  • Всего: <b>{count}</b>\n"
        f"  • Активных сегодня: <b>{active_today}</b>\n"
        f"  • Новых сегодня: <b>{today}</b>\n"
        f"  • Новых за неделю: <b>{week}</b>\n"
        f"  • Новых за месяц: <b>{month}</b>\n\n"
        f"👨‍💼 <b>Администрация:</b>\n"
        f"  • Всего админов: <b>{admins_count}</b>\n\n"
        f"📢 <b>Рассылки:</b>\n"
        f"  • Всего отправлено: <b>{broadcast_stats['total']}</b>\n"
        f"  • Последняя: {broadcast_stats['last']}\n\n"
        f"📅 Обновлено: <code>{datetime.now().strftime('%d.%m.%Y %H:%M')}</code>"
    )
    
    await callback.message.edit_text(detailed_text, reply_markup=get_stats_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data == "refresh_stats")
async def callback_refresh_stats(callback: CallbackQuery):
    """Обновление статистики"""
    await callback.answer("🔄 Обновление...")
    
    count = await get_users_count()
    today = await get_users_today()
    week = await get_users_week()
    month = await get_users_month()
    active_today = await get_active_users_today()
    admins_count = await get_admins_count()
    broadcast_stats = await get_broadcast_stats()
    
    stats_text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{count}</b>\n"
        f"📈 Активных сегодня: <b>{active_today}</b>\n\n"
        f"📅 <b>Новые пользователи:</b>\n"
        f"  • Сегодня: <b>{today}</b>\n"
        f"  • За неделю: <b>{week}</b>\n"
        f"  • За месяц: <b>{month}</b>\n\n"
        f"👨‍💼 Администраторов: <b>{admins_count}</b>\n"
        f"📢 Всего рассылок: <b>{broadcast_stats['total']}</b>\n\n"
        f"📅 Дата: <code>{datetime.now().strftime('%d.%m.%Y %H:%M')}</code>\n"
        f"🤖 Статус: <b>Активен</b>"
    )
    
    await callback.message.edit_text(stats_text, reply_markup=get_stats_keyboard(), parse_mode="HTML")


# ==================== ОБРАБОТЧИК ОСТАЛЬНЫХ СООБЩЕНИЙ ====================

@dp.message()
async def echo_handler(message: Message):
    """Обработчик всех остальных сообщений"""
    await add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    if is_admin(message.from_user.id):
        if await is_admin(message.from_user.id):
            await message.answer(
            "❓ Неизвестная команда. Используйте кнопки меню.",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "❓ Неизвестная команда. Используйте кнопки меню.",
            reply_markup=get_main_keyboard()
        )


# ==================== ЗАПУСК БОТА ====================

async def start_web_server():
    """Запуск веб-сервера для Mini App"""
    from aiohttp import web
    from web_server import setup_routes
    
    app = web.Application()
    setup_routes(app)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("🌐 Веб-сервер запущен на порту 8080")


async def main():
    """Главная функция запуска бота"""
    await init_db()
    logger.info("🤖 Бот запущен и готов к работе!")
    
    # Запускаем веб-сервер в фоне
    asyncio.create_task(start_web_server())
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
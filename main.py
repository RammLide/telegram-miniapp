import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from database import (
    init_db, add_user, get_all_users, get_users_count,
    add_admin, remove_admin, is_admin as check_is_admin, get_all_admins, get_admins_count,
    log_event, get_users_today, get_users_week, get_users_month, 
    get_active_users_today, get_user_info, get_broadcast_stats,
    get_referral_code, get_user_by_referral_code, add_referral, claim_referral_bonus,
    get_bot_setting, set_bot_setting,
    ban_user, unban_user, is_user_banned, delete_user_completely,
    log_admin_action, get_admin_logs, search_users_by_username
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
    get_stats_keyboard,
    get_users_list_keyboard,
    get_user_management_keyboard,
    get_balance_edit_keyboard
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

# Инициализация бота (без прокси для Render)
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
    waiting_for_welcome_message = State()


class BanStates(StatesGroup):
    waiting_for_ban_reason = State()
    user_id_to_ban = State()


class SearchStates(StatesGroup):
    waiting_for_username = State()


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
    # Проверяем, новый ли это пользователь ПЕРЕД добавлением в базу
    user_info = await get_user_info(message.from_user.id)
    is_new_user = user_info is None
    
    logger.info(f"User {message.from_user.id} started bot with text: {message.text}, is_new_user: {is_new_user}")
    
    # Проверяем реферальную ссылку (только для новых пользователей)
    referrer_id = None
    ref_code = None
    
    if is_new_user and message.text and len(message.text.split()) > 1:
        args = message.text.split()[1]
        logger.info(f"Start command args: {args}")
        
        if args.startswith('ref_'):
            ref_code = args[4:]  # Убираем префикс 'ref_'
            logger.info(f"Referral code detected: {ref_code}")
            
            referrer_id = await get_user_by_referral_code(ref_code)
            logger.info(f"Referrer ID found: {referrer_id}")
    
    # ТЕПЕРЬ добавляем пользователя в базу
    await add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Генерируем реферальный код для пользователя если его нет
    await get_referral_code(message.from_user.id)
    
    # ОБРАБАТЫВАЕМ РЕФЕРАЛА ПОСЛЕ добавления пользователя
    if is_new_user and referrer_id and referrer_id != message.from_user.id:
        # Добавляем реферала
        success = await add_referral(referrer_id, message.from_user.id)
        logger.info(f"Add referral result: {success}")
        
        if success:
            # Начисляем бонус рефереру
            bonus_claimed = await claim_referral_bonus(referrer_id, message.from_user.id, 1000)
            logger.info(f"Bonus claimed result: {bonus_claimed}")
            
            # Уведомляем реферера
            try:
                await bot.send_message(
                    referrer_id,
                    f"🎉 <b>Новый друг!</b>\n\n"
                    f"Ваш друг {message.from_user.first_name} присоединился к игре!\n"
                    f"💰 Вы получили <b>1000 монет</b>!",
                    parse_mode="HTML"
                )
                logger.info(f"Notification sent to referrer {referrer_id}")
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
        else:
            logger.warning(f"User {message.from_user.id} already registered as referral")
    elif not is_new_user and message.text and len(message.text.split()) > 1:
        logger.info(f"User {message.from_user.id} is not new, referral not counted")
    
    # Получаем тип приветственного сообщения
    welcome_type = await get_bot_setting('welcome_message_type', 'text')
    welcome_text = await get_bot_setting('welcome_message_text', '')
    welcome_file_id = await get_bot_setting('welcome_message_file_id', '')
    
    # Если нет сохраненного приветствия, используем дефолтное
    if not welcome_text and not welcome_file_id:
        welcome_text = (
            f"👋 <b>Добро пожаловать, {message.from_user.first_name}!</b>\n\n"
            "🎮 <b>Turbo Token</b>\n\n"
            "🎁 Открывай кейсы и получай предметы\n"
            "👆 Кликай и зарабатывай монеты\n"
            "⬆️ Улучшай свои способности\n"
            "🏆 Получай достижения\n"
            "👥 Приглашай друзей и получай бонусы\n"
            "📊 Соревнуйся в рейтинге\n\n"
            "🚀 Нажми <b>\"🎁 Открыть кейсы\"</b> чтобы начать!"
        )
        welcome_type = 'text'
    
    # Заменяем {first_name} на реальное имя
    if welcome_text:
        welcome_text = welcome_text.replace('{first_name}', message.from_user.first_name)
    
    # Отправляем приветствие в зависимости от типа
    keyboard = get_admin_keyboard() if await is_admin(message.from_user.id) else get_main_keyboard()
    
    try:
        if welcome_type == 'photo' and welcome_file_id:
            await message.answer_photo(
                photo=welcome_file_id,
                caption=welcome_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        elif welcome_type == 'video' and welcome_file_id:
            await message.answer_video(
                video=welcome_file_id,
                caption=welcome_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        elif welcome_type == 'animation' and welcome_file_id:
            await message.answer_animation(
                animation=welcome_file_id,
                caption=welcome_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        elif welcome_type == 'document' and welcome_file_id:
            await message.answer_document(
                document=welcome_file_id,
                caption=welcome_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")
        # Если ошибка, отправляем текстовое приветствие
        default_text = (
            f"👋 <b>Добро пожаловать, {message.from_user.first_name}!</b>\n\n"
            "🎮 <b>Turbo Token</b>\n\n"
            "🚀 Нажми <b>\"🎁 Открыть кейсы\"</b> чтобы начать!"
        )
        await message.answer(default_text, reply_markup=keyboard, parse_mode="HTML")
    
    # Отправляем отдельное сообщение о реферале
    if referrer_id and is_new_user:
        await message.answer(
            "✅ <b>Вы пришли по реферальной ссылке!</b>\n"
            "Ваш друг получил бонус 1000 монет!",
            parse_mode="HTML"
        )


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
    """Список пользователей с кнопками"""
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
    page_user_ids = users[start_idx:end_idx]
    
    # Получаем информацию о пользователях
    page_users = []
    for user_id in page_user_ids:
        user_info = await get_user_info(user_id)
        if user_info:
            page_users.append(user_info)
    
    users_text = (
        f"👥 <b>Список пользователей</b>\n"
        f"📄 Страница {page}/{total_pages}\n"
        f"👤 Всего: {total_users}\n\n"
        f"Выберите пользователя для управления:"
    )
    
    await message.answer(users_text, reply_markup=get_users_list_keyboard(page_users, page, total_pages), parse_mode="HTML")


@dp.message(F.text == "⚙️ Настройки")
async def button_settings(message: Message):
    """Настройки бота"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    settings_text = (
        "⚙️ <b>Настройки бота</b>\n\n"
        f"🆔 ID главного админа: <code>{ADMIN_ID}</code>\n"
        f"🤖 Версия: <b>3.2 - Turbo Token</b>\n"
        f"📅 Дата запуска: <code>{datetime.now().strftime('%d.%m.%Y')}</code>\n"
        f"🎮 Тип: <b>Turbo Token Game Bot</b>\n\n"
        "💡 Используйте кнопки ниже для настройки бота."
    )
    
    # Создаем клавиатуру с кнопками настроек
    buttons = []
    
    # Кнопка изменения приветствия только для главного админа
    if await is_super_admin(message.from_user.id):
        buttons.append([InlineKeyboardButton(text="💬 Изменить приветствие", callback_data="change_welcome")])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад в админ панель", callback_data="back_to_admin")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(settings_text, reply_markup=keyboard, parse_mode="HTML")


@dp.callback_query(F.data == "change_welcome")
async def callback_change_welcome(callback: CallbackQuery, state: FSMContext):
    """Начать изменение приветственного сообщения"""
    await callback.answer()
    
    if not await is_super_admin(callback.from_user.id):
        await callback.message.answer("❌ Только главный администратор может изменять приветствие.")
        return
    
    current_welcome = await get_bot_setting('welcome_message', 'Не установлено')
    
    change_text = (
        "💬 <b>Изменение приветственного сообщения</b>\n\n"
        "📝 Текущее приветствие:\n"
        f"<code>{current_welcome[:300]}...</code>\n\n"
        "Отправьте новое приветственное сообщение.\n\n"
        "💡 Можете отправить:\n"
        "• Текст (используйте <code>{first_name}</code> для имени)\n"
        "• Фото с подписью\n"
        "• Видео с подписью\n"
        "• GIF с подписью\n"
        "• Документ с подписью\n\n"
        "❌ Для отмены нажмите кнопку ниже."
    )
    
    await callback.message.answer(change_text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_welcome_message)


@dp.message(F.text == "💬 Изменить приветствие")
async def button_change_welcome(message: Message, state: FSMContext):
    """Изменение приветственного сообщения"""
    if not await is_super_admin(message.from_user.id):
        await message.answer("❌ Только главный администратор может изменять приветствие.")
        return
    
    current_welcome = await get_bot_setting('welcome_message', 'Не установлено')
    
    change_text = (
        "💬 <b>Изменение приветственного сообщения</b>\n\n"
        "📝 Текущее приветствие:\n"
        f"<code>{current_welcome[:300]}...</code>\n\n"
        "Отправьте новое приветственное сообщение.\n\n"
        "💡 Можете отправить:\n"
        "• Текст (используйте <code>{first_name}</code> для имени)\n"
        "• Фото с подписью\n"
        "• Видео с подписью\n"
        "• GIF с подписью\n"
        "• Документ с подписью\n\n"
        "❌ Для отмены нажмите кнопку ниже."
    )
    
    await message.answer(change_text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_welcome_message)


@dp.message(AdminStates.waiting_for_welcome_message)
async def process_welcome_message(message: Message, state: FSMContext):
    """Обработка нового приветственного сообщения"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer("❌ Изменение отменено.", reply_markup=get_admin_keyboard())
        return
    
    # Сохраняем ID сообщения и chat_id для копирования
    await state.update_data(
        welcome_message_id=message.message_id,
        welcome_chat_id=message.chat.id
    )
    
    # Сохраняем текст если есть
    if message.text:
        await set_bot_setting('welcome_message_text', message.text)
    elif message.caption:
        await set_bot_setting('welcome_message_text', message.caption)
    else:
        await set_bot_setting('welcome_message_text', '')
    
    # Сохраняем тип медиа
    if message.photo:
        await set_bot_setting('welcome_message_type', 'photo')
        await set_bot_setting('welcome_message_file_id', message.photo[-1].file_id)
    elif message.video:
        await set_bot_setting('welcome_message_type', 'video')
        await set_bot_setting('welcome_message_file_id', message.video.file_id)
    elif message.animation:
        await set_bot_setting('welcome_message_type', 'animation')
        await set_bot_setting('welcome_message_file_id', message.animation.file_id)
    elif message.document:
        await set_bot_setting('welcome_message_type', 'document')
        await set_bot_setting('welcome_message_file_id', message.document.file_id)
    else:
        await set_bot_setting('welcome_message_type', 'text')
        await set_bot_setting('welcome_message_file_id', '')
    
    success_text = "✅ <b>Приветственное сообщение обновлено!</b>\n\nНовые пользователи будут получать это сообщение."
    
    await message.answer(success_text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    await state.clear()


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


@dp.message(F.text == "📝 Логи админов")
async def button_admin_logs(message: Message):
    """Просмотр логов действий админов"""
    if not await is_super_admin(message.from_user.id):
        await message.answer("❌ Только главный администратор может просматривать логи.")
        return
    
    logs = await get_admin_logs(limit=30)
    
    if not logs:
        await message.answer("📝 Логи действий админов пусты.")
        return
    
    logs_text = "📝 <b>Логи действий админов</b>\n"
    logs_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    action_names = {
        "BAN_USER": "Блокировка",
        "UNBAN_USER": "Разблокировка",
        "DELETE_USER": "Удаление",
        "ADD_BALANCE": "Добавление баланса",
        "SUB_BALANCE": "Снятие баланса",
        "SET_BALANCE": "Установка баланса",
        "BROADCAST": "Рассылка"
    }
    
    for i, log in enumerate(logs, 1):
        action_emoji = {
            "BAN_USER": "🚫",
            "UNBAN_USER": "✅",
            "DELETE_USER": "🗑️",
            "ADD_BALANCE": "💰",
            "SUB_BALANCE": "💸",
            "SET_BALANCE": "💵",
            "BROADCAST": "📢"
        }.get(log['action'], "📌")
        
        action_name = action_names.get(log['action'], log['action'])
        
        admin_username = f"@{log['admin_username']}" if log.get('admin_username') else log['admin_name']
        
        logs_text += f"<b>#{i}. {action_emoji} {action_name}</b>\n"
        logs_text += f"👤 Админ: <code>{admin_username}</code>\n"
        
        if log['target_user_id']:
            target_username = f"@{log['target_username']}" if log.get('target_username') else log['target_name']
            logs_text += f"🎯 Пользователь: <code>{target_username}</code>\n"
        
        if log['details']:
            details = log['details'][:50] + "..." if len(log['details']) > 50 else log['details']
            logs_text += f"💬 {details}\n"
        
        # Форматируем дату
        date_str = log['created_at'][:16].replace('T', ' ')
        logs_text += f"🕐 {date_str}\n"
        logs_text += "─────────────────\n\n"
    
    await message.answer(logs_text, parse_mode="HTML")


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
        "🎮 <b>Turbo Token</b>\n\n"
        "🎁 Открывай кейсы и получай предметы\n"
        "👆 Кликай и зарабатывай монеты\n"
        "⬆️ Улучшай свои способности\n"
        "🏆 Получай достижения\n"
        "📊 Прокачивай уровень\n\n"
        "📱 Версия: 3.2\n"
        "💻 Разработан на aiogram 3.x\n"
        "🎨 Современный дизайн\n\n"
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
    
    # Логируем рассылку в логах админов
    await log_admin_action(
        callback.from_user.id, 
        "BROADCAST", 
        None, 
        f"Отправлено: {success_count}/{total_users}, Ошибок: {failed_count}"
    )
    
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
    page_user_ids = users[start_idx:end_idx]
    
    # Получаем информацию о пользователях
    page_users = []
    for user_id in page_user_ids:
        user_info = await get_user_info(user_id)
        if user_info:
            page_users.append(user_info)
    
    users_text = (
        f"👥 <b>Список пользователей</b>\n"
        f"📄 Страница {page}/{total_pages}\n"
        f"👤 Всего: {total_users}\n\n"
        f"Выберите пользователя для управления:"
    )
    
    await callback.message.edit_text(
        users_text, 
        reply_markup=get_users_list_keyboard(page_users, page, total_pages),
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


# ==================== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ====================

@dp.callback_query(F.data.startswith("user_info_"))
async def callback_user_info(callback: CallbackQuery):
    """Показать информацию о пользователе"""
    await callback.answer()
    
    user_id = int(callback.data.split("_")[-1])
    user_info = await get_user_info(user_id)
    
    if not user_info:
        await callback.message.edit_text("❌ Пользователь не найден")
        return
    
    # Получаем баланс и игровые данные
    from database import get_user_balance, get_user_game_data
    balance = await get_user_balance(user_id)
    game_data = await get_user_game_data(user_id)
    
    # Проверяем статус блокировки
    is_banned, ban_reason = await is_user_banned(user_id)
    
    name = user_info.get('first_name', 'Без имени')
    username = f"@{user_info['username']}" if user_info.get('username') else "Нет username"
    created_at = user_info.get('created_at', 'Неизвестно')
    
    level = game_data.get('level', 1) if game_data else 1
    total_clicks = game_data.get('total_clicks', 0) if game_data else 0
    
    ban_status = f"🚫 <b>ЗАБЛОКИРОВАН</b>\nПричина: {ban_reason}\n\n" if is_banned else ""
    
    info_text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"{ban_status}"
        f"📛 Имя: {name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📅 Регистрация: {created_at[:10] if created_at != 'Неизвестно' else created_at}\n\n"
        f"💰 Баланс: <b>{balance}</b> монет\n"
        f"⭐ Уровень: <b>{level}</b>\n"
        f"👆 Всего кликов: <b>{total_clicks}</b>\n"
    )
    
    await callback.message.edit_text(info_text, reply_markup=get_user_management_keyboard(user_id, is_banned), parse_mode="HTML")


@dp.callback_query(F.data.startswith("edit_balance_"))
async def callback_edit_balance(callback: CallbackQuery):
    """Открыть меню изменения баланса"""
    await callback.answer()
    
    user_id = int(callback.data.split("_")[-1])
    user_info = await get_user_info(user_id)
    
    if not user_info:
        await callback.message.edit_text("❌ Пользователь не найден")
        return
    
    from database import get_user_balance
    balance = await get_user_balance(user_id)
    
    name = user_info.get('first_name', 'Без имени')
    
    balance_text = (
        f"💰 <b>Изменение баланса</b>\n\n"
        f"👤 Пользователь: {name}\n"
        f"💵 Текущий баланс: <b>{balance}</b> монет\n\n"
        f"Выберите действие:"
    )
    
    await callback.message.edit_text(balance_text, reply_markup=get_balance_edit_keyboard(user_id), parse_mode="HTML")


@dp.callback_query(F.data.startswith("add_balance_"))
async def callback_add_balance(callback: CallbackQuery):
    """Добавить баланс пользователю"""
    await callback.answer()
    
    parts = callback.data.split("_")
    user_id = int(parts[2])
    amount = int(parts[3])
    
    from database import add_balance, get_user_balance
    await add_balance(user_id, amount)
    new_balance = await get_user_balance(user_id)
    
    user_info = await get_user_info(user_id)
    name = user_info.get('first_name', 'Без имени') if user_info else 'Неизвестный'
    
    balance_text = (
        f"✅ <b>Баланс изменен!</b>\n\n"
        f"👤 Пользователь: {name}\n"
        f"➕ Добавлено: <b>+{amount}</b> монет\n"
        f"💵 Новый баланс: <b>{new_balance}</b> монет"
    )
    
    await callback.message.edit_text(balance_text, reply_markup=get_balance_edit_keyboard(user_id), parse_mode="HTML")
    
    # Уведомляем пользователя
    try:
        await bot.send_message(
            user_id,
            f"💰 <b>Ваш баланс пополнен!</b>\n\n"
            f"Вам начислено <b>+{amount}</b> монет от администратора.\n"
            f"Новый баланс: <b>{new_balance}</b> монет",
            parse_mode="HTML"
        )
    except:
        pass


@dp.callback_query(F.data.startswith("sub_balance_"))
async def callback_sub_balance(callback: CallbackQuery):
    """Вычесть баланс у пользователя"""
    await callback.answer()
    
    parts = callback.data.split("_")
    user_id = int(parts[2])
    amount = int(parts[3])
    
    from database import subtract_balance, get_user_balance
    success = await subtract_balance(user_id, amount)
    new_balance = await get_user_balance(user_id)
    
    user_info = await get_user_info(user_id)
    name = user_info.get('first_name', 'Без имени') if user_info else 'Неизвестный'
    
    if success:
        balance_text = (
            f"✅ <b>Баланс изменен!</b>\n\n"
            f"👤 Пользователь: {name}\n"
            f"➖ Вычтено: <b>-{amount}</b> монет\n"
            f"💵 Новый баланс: <b>{new_balance}</b> монет"
        )
    else:
        balance_text = (
            f"⚠️ <b>Недостаточно средств!</b>\n\n"
            f"👤 Пользователь: {name}\n"
            f"💵 Текущий баланс: <b>{new_balance}</b> монет\n"
            f"❌ Невозможно вычесть {amount} монет"
        )
    
    await callback.message.edit_text(balance_text, reply_markup=get_balance_edit_keyboard(user_id), parse_mode="HTML")


@dp.callback_query(F.data.startswith("set_balance_"))
async def callback_set_balance(callback: CallbackQuery):
    """Установить баланс пользователю"""
    await callback.answer()
    
    parts = callback.data.split("_")
    user_id = int(parts[2])
    amount = int(parts[3])
    
    from database import update_user_balance, get_user_balance
    await update_user_balance(user_id, amount)
    new_balance = await get_user_balance(user_id)
    
    user_info = await get_user_info(user_id)
    name = user_info.get('first_name', 'Без имени') if user_info else 'Неизвестный'
    
    balance_text = (
        f"✅ <b>Баланс установлен!</b>\n\n"
        f"👤 Пользователь: {name}\n"
        f"💵 Новый баланс: <b>{new_balance}</b> монет"
    )
    
    await callback.message.edit_text(balance_text, reply_markup=get_balance_edit_keyboard(user_id), parse_mode="HTML")


@dp.callback_query(F.data.startswith("user_stats_"))
async def callback_user_stats(callback: CallbackQuery):
    """Показать подробную статистику пользователя"""
    await callback.answer()
    
    user_id = int(callback.data.split("_")[-1])
    user_info = await get_user_info(user_id)
    
    if not user_info:
        await callback.message.edit_text("❌ Пользователь не найден")
        return
    
    # Получаем все данные пользователя
    from database import (
        get_user_balance, 
        get_user_game_data, 
        get_user_inventory,
        get_referrals_count,
        get_referrals_earned
    )
    
    balance = await get_user_balance(user_id)
    game_data = await get_user_game_data(user_id)
    inventory = await get_user_inventory(user_id)
    referrals_count = await get_referrals_count(user_id)
    referrals_earned = await get_referrals_earned(user_id)
    
    name = user_info.get('first_name', 'Без имени')
    username = f"@{user_info['username']}" if user_info.get('username') else "Нет username"
    created_at = user_info.get('created_at', 'Неизвестно')
    
    level = game_data.get('level', 1) if game_data else 1
    exp = game_data.get('exp', 0) if game_data else 0
    total_clicks = game_data.get('total_clicks', 0) if game_data else 0
    coins_per_click = game_data.get('coins_per_click', 1) if game_data else 1
    energy = game_data.get('energy', 1000) if game_data else 1000
    max_energy = game_data.get('max_energy', 1000) if game_data else 1000
    
    inventory_count = len(inventory) if inventory else 0
    
    is_banned, ban_reason = await is_user_banned(user_id)
    ban_status = f"🚫 <b>ЗАБЛОКИРОВАН</b>\nПричина: {ban_reason}\n\n" if is_banned else ""
    
    stats_text = (
        f"📊 <b>Подробная статистика</b>\n\n"
        f"{ban_status}"
        f"👤 <b>Пользователь:</b> {name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📅 Регистрация: {created_at[:10] if created_at != 'Неизвестно' else created_at}\n\n"
        f"💰 <b>Экономика:</b>\n"
        f"  • Баланс: <b>{balance}</b> монет\n"
        f"  • Заработано с рефералов: <b>{referrals_earned}</b> монет\n\n"
        f"🎮 <b>Игровой прогресс:</b>\n"
        f"  • Уровень: <b>{level}</b>\n"
        f"  • Опыт: <b>{exp}</b> XP\n"
        f"  • Монет за клик: <b>{coins_per_click}</b>\n"
        f"  • Энергия: <b>{energy}/{max_energy}</b>\n"
        f"  • Всего кликов: <b>{total_clicks}</b>\n\n"
        f"🎒 <b>Инвентарь:</b>\n"
        f"  • Предметов: <b>{inventory_count}</b>\n\n"
        f"👥 <b>Рефералы:</b>\n"
        f"  • Приглашено друзей: <b>{referrals_count}</b>\n"
    )
    
    await callback.message.edit_text(stats_text, reply_markup=get_user_management_keyboard(user_id, is_banned), parse_mode="HTML")


@dp.callback_query(F.data.startswith("ban_user_"))
async def callback_ban_user(callback: CallbackQuery, state: FSMContext):
    """Начать процесс блокировки пользователя"""
    await callback.answer()
    
    user_id = int(callback.data.split("_")[-1])
    
    # Проверка: нельзя заблокировать главного админа
    if user_id == ADMIN_ID:
        await callback.message.answer("❌ Нельзя заблокировать главного администратора!")
        return
    
    # Сохраняем ID пользователя для блокировки
    await state.update_data(user_id_to_ban=user_id)
    await state.set_state(BanStates.waiting_for_ban_reason)
    
    await callback.message.answer(
        f"🚫 <b>Блокировка пользователя</b>\n\n"
        f"Введите причину блокировки или отправьте /skip для использования стандартной причины:\n"
        f"<i>\"Нарушение правил Turbo Token!\"</i>",
        parse_mode="HTML"
    )


@dp.message(BanStates.waiting_for_ban_reason)
async def process_ban_reason(message: Message, state: FSMContext):
    """Обработка причины блокировки"""
    data = await state.get_data()
    user_id = data.get('user_id_to_ban')
    
    if message.text == "/skip":
        reason = "Нарушение правил Turbo Token!"
    else:
        reason = message.text
    
    # Блокируем пользователя
    await ban_user(user_id, message.from_user.id, reason)
    
    # Логируем действие
    await log_admin_action(message.from_user.id, "BAN_USER", user_id, reason)
    
    # Уведомляем пользователя
    user_info = await get_user_info(user_id)
    name = user_info.get('first_name', 'Пользователь') if user_info else 'Пользователь'
    
    try:
        await bot.send_message(
            user_id,
            f"🚫 <b>Ваш аккаунт заблокирован</b>\n\n"
            f"<b>Причина:</b> {reason}\n\n"
            f"Если вы не согласны с блокировкой, обратитесь в <a href='https://t.me/turbo_token_support'>поддержку</a>.",
            parse_mode="HTML"
        )
    except:
        pass
    
    # Показываем обновленную информацию о пользователе
    balance = await get_user_balance(user_id)
    game_data = await get_user_game_data(user_id)
    username = f"@{user_info['username']}" if user_info.get('username') else "Нет username"
    created_at = user_info.get('created_at', 'Неизвестно')
    level = game_data.get('level', 1) if game_data else 1
    total_clicks = game_data.get('total_clicks', 0) if game_data else 0
    
    info_text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"🚫 <b>ЗАБЛОКИРОВАН</b>\nПричина: {reason}\n\n"
        f"📛 Имя: {name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📅 Регистрация: {created_at[:10] if created_at != 'Неизвестно' else created_at}\n\n"
        f"💰 Баланс: <b>{balance}</b> монет\n"
        f"⭐ Уровень: <b>{level}</b>\n"
        f"👆 Всего кликов: <b>{total_clicks}</b>\n"
    )
    
    await message.answer(info_text, reply_markup=get_user_management_keyboard(user_id, is_banned=True), parse_mode="HTML")
    
    # Уведомление админу об успешной блокировке
    await message.answer(
        f"✅ <b>Пользователь {name} ({username}) успешно заблокирован!</b>\n"
        f"📄 Причина: {reason}",
        parse_mode="HTML"
    )
    
    await state.clear()


@dp.callback_query(F.data.startswith("unban_user_"))
async def callback_unban_user(callback: CallbackQuery):
    """Разблокировать пользователя"""
    await callback.answer()
    
    user_id = int(callback.data.split("_")[-1])
    
    # Проверяем, заблокирован ли пользователь
    is_banned, reason = await is_user_banned(user_id)
    
    if not is_banned:
        await callback.message.answer("ℹ️ Этот пользователь не заблокирован.")
        return
    
    # Разблокируем
    await unban_user(user_id, callback.from_user.id)
    
    # Логируем действие
    await log_admin_action(callback.from_user.id, "UNBAN_USER", user_id)
    
    # Уведомляем пользователя
    user_info = await get_user_info(user_id)
    name = user_info.get('first_name', 'Пользователь') if user_info else 'Пользователь'
    
    try:
        await bot.send_message(
            user_id,
            f"✅ <b>Ваш аккаунт разблокирован</b>\n\n"
            f"Вы снова можете пользоваться Turbo Token!",
            parse_mode="HTML"
        )
    except:
        pass
    
    # Показываем обновленную информацию о пользователе
    balance = await get_user_balance(user_id)
    game_data = await get_user_game_data(user_id)
    username = f"@{user_info['username']}" if user_info.get('username') else "Нет username"
    created_at = user_info.get('created_at', 'Неизвестно')
    level = game_data.get('level', 1) if game_data else 1
    total_clicks = game_data.get('total_clicks', 0) if game_data else 0
    
    info_text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"📛 Имя: {name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📅 Регистрация: {created_at[:10] if created_at != 'Неизвестно' else created_at}\n\n"
        f"💰 Баланс: <b>{balance}</b> монет\n"
        f"⭐ Уровень: <b>{level}</b>\n"
        f"👆 Всего кликов: <b>{total_clicks}</b>\n"
    )
    
    await callback.message.edit_text(info_text, reply_markup=get_user_management_keyboard(user_id, is_banned=False), parse_mode="HTML")
    
    # Уведомление админу об успешной разблокировке
    await callback.message.answer(
        f"✅ <b>Пользователь {name} ({username}) успешно разблокирован!</b>",
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("delete_user_"))
async def callback_delete_user(callback: CallbackQuery):
    """Удалить пользователя (только для главного админа)"""
    await callback.answer()
    
    # Проверка: только главный админ
    if not await is_super_admin(callback.from_user.id):
        await callback.message.answer("❌ Эта функция доступна только главному администратору!")
        return
    
    user_id = int(callback.data.split("_")[-1])
    
    # Проверка: нельзя удалить главного админа
    if user_id == ADMIN_ID:
        await callback.message.answer("❌ Нельзя удалить главного администратора!")
        return
    
    user_info = await get_user_info(user_id)
    name = user_info.get('first_name', 'Пользователь') if user_info else 'Пользователь'
    
    # Удаляем пользователя
    await delete_user_completely(user_id)
    
    # Логируем действие
    await log_admin_action(callback.from_user.id, "DELETE_USER", user_id, f"Deleted user: {name}")
    
    await callback.message.answer(
        f"🗑️ Пользователь <b>{name}</b> (ID: {user_id}) полностью удален из базы данных.",
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "back_to_users_list")
async def callback_back_to_users_list(callback: CallbackQuery):
    """Вернуться к списку пользователей"""
    await callback.answer()
    
    users = await get_all_users()
    total_users = len(users)
    
    page = 1
    per_page = 10
    total_pages = (total_users + per_page - 1) // per_page
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_user_ids = users[start_idx:end_idx]
    
    page_users = []
    for user_id in page_user_ids:
        user_info = await get_user_info(user_id)
        if user_info:
            page_users.append(user_info)
    
    users_text = (
        f"👥 <b>Список пользователей</b>\n"
        f"📄 Страница {page}/{total_pages}\n"
        f"👤 Всего: {total_users}\n\n"
        f"Выберите пользователя для управления:"
    )
    
    await callback.message.edit_text(users_text, reply_markup=get_users_list_keyboard(page_users, page, total_pages), parse_mode="HTML")


@dp.callback_query(F.data == "search_user")
async def callback_search_user(callback: CallbackQuery, state: FSMContext):
    """Начать поиск пользователя"""
    await callback.answer()
    
    await callback.message.answer(
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Введите username или имя пользователя для поиска:\n"
        "(можно вводить с @ или без)",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(SearchStates.waiting_for_username)


@dp.message(SearchStates.waiting_for_username)
async def process_search_username(message: Message, state: FSMContext):
    """Обработка поиска пользователя"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer("❌ Поиск отменен.", reply_markup=get_admin_keyboard())
        return
    
    search_query = message.text.strip()
    
    # Ищем пользователей
    found_users = await search_users_by_username(search_query)
    
    if not found_users:
        await message.answer(
            f"❌ Пользователи с username/именем '<b>{search_query}</b>' не найдены.\n\n"
            "Попробуйте другой запрос или нажмите ❌ Отменить",
            parse_mode="HTML"
        )
        return
    
    # Показываем результаты
    results_text = (
        f"🔍 <b>Результаты поиска</b>\n"
        f"Запрос: <code>{search_query}</code>\n"
        f"Найдено: {len(found_users)}\n\n"
        "Выберите пользователя:"
    )
    
    # Создаем клавиатуру с результатами
    buttons = []
    for user in found_users:
        name = user.get('first_name', 'Без имени')
        username = f"@{user['username']}" if user.get('username') else ""
        label = f"{name} {username}".strip()
        buttons.append([InlineKeyboardButton(
            text=label[:40],
            callback_data=f"user_info_{user['user_id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад к списку", callback_data="back_to_users_list")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(results_text, reply_markup=keyboard, parse_mode="HTML")
    await state.clear()


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
    
    # Получаем порт из переменной окружения (для Render) или используем 8080
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"🌐 Веб-сервер запущен на порту {port}")


async def main():
    """Главная функция запуска бота"""
    await init_db()
    logger.info("🤖 Бот запущен и готов к работе!")
    
    # Устанавливаем Menu Button для WebApp
    from aiogram.types import MenuButtonWebApp, WebAppInfo
    from keyboards import WEBAPP_URL
    
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🎁 Открыть кейсы",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        )
        logger.info("✅ Menu Button установлена")
    except Exception as e:
        logger.error(f"❌ Ошибка установки Menu Button: {e}")
    
    # Запускаем веб-сервер в фоне
    asyncio.create_task(start_web_server())
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
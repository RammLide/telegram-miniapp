from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# ВАЖНО: Замените этот URL на ваш Railway URL
WEBAPP_URL = "https://web-production-b9e5d.up.railway.app/webapp/index.html"


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура для пользователей"""
    buttons = []
    
    # Добавляем кнопку Mini App только если URL настроен и это HTTPS
    if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
        buttons.append([KeyboardButton(text="🎁 Открыть кейсы", web_app=WebAppInfo(url=WEBAPP_URL))])
    
    buttons.append([KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="📞 Поддержка")])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    return keyboard


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура для администратора"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📢 Рассылка")],
            [KeyboardButton(text="👥 Список пользователей"), KeyboardButton(text="👨‍💼 Управление админами")],
            [KeyboardButton(text="📝 Логи админов"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="👤 Режим пользователя")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Панель администратора"
    )
    return keyboard


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения рассылки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel")
            ]
        ]
    )
    return keyboard


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура отмены"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отменить")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в админ панель"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад в админ панель", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def get_pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Клавиатура пагинации для списка пользователей"""
    buttons = []
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"users_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="current_page"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"users_page_{page+1}"))
    
    buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="◀️ Назад в админ панель", callback_data="back_to_admin")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_admin_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления администраторами"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить админа", callback_data="add_admin")],
            [InlineKeyboardButton(text="➖ Удалить админа", callback_data="remove_admin")],
            [InlineKeyboardButton(text="📋 Список админов", callback_data="list_admins")],
            [InlineKeyboardButton(text="◀️ Назад в админ панель", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def get_admin_list_keyboard(admins: list, is_super_admin: bool) -> InlineKeyboardMarkup:
    """Клавиатура со списком админов для удаления"""
    buttons = []
    
    for admin in admins:
        name = admin.get('first_name', 'Без имени')
        username = f"@{admin['username']}" if admin.get('username') else ""
        label = f"❌ {name} {username}".strip()
        buttons.append([InlineKeyboardButton(
            text=label, 
            callback_data=f"del_admin_{admin['user_id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="manage_admins")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_stats_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для детальной статистики"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📈 Детальная статистика", callback_data="detailed_stats")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_stats")],
            [InlineKeyboardButton(text="◀️ Назад в админ панель", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def get_users_list_keyboard(users: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Клавиатура со списком пользователей (кнопки)"""
    buttons = []
    
    # Кнопка поиска
    buttons.append([InlineKeyboardButton(text="🔍 Поиск по username", callback_data="search_user")])
    
    # Добавляем кнопки пользователей
    for user in users:
        name = user.get('first_name', 'Без имени')
        username = f"@{user['username']}" if user.get('username') else ""
        label = f"{name} {username}".strip()
        buttons.append([InlineKeyboardButton(
            text=label[:30],  # Ограничиваем длину
            callback_data=f"user_info_{user['user_id']}"
        )])
    
    # Навигация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"users_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="current_page"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"users_page_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад в админ панель", callback_data="back_to_admin")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_user_management_keyboard(user_id: int, is_banned: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура управления пользователем"""
    buttons = [
        [InlineKeyboardButton(text="💰 Изменить баланс", callback_data=f"edit_balance_{user_id}")],
        [InlineKeyboardButton(text="📊 Показать статистику", callback_data=f"user_stats_{user_id}")]
    ]
    
    # Показываем либо блокировку, либо разблокировку
    if is_banned:
        buttons.append([InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"unban_user_{user_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"ban_user_{user_id}")])
    
    buttons.append([InlineKeyboardButton(text="🗑️ Удалить аккаунт", callback_data=f"delete_user_{user_id}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад к списку", callback_data="back_to_users_list")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_balance_edit_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для изменения баланса"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="+100", callback_data=f"add_balance_{user_id}_100"),
                InlineKeyboardButton(text="+500", callback_data=f"add_balance_{user_id}_500"),
                InlineKeyboardButton(text="+1000", callback_data=f"add_balance_{user_id}_1000")
            ],
            [
                InlineKeyboardButton(text="+5000", callback_data=f"add_balance_{user_id}_5000"),
                InlineKeyboardButton(text="+10000", callback_data=f"add_balance_{user_id}_10000"),
                InlineKeyboardButton(text="+50000", callback_data=f"add_balance_{user_id}_50000")
            ],
            [
                InlineKeyboardButton(text="-100", callback_data=f"sub_balance_{user_id}_100"),
                InlineKeyboardButton(text="-500", callback_data=f"sub_balance_{user_id}_500"),
                InlineKeyboardButton(text="-1000", callback_data=f"sub_balance_{user_id}_1000")
            ],
            [
                InlineKeyboardButton(text="🗑️ Обнулить", callback_data=f"set_balance_{user_id}_0"),
                InlineKeyboardButton(text="💎 Установить", callback_data=f"custom_balance_{user_id}")
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f"user_info_{user_id}")]
        ]
    )
    return keyboard
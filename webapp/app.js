// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

// API URL
const API_URL = window.location.origin;

// Функция для безопасного получения данных пользователя из Telegram
function getTelegramUser() {
    console.log('🔍 Getting Telegram user data...');
    console.log('📱 tg object:', tg);
    console.log('📱 tg.initDataUnsafe:', tg.initDataUnsafe);
    console.log('📱 tg.initData:', tg.initData);
    
    // Проверяем разные способы получения данных
    if (tg.initDataUnsafe?.user?.id) {
        console.log('✅ User data from initDataUnsafe:', tg.initDataUnsafe.user);
        return {
            id: tg.initDataUnsafe.user.id,
            firstName: tg.initDataUnsafe.user.first_name || 'Игрок',
            username: tg.initDataUnsafe.user.username || tg.initDataUnsafe.user.first_name || 'Игрок'
        };
    }
    
    // Fallback: пытаемся распарсить initData
    if (tg.initData) {
        console.log('⚠️ Trying to parse initData:', tg.initData);
        try {
            const params = new URLSearchParams(tg.initData);
            const userParam = params.get('user');
            if (userParam) {
                const user = JSON.parse(decodeURIComponent(userParam));
                console.log('✅ User data from initData:', user);
                if (user.id) {
                    return {
                        id: user.id,
                        firstName: user.first_name || 'Игрок',
                        username: user.username || user.first_name || 'Игрок'
                    };
                }
            }
        } catch (e) {
            console.error('❌ Error parsing initData:', e);
        }
    }
    
    // Проверяем localStorage - может там сохранен правильный ID
    const savedUserId = localStorage.getItem('telegram_user_id');
    if (savedUserId && savedUserId !== '12345') {
        console.log('✅ Using saved user ID from localStorage:', savedUserId);
        return {
            id: parseInt(savedUserId),
            firstName: localStorage.getItem('telegram_first_name') || 'Игрок',
            username: localStorage.getItem('telegram_username') || 'Игрок'
        };
    }
    
    console.error('❌ CRITICAL: No user data available! App may not work correctly!');
    console.error('❌ Please open the app from the bot menu button or restart the bot');
    
    // НЕ показываем alert здесь - он будет обработан позже
    
    return {
        id: 12345,
        firstName: 'Игрок',
        username: 'Игрок'
    };
}

// Получаем данные пользователя
const telegramUser = getTelegramUser();

// КРИТИЧЕСКАЯ ПРОВЕРКА: если ID = 12345, не даем приложению работать
if (telegramUser.id === 12345) {
    console.error('❌ CRITICAL ERROR: Invalid user ID detected!');
    document.addEventListener('DOMContentLoaded', () => {
        document.body.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; padding: 20px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <div style="background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); max-width: 400px;">
                    <div style="font-size: 60px; margin-bottom: 20px;">⚠️</div>
                    <h2 style="color: #333; margin-bottom: 15px;">Ошибка загрузки</h2>
                    <p style="color: #666; margin-bottom: 20px; line-height: 1.6;">
                        Не удалось получить данные пользователя из Telegram.
                    </p>
                    <p style="color: #666; margin-bottom: 25px; line-height: 1.6;">
                        <strong>Пожалуйста, откройте приложение через кнопку меню бота</strong> (три полоски слева внизу в чате с ботом).
                    </p>
                    <button onclick="window.Telegram.WebApp.close()" style="background: #667eea; color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 16px; cursor: pointer; font-weight: bold;">
                        Закрыть
                    </button>
                </div>
            </div>
        `;
    });
    throw new Error('Invalid user ID - stopping app initialization');
}

// Данные пользователя
let userData = {
    userId: telegramUser.id,
    username: telegramUser.username,
    firstName: telegramUser.firstName,
    balance: 1000,
    level: 1,
    exp: 0,
    expToNextLevel: 100,
    energy: 1000,
    maxEnergy: 1000,
    coinsPerClick: 1,
    totalClicks: 0,
    ratingScore: 0,
    userRank: 0,
    referralCode: '',
    referralsCount: 0,
    referralsEarned: 0
};

// Игровые данные
let inventory = [];
let openHistory = [];
let upgrades = [];
let achievements = [];
let leaderboard = [];
let marketListings = [];
let myListings = [];
let isLoading = false;
let currentSellItem = null;
let turboPassData = null;
let currentQuickSellItem = null;

// Улучшения
const upgradesData = [
    { id: 'click_power', name: 'Сила клика', desc: 'Увеличивает монеты за клик', icon: '💪', baseCost: 100, costMultiplier: 1.5, effect: 1 },
    { id: 'max_energy', name: 'Больше энергии', desc: 'Увеличивает максимум энергии', icon: '⚡', baseCost: 200, costMultiplier: 1.6, effect: 100 },
    { id: 'energy_regen', name: 'Регенерация', desc: 'Быстрее восстанавливает энергию', icon: '🔋', baseCost: 300, costMultiplier: 1.7, effect: 1 },
    { id: 'auto_clicker', name: 'Авто-клик', desc: 'Монеты в секунду', icon: '🤖', baseCost: 500, costMultiplier: 2.0, effect: 1 },
    { id: 'lucky_case', name: 'Удача', desc: 'Шанс лучших предметов', icon: '🍀', baseCost: 800, costMultiplier: 1.8, effect: 5 },
    { id: 'exp_boost', name: 'Опыт x2', desc: 'Удваивает получаемый опыт', icon: '📚', baseCost: 1000, costMultiplier: 2.2, effect: 2 },
    { id: 'coin_magnet', name: 'Магнит монет', desc: 'Бонус к заработку', icon: '🧲', baseCost: 1500, costMultiplier: 1.9, effect: 10 },
    { id: 'energy_saver', name: 'Экономия', desc: 'Меньше тратит энергии', icon: '💚', baseCost: 2000, costMultiplier: 2.1, effect: 1 },
    { id: 'mega_click', name: 'Мега-клик', desc: 'Огромный бонус к клику', icon: '💥', baseCost: 3000, costMultiplier: 2.5, effect: 5 },
    { id: 'case_discount', name: 'Скидка', desc: 'Кейсы дешевле на 10%', icon: '💸', baseCost: 2500, costMultiplier: 2.0, effect: 10 },
    { id: 'double_reward', name: 'Двойная награда', desc: 'Шанс x2 награды', icon: '🎁', baseCost: 4000, costMultiplier: 2.3, effect: 15 },
    { id: 'speed_boost', name: 'Ускорение', desc: 'Быстрее все действия', icon: '⚡', baseCost: 5000, costMultiplier: 2.4, effect: 20 },
    { id: 'golden_touch', name: 'Золотое касание', desc: 'Больше монет везде', icon: '✨', baseCost: 7000, costMultiplier: 2.6, effect: 25 },
    { id: 'legendary_luck', name: 'Легендарная удача', desc: 'Больше легендарок', icon: '🌟', baseCost: 10000, costMultiplier: 3.0, effect: 10 },
    { id: 'turbo_energy', name: 'Турбо энергия', desc: 'Супер регенерация энергии', icon: '🚀', baseCost: 12000, costMultiplier: 2.8, effect: 2 },
    { id: 'critical_hit', name: 'Критический удар', desc: 'Шанс x5 монет за клик', icon: '💢', baseCost: 15000, costMultiplier: 3.2, effect: 20 },
    { id: 'treasure_hunter', name: 'Охотник за сокровищами', desc: '+50% к ценности предметов', icon: '🗺️', baseCost: 18000, costMultiplier: 2.9, effect: 50 },
    { id: 'time_warp', name: 'Искажение времени', desc: 'Ускоряет все процессы', icon: '⏰', baseCost: 20000, costMultiplier: 3.5, effect: 30 },
    { id: 'diamond_hands', name: 'Алмазные руки', desc: 'Больше редких предметов', icon: '💎', baseCost: 25000, costMultiplier: 3.3, effect: 15 },
    { id: 'infinity_energy', name: 'Бесконечная энергия', desc: 'Огромный запас энергии', icon: '♾️', baseCost: 30000, costMultiplier: 3.8, effect: 500 },
    { id: 'god_mode', name: 'Режим бога', desc: 'Максимальные бонусы', icon: '👑', baseCost: 50000, costMultiplier: 4.0, effect: 100 }
];

// Достижения
const achievementsData = [
    { id: 'first_click', name: 'Первый клик', desc: 'Сделай первый клик', icon: '👆', target: 1, progress: 0, unlocked: false },
    { id: 'clicker_100', name: 'Кликер', desc: 'Сделай 100 кликов', icon: '🖱️', target: 100, progress: 0, unlocked: false },
    { id: 'clicker_1000', name: 'Мастер кликов', desc: 'Сделай 1000 кликов', icon: '⚡', target: 1000, progress: 0, unlocked: false },
    { id: 'clicker_5000', name: 'Супер кликер', desc: 'Сделай 5000 кликов', icon: '💪', target: 5000, progress: 0, unlocked: false },
    { id: 'clicker_10000', name: 'Легенда кликов', desc: 'Сделай 10000 кликов', icon: '💫', target: 10000, progress: 0, unlocked: false },
    { id: 'clicker_50000', name: 'Бог кликов', desc: 'Сделай 50000 кликов', icon: '👑', target: 50000, progress: 0, unlocked: false },
    { id: 'first_case', name: 'Первый кейс', desc: 'Открой первый кейс', icon: '🎁', target: 1, progress: 0, unlocked: false },
    { id: 'case_10', name: 'Коллекционер', desc: 'Открой 10 кейсов', icon: '📦', target: 10, progress: 0, unlocked: false },
    { id: 'case_50', name: 'Охотник за кейсами', desc: 'Открой 50 кейсов', icon: '🎯', target: 50, progress: 0, unlocked: false },
    { id: 'case_100', name: 'Мастер кейсов', desc: 'Открой 100 кейсов', icon: '👑', target: 100, progress: 0, unlocked: false },
    { id: 'case_500', name: 'Король кейсов', desc: 'Открой 500 кейсов', icon: '🔥', target: 500, progress: 0, unlocked: false },
    { id: 'case_1000', name: 'Легенда кейсов', desc: 'Открой 1000 кейсов', icon: '💎', target: 1000, progress: 0, unlocked: false },
    { id: 'rich', name: 'Богач', desc: 'Накопи 10000 монет', icon: '💰', target: 10000, progress: 0, unlocked: false },
    { id: 'very_rich', name: 'Очень богатый', desc: 'Накопи 50000 монет', icon: '💵', target: 50000, progress: 0, unlocked: false },
    { id: 'millionaire', name: 'Миллионер', desc: 'Накопи 100000 монет', icon: '💎', target: 100000, progress: 0, unlocked: false },
    { id: 'multimillionaire', name: 'Мультимиллионер', desc: 'Накопи 500000 монет', icon: '🏆', target: 500000, progress: 0, unlocked: false },
    { id: 'level_5', name: 'Опытный', desc: 'Достигни 5 уровня', icon: '⭐', target: 5, progress: 0, unlocked: false },
    { id: 'level_10', name: 'Профи', desc: 'Достигни 10 уровня', icon: '🌟', target: 10, progress: 0, unlocked: false },
    { id: 'level_25', name: 'Мастер', desc: 'Достигни 25 уровня', icon: '✨', target: 25, progress: 0, unlocked: false },
    { id: 'level_50', name: 'Эксперт', desc: 'Достигни 50 уровня', icon: '🎖️', target: 50, progress: 0, unlocked: false },
    { id: 'level_100', name: 'Легенда', desc: 'Достигни 100 уровня', icon: '👑', target: 100, progress: 0, unlocked: false },
    { id: 'upgrader', name: 'Улучшатель', desc: 'Купи 5 улучшений', icon: '⬆️', target: 5, progress: 0, unlocked: false },
    { id: 'upgrader_pro', name: 'Про улучшатель', desc: 'Купи 15 улучшений', icon: '🚀', target: 15, progress: 0, unlocked: false },
    { id: 'upgrader_master', name: 'Мастер улучшений', desc: 'Купи 30 улучшений', icon: '💫', target: 30, progress: 0, unlocked: false },
    { id: 'legendary_item', name: 'Легендарка!', desc: 'Получи легендарный предмет', icon: '🏆', target: 1, progress: 0, unlocked: false },
    { id: 'legendary_5', name: 'Коллекция легенд', desc: 'Получи 5 легендарных предметов', icon: '🌟', target: 5, progress: 0, unlocked: false },
    { id: 'legendary_10', name: 'Мастер легенд', desc: 'Получи 10 легендарных предметов', icon: '💎', target: 10, progress: 0, unlocked: false },
    { id: 'daily_player', name: 'Ежедневный игрок', desc: 'Забери 7 дневных наград', icon: '📅', target: 7, progress: 0, unlocked: false },
    { id: 'daily_30', name: 'Преданный игрок', desc: 'Забери 30 дневных наград', icon: '🎯', target: 30, progress: 0, unlocked: false },
    { id: 'referrer', name: 'Друг', desc: 'Пригласи 1 друга', icon: '👥', target: 1, progress: 0, unlocked: false },
    { id: 'referrer_5', name: 'Общительный', desc: 'Пригласи 5 друзей', icon: '🤝', target: 5, progress: 0, unlocked: false },
    { id: 'referrer_pro', name: 'Популярный', desc: 'Пригласи 10 друзей', icon: '🎉', target: 10, progress: 0, unlocked: false },
    { id: 'referrer_master', name: 'Звезда', desc: 'Пригласи 25 друзей', icon: '⭐', target: 25, progress: 0, unlocked: false },
    { id: 'referrer_legend', name: 'Инфлюенсер', desc: 'Пригласи 50 друзей', icon: '🔥', target: 50, progress: 0, unlocked: false },
    { id: 'top_100', name: 'Топ 100', desc: 'Попади в топ 100 рейтинга', icon: '🥉', target: 1, progress: 0, unlocked: false },
    { id: 'top_50', name: 'Топ 50', desc: 'Попади в топ 50 рейтинга', icon: '🥈', target: 1, progress: 0, unlocked: false },
    { id: 'top_10', name: 'Топ 10', desc: 'Попади в топ 10 рейтинга', icon: '🥇', target: 1, progress: 0, unlocked: false },
    { id: 'top_1', name: 'Чемпион', desc: 'Стань первым в рейтинге', icon: '👑', target: 1, progress: 0, unlocked: false },
    { id: 'energy_master', name: 'Энергичный', desc: 'Достигни 5000 макс. энергии', icon: '⚡', target: 5000, progress: 0, unlocked: false },
    { id: 'speed_demon', name: 'Скоростной', desc: 'Сделай 100 кликов за минуту', icon: '💨', target: 100, progress: 0, unlocked: false },
    { id: 'lucky_one', name: 'Везунчик', desc: 'Получи 3 легендарки подряд', icon: '🍀', target: 3, progress: 0, unlocked: false }
];

// Кейсы
const cases = [
    {
        id: 1,
        name: 'Бронзовый',
        price: 100,
        emoji: '📦',
        items: [
            { name: '50 монет', rarity: 'common', value: 50, image: '💰', exp: 5, chance: 35, type: 'money' },
            { name: 'Монета', rarity: 'common', value: 10, image: '🪙', exp: 5, chance: 25, type: 'item' },
            { name: 'Кристалл', rarity: 'rare', value: 50, image: '💎', exp: 15, chance: 20, type: 'item' },
            { name: '200 монет', rarity: 'rare', value: 200, image: '💵', exp: 10, chance: 10, type: 'money' },
            { name: 'Золото', rarity: 'epic', value: 150, image: '🏆', exp: 30, chance: 7, type: 'item' },
            { name: 'Меч', rarity: 'legendary', value: 500, image: '⚔️', exp: 100, chance: 3, type: 'item' }
        ]
    },
    {
        id: 2,
        name: 'Серебряный',
        price: 250,
        emoji: '🎁',
        items: [
            { name: '150 монет', rarity: 'common', value: 150, image: '💰', exp: 10, chance: 30, type: 'money' },
            { name: 'Серебро', rarity: 'common', value: 50, image: '🥈', exp: 10, chance: 25, type: 'item' },
            { name: 'Рубин', rarity: 'rare', value: 150, image: '💍', exp: 25, chance: 20, type: 'item' },
            { name: '500 монет', rarity: 'rare', value: 500, image: '💵', exp: 15, chance: 12, type: 'money' },
            { name: 'Корона', rarity: 'epic', value: 400, image: '👑', exp: 50, chance: 10, type: 'item' },
            { name: 'Дракон', rarity: 'legendary', value: 1000, image: '🐉', exp: 150, chance: 3, type: 'item' }
        ]
    },
    {
        id: 3,
        name: 'Золотой',
        price: 500,
        emoji: '💎',
        items: [
            { name: '300 монет', rarity: 'common', value: 300, image: '💰', exp: 20, chance: 30, type: 'money' },
            { name: 'Золото', rarity: 'common', value: 100, image: '🟡', exp: 20, chance: 25, type: 'item' },
            { name: 'Изумруд', rarity: 'rare', value: 300, image: '💚', exp: 40, chance: 20, type: 'item' },
            { name: '1000 монет', rarity: 'rare', value: 1000, image: '💵', exp: 30, chance: 12, type: 'money' },
            { name: 'Посох', rarity: 'epic', value: 800, image: '🪄', exp: 80, chance: 10, type: 'item' },
            { name: 'Феникс', rarity: 'legendary', value: 2000, image: '🔥', exp: 200, chance: 3, type: 'item' }
        ]
    },
    {
        id: 4,
        name: 'Платиновый',
        price: 1000,
        emoji: '👑',
        items: [
            { name: '800 монет', rarity: 'rare', value: 800, image: '💰', exp: 40, chance: 25, type: 'money' },
            { name: 'Платина', rarity: 'rare', value: 500, image: '⚪', exp: 50, chance: 25, type: 'item' },
            { name: 'Алмаз', rarity: 'epic', value: 1200, image: '💎', exp: 100, chance: 20, type: 'item' },
            { name: '2500 монет', rarity: 'epic', value: 2500, image: '💵', exp: 80, chance: 15, type: 'money' },
            { name: 'Щит', rarity: 'legendary', value: 3000, image: '🛡️', exp: 250, chance: 12, type: 'item' },
            { name: 'Единорог', rarity: 'legendary', value: 5000, image: '🦄', exp: 500, chance: 3, type: 'item' }
        ]
    },
    {
        id: 5,
        name: 'Алмазный',
        price: 2000,
        emoji: '💠',
        items: [
            { name: '1500 монет', rarity: 'rare', value: 1500, image: '💰', exp: 60, chance: 25, type: 'money' },
            { name: 'Сапфир', rarity: 'rare', value: 800, image: '🔷', exp: 80, chance: 25, type: 'item' },
            { name: 'Топаз', rarity: 'epic', value: 1800, image: '🟨', exp: 150, chance: 20, type: 'item' },
            { name: '4000 монет', rarity: 'epic', value: 4000, image: '💵', exp: 120, chance: 15, type: 'money' },
            { name: 'Трон', rarity: 'legendary', value: 4500, image: '🪑', exp: 350, chance: 12, type: 'item' },
            { name: 'Грифон', rarity: 'legendary', value: 8000, image: '🦅', exp: 700, chance: 3, type: 'item' }
        ]
    },
    {
        id: 6,
        name: 'Мифический',
        price: 5000,
        emoji: '🌟',
        items: [
            { name: '3500 монет', rarity: 'epic', value: 3500, image: '💰', exp: 200, chance: 25, type: 'money' },
            { name: 'Опал', rarity: 'epic', value: 3000, image: '🔮', exp: 250, chance: 25, type: 'item' },
            { name: 'Скипетр', rarity: 'legendary', value: 7000, image: '👑', exp: 500, chance: 20, type: 'item' },
            { name: '10000 монет', rarity: 'legendary', value: 10000, image: '💵', exp: 400, chance: 15, type: 'money' },
            { name: 'Дракон-король', rarity: 'legendary', value: 12000, image: '🐲', exp: 900, chance: 12, type: 'item' },
            { name: 'Экскалибур', rarity: 'legendary', value: 20000, image: '⚔️', exp: 1500, chance: 3, type: 'item' }
        ]
    },
    {
        id: 7,
        name: 'Божественный',
        price: 10000,
        emoji: '✨',
        items: [
            { name: '7000 монет', rarity: 'epic', value: 7000, image: '💰', exp: 350, chance: 25, type: 'money' },
            { name: 'Нефрит', rarity: 'epic', value: 6000, image: '🟢', exp: 450, chance: 25, type: 'item' },
            { name: 'Крылья ангела', rarity: 'legendary', value: 15000, image: '🪽', exp: 1000, chance: 20, type: 'item' },
            { name: '20000 монет', rarity: 'legendary', value: 20000, image: '💵', exp: 800, chance: 15, type: 'money' },
            { name: 'Молат Тора', rarity: 'legendary', value: 25000, image: '🔨', exp: 1800, chance: 12, type: 'item' },
            { name: 'Корона богов', rarity: 'legendary', value: 50000, image: '👑', exp: 3500, chance: 3, type: 'item' }
        ]
    }
];

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    await initApp();
});

async function initApp() {
    showLoading();
    
    // Логируем данные для отладки
    console.log('🚀 Initializing app...');
    console.log('👤 User ID:', userData.userId);
    console.log('👤 Username:', userData.username);
    console.log('👤 First Name:', userData.firstName);
    console.log('📱 Telegram initDataUnsafe:', tg.initDataUnsafe);
    console.log('📱 Telegram initData:', tg.initData);
    
    // Проверяем блокировку пользователя
    try {
        const banCheckResponse = await fetch(`${API_URL}/api/check_ban`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.userId })
        });
        
        if (banCheckResponse.ok) {
            const banData = await banCheckResponse.json();
            if (banData.is_banned) {
                // Показываем экран блокировки
                document.body.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; padding: 20px; text-align: center; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);">
                        <div style="background: rgba(255,255,255,0.05); padding: 30px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); max-width: 400px; border: 2px solid #ff6b6b;">
                            <div style="font-size: 60px; margin-bottom: 20px;">🚫</div>
                            <h2 style="color: #ff6b6b; margin-bottom: 15px;">Аккаунт заблокирован</h2>
                            <p style="color: #fff; margin-bottom: 15px; line-height: 1.6;">
                                <strong>Причина:</strong><br>${banData.reason}
                            </p>
                            <p style="color: #a0a0a0; margin-bottom: 25px; line-height: 1.6; font-size: 14px;">
                                Если вы не согласны с блокировкой, обратитесь в <a href="https://t.me/turbo_token_support" style="color: #667eea; text-decoration: none;">поддержку</a>.
                            </p>
                            <button onclick="window.Telegram.WebApp.close()" style="background: #667eea; color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 16px; cursor: pointer; font-weight: bold;">
                                Закрыть
                            </button>
                        </div>
                    </div>
                `;
                return; // Останавливаем инициализацию
            }
        }
    } catch (error) {
        console.error('Error checking ban status:', error);
    }
    
    // Загружаем аватарку пользователя
    loadUserAvatar();
    
    // Обновляем UI с начальными данными
    updateUI();
    
    // Загружаем данные с сервера
    await loadGameData();
    
    // Инициализация UI
    updateUI();
    loadCases();
    loadUpgrades();
    loadAchievements();
    checkDailyReward();
    
    // Обработчики событий
    setupEventListeners();
    
    // Загружаем рейтинг и реферальные данные
    await loadLeaderboard();
    await loadReferralData();
    
    // Запускаем регенерацию энергии
    startEnergyRegen();
    
    // Автосохранение каждые 5 секунд
    setInterval(() => {
        if (!isLoading) {
            saveGameData();
        }
    }, 5000);
    
    // Проверка обновлений каждые 3 секунды (баланс, бан статус и т.д.)
    setInterval(() => {
        checkForUpdates();
    }, 3000);
    
    // Сохранение при закрытии/перезагрузке страницы
    window.addEventListener('beforeunload', (e) => {
        // Синхронное сохранение в localStorage
        saveToLocalStorage();
        
        // Пытаемся сохранить на сервер с помощью sendBeacon (не блокирует закрытие)
        const data = JSON.stringify({
            user_id: userData.userId,
            game_data: {
                level: userData.level,
                exp: userData.exp,
                exp_to_next_level: userData.expToNextLevel,
                total_clicks: userData.totalClicks,
                coins_per_click: userData.coinsPerClick,
                energy: Math.floor(userData.energy),
                max_energy: userData.maxEnergy,
                last_energy_update: new Date().toISOString()
            },
            balance: userData.balance,
            upgrades: upgrades.map(u => ({ upgrade_id: u.upgrade_id || u.id, level: u.level })),
            achievements: achievements.map(a => ({ id: a.achievement_id || a.id, progress: a.progress, unlocked: a.unlocked }))
        });
        
        // sendBeacon работает даже при закрытии страницы
        navigator.sendBeacon(`${API_URL}/api/save_game_data`, new Blob([data], { type: 'application/json' }));
    });
    
    // Сохранение при потере фокуса (когда пользователь сворачивает приложение)
    window.addEventListener('blur', () => {
        saveToLocalStorage();
        saveGameData();
    });
    
    // Сохранение при возврате фокуса
    window.addEventListener('focus', async () => {
        // Загружаем актуальные данные с сервера
        await loadGameData();
        updateUI();
    });
    
    // Telegram Web App событие закрытия
    tg.onEvent('viewportChanged', () => {
        saveToLocalStorage();
        saveGameData();
    });
    
    hideLoading();
}

// Загрузка аватарки пользователя
function loadUserAvatar() {
    const avatarEmoji = document.getElementById('avatarEmoji');
    const avatarImage = document.getElementById('avatarImage');
    
    // Пытаемся получить фото профиля из Telegram
    if (tg.initDataUnsafe?.user?.photo_url) {
        console.log('📸 Loading user avatar from Telegram:', tg.initDataUnsafe.user.photo_url);
        avatarImage.src = tg.initDataUnsafe.user.photo_url;
        avatarImage.onload = () => {
            avatarEmoji.style.display = 'none';
            avatarImage.style.display = 'block';
            console.log('✅ Avatar loaded successfully');
        };
        avatarImage.onerror = () => {
            console.warn('⚠️ Failed to load avatar, using emoji');
            avatarEmoji.style.display = 'flex';
            avatarImage.style.display = 'none';
        };
    } else {
        console.log('ℹ️ No avatar URL available, using emoji');
        // Используем первую букву имени как аватарку
        if (userData.firstName) {
            avatarEmoji.textContent = userData.firstName.charAt(0).toUpperCase();
        }
    }
}

function setupEventListeners() {
    // Навигация
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Тап
    const tapCircle = document.getElementById('tapCircle');
    tapCircle.addEventListener('click', handleTap);
    
    // Ежедневная награда
    document.getElementById('claimDaily').addEventListener('click', claimDailyReward);
    
    // Модальное окно кейса
    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modalOverlay').addEventListener('click', closeModal);
    document.getElementById('openCaseBtn').addEventListener('click', openCase);
    
    // Выбор награды из кейса
    document.getElementById('btnKeepItem').addEventListener('click', () => handleRewardChoice('keep'));
    document.getElementById('btnSellItem').addEventListener('click', () => handleRewardChoice('sell'));
    
    // Модальное окно достижений
    document.getElementById('achievementsBtn').addEventListener('click', openAchievementsModal);
    document.getElementById('achievementsModalClose').addEventListener('click', closeAchievementsModal);
    document.getElementById('achievementsModalOverlay').addEventListener('click', closeAchievementsModal);
    
    // Модальное окно Turbo PASS
    document.getElementById('turboPassBtn').addEventListener('click', openTurboPassModal);
    document.getElementById('turboPassModalClose').addEventListener('click', closeTurboPassModal);
    document.getElementById('turboPassModalOverlay').addEventListener('click', closeTurboPassModal);
    
    // Модальное окно продажи
    document.getElementById('sellModalClose').addEventListener('click', closeSellModal);
    document.getElementById('sellModalOverlay').addEventListener('click', closeSellModal);
    document.getElementById('confirmSellBtn').addEventListener('click', confirmSell);
    
    // Модальное окно быстрой продажи
    document.getElementById('quickSellModalClose').addEventListener('click', closeQuickSellModal);
    document.getElementById('quickSellModalOverlay').addEventListener('click', closeQuickSellModal);
    document.getElementById('btnQuickSellHalf').addEventListener('click', quickSellForHalf);
    document.getElementById('btnQuickSellMarket').addEventListener('click', openMarketSellFromQuick);
    
    // Приглашение друзей
    document.getElementById('inviteBtn').addEventListener('click', inviteFriend);
    document.getElementById('copyRefLink')?.addEventListener('click', copyReferralLink);
    
    // Вкладки торговой площадки
    document.querySelectorAll('.market-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchMarketTab(btn.dataset.marketTab));
    });
}

// Загрузка данных с сервера
async function loadGameData() {
    try {
        console.log('🔄 Loading game data from server...');
        const response = await fetch(`${API_URL}/api/game_data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.userId })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('📦 Received data from server:', data);
            
            // Обновляем данные (используем ?? вместо || для правильной обработки 0)
            if (data.game_data) {
                userData.level = data.game_data.level ?? userData.level;
                userData.exp = data.game_data.exp ?? userData.exp;
                userData.expToNextLevel = data.game_data.exp_to_next_level ?? userData.expToNextLevel;
                userData.totalClicks = data.game_data.total_clicks ?? userData.totalClicks;
                userData.coinsPerClick = data.game_data.coins_per_click ?? userData.coinsPerClick;
                userData.energy = data.game_data.energy ?? userData.energy;
                userData.maxEnergy = data.game_data.max_energy ?? userData.maxEnergy;
            }
            if (data.balance !== undefined && data.balance !== null) {
                userData.balance = data.balance;
            }
            if (data.inventory) {
                inventory = data.inventory;
            }
            if (data.upgrades && data.upgrades.length > 0) {
                upgrades = data.upgrades;
            }
            if (data.achievements) {
                if (data.achievements.length > 0) {
                    achievements = data.achievements.map(a => ({
                        achievement_id: a.achievement_id,
                        progress: a.progress,
                        unlocked: a.unlocked
                    }));
                } else {
                    // Инициализируем пустой массив достижений
                    achievements = [];
                }
            }
            
            // Получаем имя пользователя
            const userInfoResponse = await fetch(`${API_URL}/api/user_info`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userData.userId })
            });
            
            if (userInfoResponse.ok) {
                const userInfo = await userInfoResponse.json();
                console.log('👤 User info from server:', userInfo);
                userData.username = userInfo.first_name || userInfo.username || userData.username;
                userData.firstName = userInfo.first_name || userData.firstName;
                
                // Сохраняем в localStorage для следующего раза
                localStorage.setItem('telegram_user_id', userData.userId.toString());
                localStorage.setItem('telegram_first_name', userData.firstName);
                localStorage.setItem('telegram_username', userData.username);
            } else {
                console.warn('⚠️ Failed to get user info from server, using Telegram data');
                // Данные уже установлены из getTelegramUser()
            }
            
            // Получаем рейтинг пользователя
            if (data.game_data && data.game_data.rating_score !== undefined) {
                userData.ratingScore = data.game_data.rating_score;
            }
            
            // Получаем реферальный код
            if (data.referral_code) {
                userData.referralCode = data.referral_code;
            }
            
            console.log('✅ Game data loaded successfully from server');
            console.log('💰 Balance:', userData.balance);
            console.log('📊 Level:', userData.level);
            console.log('🔗 Referral code:', userData.referralCode);
        } else {
            console.warn('⚠️ Server returned error, loading from localStorage');
            loadFromLocalStorage();
        }
    } catch (error) {
        console.error('❌ Error loading game data:', error);
        // Загружаем из localStorage как fallback
        loadFromLocalStorage();
        // Данные пользователя уже установлены из getTelegramUser()
        console.log('✅ Using Telegram user data:', userData.username, userData.userId);
    }
}

// Сохранение данных на сервер
async function saveGameData() {
    if (isLoading) return;
    
    try {
        console.log('💾 Saving game data to server...');
        console.log('📊 Current balance:', userData.balance);
        console.log('📊 Current level:', userData.level);
        
        const response = await fetch(`${API_URL}/api/save_game_data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userData.userId,
                game_data: {
                    level: userData.level,
                    exp: userData.exp,
                    exp_to_next_level: userData.expToNextLevel,
                    total_clicks: userData.totalClicks,
                    coins_per_click: userData.coinsPerClick,
                    energy: Math.floor(userData.energy),
                    max_energy: userData.maxEnergy,
                    last_energy_update: new Date().toISOString()
                },
                balance: userData.balance,
                upgrades: upgrades.map(u => ({ upgrade_id: u.upgrade_id || u.id, level: u.level })),
                achievements: achievements.map(a => ({ id: a.achievement_id || a.id, progress: a.progress, unlocked: a.unlocked }))
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ Game data saved successfully:', result);
            // Также сохраняем в localStorage как резервную копию
            saveToLocalStorage();
        } else {
            console.error('❌ Failed to save game data, status:', response.status);
            // Сохраняем локально если сервер вернул ошибку
            saveToLocalStorage();
        }
    } catch (error) {
        console.error('❌ Error saving game data:', error);
        // Сохраняем локально если сервер недоступен
        saveToLocalStorage();
    }
}

// Навигация
function switchTab(tabName) {
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    if (tabName === 'earn') {
        loadHistory();
        loadAchievements();
    } else if (tabName === 'friends') {
        loadReferralData();
    } else if (tabName === 'rating') {
        loadLeaderboard();
    } else if (tabName === 'inventory') {
        loadInventory();
    } else if (tabName === 'market') {
        loadMarketplace();
    }
}

function switchMarketTab(tabName) {
    document.querySelectorAll('.market-tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.market-tab-content').forEach(content => content.classList.remove('active'));
    
    document.querySelector(`[data-market-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`market-${tabName}-tab`).classList.add('active');
    
    if (tabName === 'buy') {
        loadMarketplace();
    } else if (tabName === 'sell') {
        loadInventory(); // Загружаем инвентарь для отображения
        loadSellInventory();
    } else if (tabName === 'my') {
        loadMyListings();
    }
}

// Обработка тапа
function handleTap(e) {
    if (userData.energy < 1) {
        showNotification('Недостаточно энергии!');
        return;
    }
    
    // Уменьшаем энергию
    userData.energy = Math.max(0, userData.energy - 1);
    
    // Добавляем монеты
    userData.balance += userData.coinsPerClick;
    userData.totalClicks++;
    
    // Добавляем опыт
    addExp(1);
    
    // Обновляем рейтинг (рейтинг = уровень * 100 + баланс / 10)
    updateRatingScore();
    
    // Обновляем достижения
    updateAchievement('first_click', 1);
    updateAchievement('clicker_100', userData.totalClicks);
    updateAchievement('clicker_1000', userData.totalClicks);
    updateAchievement('clicker_5000', userData.totalClicks);
    updateAchievement('clicker_10000', userData.totalClicks);
    updateAchievement('clicker_50000', userData.totalClicks);
    updateAchievement('rich', userData.balance);
    updateAchievement('very_rich', userData.balance);
    updateAchievement('millionaire', userData.balance);
    updateAchievement('multimillionaire', userData.balance);
    
    // Показываем анимацию
    showTapAnimation(e, userData.coinsPerClick);
    
    // Обновляем UI
    updateUI();
    
    // Сохраняем данные сразу после важного действия
    saveGameData();
    
    // Вибрация
    tg.HapticFeedback.impactOccurred('light');
}

function showTapAnimation(e, amount) {
    const counter = document.getElementById('tapCounter');
    const rect = e.target.getBoundingClientRect();
    
    counter.textContent = `+${amount}`;
    counter.style.left = `${e.clientX - rect.left}px`;
    counter.style.top = `${e.clientY - rect.top}px`;
    counter.classList.remove('show');
    
    setTimeout(() => {
        counter.classList.add('show');
    }, 10);
}

// Регенерация энергии
function startEnergyRegen() {
    setInterval(() => {
        if (userData.energy < userData.maxEnergy) {
            userData.energy = Math.min(userData.maxEnergy, userData.energy + 1);
            updateUI();
        }
    }, 1000); // Восстанавливаем 1 энергию в секунду
    
    // Автосохранение при изменении энергии каждые 30 секунд
    setInterval(() => {
        if (!isLoading) {
            saveGameData();
        }
    }, 30000);
}

// Уровни и опыт
function addExp(amount) {
    userData.exp += amount;
    
    while (userData.exp >= userData.expToNextLevel) {
        userData.exp -= userData.expToNextLevel;
        userData.level++;
        userData.expToNextLevel = Math.floor(userData.expToNextLevel * 1.5);
        
        showNotification(`🎉 Уровень ${userData.level}!`);
        tg.HapticFeedback.notificationOccurred('success');
        
        updateAchievement('level_5', userData.level);
        updateAchievement('level_10', userData.level);
        updateAchievement('level_25', userData.level);
        updateAchievement('level_50', userData.level);
        updateAchievement('level_100', userData.level);
        
        // Обновляем рейтинг при повышении уровня
        updateRatingScore();
    }
    
    updateUI();
}

// Обновление UI
function updateUI() {
    document.getElementById('username').textContent = userData.username;
    document.getElementById('level').textContent = userData.level;
    document.getElementById('balance').textContent = userData.balance.toLocaleString();
    document.getElementById('energy').textContent = Math.floor(userData.energy);
    document.getElementById('maxEnergy').textContent = userData.maxEnergy;
    document.getElementById('coinsPerClick').textContent = userData.coinsPerClick;
    
    const expProgress = (userData.exp / userData.expToNextLevel) * 100;
    document.getElementById('expFill').style.width = `${expProgress}%`;
    document.getElementById('expText').textContent = `${userData.exp} / ${userData.expToNextLevel} XP`;
}

// Ежедневная награда
function checkDailyReward() {
    const lastClaim = localStorage.getItem('lastDailyReward');
    const today = new Date().toDateString();
    
    const dailyReward = document.getElementById('dailyReward');
    const claimBtn = document.getElementById('claimDaily');
    
    if (lastClaim !== today) {
        dailyReward.classList.remove('claimed');
        claimBtn.disabled = false;
    } else {
        dailyReward.classList.add('claimed');
        claimBtn.disabled = true;
        claimBtn.textContent = 'Завтра';
    }
}

function claimDailyReward() {
    const bonus = 500;
    userData.balance += bonus;
    updateUI();
    
    localStorage.setItem('lastDailyReward', new Date().toDateString());
    
    const dailyReward = document.getElementById('dailyReward');
    const claimBtn = document.getElementById('claimDaily');
    dailyReward.classList.add('claimed');
    claimBtn.disabled = true;
    claimBtn.textContent = 'Завтра';
    
    showNotification(`+${bonus} 💰 получено!`);
    tg.HapticFeedback.notificationOccurred('success');
    
    // Сохраняем данные сразу после получения награды
    saveGameData();
}

// Кейсы
function loadCases() {
    const casesGrid = document.getElementById('casesGrid');
    casesGrid.innerHTML = '';
    
    cases.forEach(caseItem => {
        const card = document.createElement('div');
        card.className = 'case-card';
        card.innerHTML = `
            <div class="case-emoji">${caseItem.emoji}</div>
            <div class="case-name">${caseItem.name}</div>
            <div class="case-price">💰 ${caseItem.price}</div>
        `;
        card.addEventListener('click', () => showCaseModal(caseItem));
        casesGrid.appendChild(card);
    });
}

let currentCase = null;

function showCaseModal(caseItem) {
    currentCase = caseItem;
    
    document.getElementById('caseTitle').textContent = caseItem.name + ' кейс';
    document.getElementById('casePrice').textContent = `💰 ${caseItem.price}`;
    document.getElementById('caseResult').style.display = 'none';
    document.getElementById('casePreview').style.display = 'flex';
    document.getElementById('caseRoulette').style.display = 'none';
    
    const caseBox = document.querySelector('.case-box-3d');
    caseBox.classList.remove('opening');
    
    const openBtn = document.getElementById('openCaseBtn');
    openBtn.disabled = false;
    openBtn.querySelector('.btn-text').textContent = 'Открыть кейс';
    
    // Отображаем список призов с шансами
    displayCaseItems(caseItem.items);
    
    document.getElementById('caseModal').classList.add('active');
}

function displayCaseItems(items) {
    const itemsListContent = document.getElementById('itemsListContent');
    itemsListContent.innerHTML = '';
    
    items.forEach(item => {
        const row = document.createElement('div');
        row.className = `case-item-row ${item.rarity}`;
        row.innerHTML = `
            <div class="case-item-info">
                <div class="case-item-emoji">${item.image}</div>
                <div class="case-item-name">${item.name}</div>
            </div>
            <div class="case-item-chance">${item.chance}%</div>
        `;
        itemsListContent.appendChild(row);
    });
}

function closeModal() {
    // Если есть невыбранная награда, автоматически добавляем в инвентарь
    if (currentRewardItem && document.getElementById('rewardChoice').style.display !== 'none') {
        handleRewardChoice('keep');
        return; // Не закрываем модалку сразу, дождемся завершения обработки
    }
    
    document.getElementById('caseModal').classList.remove('active');
    currentCase = null;
    currentRewardItem = null;
}

function openCase() {
    if (!currentCase || userData.balance < currentCase.price) {
        showNotification('Недостаточно средств!');
        return;
    }
    
    const openBtn = document.getElementById('openCaseBtn');
    openBtn.disabled = true;
    openBtn.querySelector('.btn-text').textContent = 'Открываем...';
    
    // Скрываем превью и показываем рулетку
    document.getElementById('casePreview').style.display = 'none';
    document.getElementById('caseRoulette').style.display = 'block';
    
    tg.HapticFeedback.impactOccurred('medium');
    
    // Отправляем запрос на сервер для открытия кейса
    fetch(`${API_URL}/api/open_case`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userData.userId,
            case_id: currentCase.id
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification('Ошибка: ' + data.error);
            openBtn.disabled = false;
            openBtn.querySelector('.btn-text').textContent = 'Открыть кейс';
            document.getElementById('casePreview').style.display = 'flex';
            document.getElementById('caseRoulette').style.display = 'none';
            return;
        }
        
        const item = data.item;
        
        // Запускаем анимацию рулетки
        startRouletteAnimation(currentCase.items, item, () => {
            // После завершения анимации показываем результат
            showCaseResult(item);
            
            // Обновляем баланс с сервера (после списания за кейс)
            userData.balance = data.balance;
            updateUI();
        });
    })
    .catch(error => {
        console.error('Error opening case:', error);
        showNotification('Ошибка открытия кейса');
        openBtn.disabled = false;
        openBtn.querySelector('.btn-text').textContent = 'Открыть кейс';
        document.getElementById('casePreview').style.display = 'flex';
        document.getElementById('caseRoulette').style.display = 'none';
    });
}

function startRouletteAnimation(items, winItem, callback) {
    const rouletteItems = document.getElementById('rouletteItems');
    
    // Полностью сбрасываем анимацию
    rouletteItems.innerHTML = '';
    rouletteItems.style.transition = 'none';
    rouletteItems.style.transform = 'translate(0, -50%)';
    
    // Создаем массив предметов для рулетки
    const rouletteArray = [];
    
    // Добавляем 40 случайных предметов ДО выигрышного
    for (let i = 0; i < 40; i++) {
        const randomItem = items[Math.floor(Math.random() * items.length)];
        rouletteArray.push(randomItem);
    }
    
    // Добавляем выигрышный предмет (он будет на позиции 40)
    rouletteArray.push(winItem);
    const winPosition = 40;
    
    // Добавляем еще 40 случайных предметов ПОСЛЕ выигрышного
    for (let i = 0; i < 40; i++) {
        const randomItem = items[Math.floor(Math.random() * items.length)];
        rouletteArray.push(randomItem);
    }
    
    console.log('🎰 Roulette array length:', rouletteArray.length);
    console.log('🎯 Win item at position:', winPosition, '=', rouletteArray[winPosition]);
    
    // Отображаем предметы
    rouletteArray.forEach(item => {
        const itemEl = document.createElement('div');
        itemEl.className = `roulette-item ${item.rarity}`;
        itemEl.innerHTML = `
            <div class="roulette-item-emoji">${item.image}</div>
            <div class="roulette-item-name">${item.name}</div>
        `;
        rouletteItems.appendChild(itemEl);
    });
    
    // Принудительный reflow для сброса анимации
    void rouletteItems.offsetWidth;
    
    // Включаем transition обратно
    rouletteItems.style.transition = 'transform 3s cubic-bezier(0.25, 0.1, 0.25, 1)';
    
    // Запускаем анимацию
    setTimeout(() => {
        // Ширина предмета: 100px (min-width) + 5px (margin-left) + 5px (margin-right) = 110px
        const itemWidth = 110;
        // Центр экрана находится в 50% от ширины контейнера
        // Нужно сместить ленту влево так, чтобы выигрышный предмет (позиция 40) оказался в центре
        // Смещение = позиция * ширина предмета + половина ширины предмета (чтобы центр предмета был под стрелкой)
        const offset = (winPosition * itemWidth) + (itemWidth / 2);
        console.log('📏 Offset:', offset, 'px');
        // Смещаем влево на offset пикселей, и центрируем по вертикали
        rouletteItems.style.transform = `translate(-${offset}px, -50%)`;
    }, 100);
    
    // Вызываем callback после завершения анимации
    setTimeout(() => {
        document.getElementById('caseRoulette').style.display = 'none';
        callback();
    }, 3200);
}

function getRandomItem(items) {
    const rand = Math.random() * 100;
    let cumulative = 0;
    
    // Используем шансы из предметов
    for (const item of items) {
        cumulative += item.chance;
        if (rand <= cumulative) {
            return item;
        }
    }
    
    return items[0];
}

let currentRewardItem = null;

function showCaseResult(item) {
    document.getElementById('casePreview').style.display = 'none';
    document.getElementById('caseItemsList').style.display = 'none';
    
    currentRewardItem = item;
    
    const result = document.getElementById('caseResult');
    document.getElementById('resultRarity').className = `result-rarity ${item.rarity}`;
    document.getElementById('resultEmoji').textContent = item.image;
    document.getElementById('resultName').textContent = item.name;
    document.getElementById('resultValue').textContent = item.value;
    
    // Рассчитываем XP: 10% от стоимости предмета
    const expGained = Math.floor(item.value * 0.1);
    document.getElementById('resultExp').textContent = expGained;
    
    // Добавляем XP к пользователю
    userData.exp += expGained;
    
    // Проверяем повышение уровня
    while (userData.exp >= userData.expToNextLevel) {
        userData.exp -= userData.expToNextLevel;
        userData.level++;
        userData.expToNextLevel = Math.floor(userData.expToNextLevel * 1.5);
        showNotification(`🎉 Поздравляем! Вы достигли ${userData.level} уровня!`);
    }
    
    updateUI();
    
    // Если выпали деньги - автоматически начисляем их
    if (item.type === 'money') {
        // Скрываем выбор для денег
        document.getElementById('rewardChoice').style.display = 'none';
        
        // Автоматически начисляем деньги
        handleRewardChoice('money');
    } else {
        // Показываем сумму продажи (50% от стоимости)
        const sellAmount = Math.floor(item.value / 2);
        document.getElementById('sellAmount').textContent = sellAmount;
        
        // Показываем выбор для предметов
        document.getElementById('rewardChoice').style.display = 'block';
    }
    
    result.style.display = 'block';
    
    tg.HapticFeedback.notificationOccurred(item.rarity === 'legendary' ? 'success' : 'warning');
}

// Улучшения
function loadUpgrades() {
    const upgradesList = document.getElementById('upgradesList');
    if (!upgradesList) return;
    upgradesList.innerHTML = '';
    
    upgradesData.forEach(upgrade => {
        const userUpgrade = upgrades.find(u => u.upgrade_id === upgrade.id) || { upgrade_id: upgrade.id, level: 0 };
        const cost = Math.floor(upgrade.baseCost * Math.pow(upgrade.costMultiplier, userUpgrade.level));
        
        const card = document.createElement('div');
        card.className = 'upgrade-card';
        card.innerHTML = `
            <div class="upgrade-icon">${upgrade.icon}</div>
            <div class="upgrade-info">
                <div class="upgrade-name">${upgrade.name}</div>
                <div class="upgrade-desc">${upgrade.desc}</div>
                <div class="upgrade-level">Уровень ${userUpgrade.level}</div>
            </div>
            <button class="upgrade-btn" data-id="${upgrade.id}" ${userData.balance < cost ? 'disabled' : ''}>
                💰 ${cost}
            </button>
        `;
        
        card.querySelector('.upgrade-btn').addEventListener('click', () => buyUpgrade(upgrade.id));
        upgradesList.appendChild(card);
    });
}

function buyUpgrade(upgradeId) {
    const upgrade = upgradesData.find(u => u.id === upgradeId);
    let userUpgrade = upgrades.find(u => u.upgrade_id === upgradeId);
    
    if (!userUpgrade) {
        userUpgrade = { upgrade_id: upgradeId, level: 0 };
        upgrades.push(userUpgrade);
    }
    
    const cost = Math.floor(upgrade.baseCost * Math.pow(upgrade.costMultiplier, userUpgrade.level));
    
    if (userData.balance < cost) {
        showNotification('Недостаточно средств!');
        return;
    }
    
    userData.balance -= cost;
    userUpgrade.level++;
    
    // Применяем эффект
    if (upgradeId === 'click_power') {
        userData.coinsPerClick += upgrade.effect;
    } else if (upgradeId === 'max_energy') {
        userData.maxEnergy += upgrade.effect;
        userData.energy = Math.min(userData.energy, userData.maxEnergy);
    }
    
    const totalUpgrades = upgrades.reduce((sum, u) => sum + u.level, 0);
    updateAchievement('upgrader', totalUpgrades);
    updateAchievement('upgrader_pro', totalUpgrades);
    updateAchievement('upgrader_master', totalUpgrades);
    
    // Обновляем рейтинг
    updateRatingScore();
    
    updateUI();
    loadUpgrades();
    
    // Сохраняем данные сразу после покупки улучшения
    saveGameData();
    
    showNotification(`${upgrade.name} улучшен!`);
    tg.HapticFeedback.notificationOccurred('success');
}

// История
function addToHistory(caseName, item) {
    openHistory.unshift({
        caseName,
        item,
        timestamp: Date.now()
    });
    
    if (openHistory.length > 20) openHistory.pop();
}

function loadHistory() {
    const historyList = document.getElementById('historyList');
    if (!historyList) return;
    historyList.innerHTML = '';
    
    if (openHistory.length === 0) {
        historyList.innerHTML = '<p style="text-align:center;opacity:0.5;">История пуста</p>';
        return;
    }
    
    openHistory.slice(0, 10).forEach(entry => {
        const item = document.createElement('div');
        item.className = `history-item ${entry.item.rarity}`;
        item.innerHTML = `
            <div class="history-icon">${entry.item.image}</div>
            <div class="history-info">
                <div class="history-name">${entry.item.name}</div>
                <div class="history-time">${entry.caseName} • ${getTimeAgo(entry.timestamp)}</div>
            </div>
            <div class="history-value">💎 ${entry.item.value}</div>
        `;
        historyList.appendChild(item);
    });
}

function getTimeAgo(timestamp) {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return 'только что';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} мин назад`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} ч назад`;
    return `${Math.floor(seconds / 86400)} дн назад`;
}

// Достижения
function loadAchievements() {
    const achievementsGrid = document.getElementById('achievementsGrid');
    console.log('Loading achievements, grid element:', achievementsGrid);
    console.log('Achievements data length:', achievementsData.length);
    console.log('User achievements:', achievements);
    
    if (!achievementsGrid) {
        console.error('achievementsGrid element not found!');
        return;
    }
    
    achievementsGrid.innerHTML = '';
    
    achievementsData.forEach(achievement => {
        const userAch = achievements.find(a => a.achievement_id === achievement.id) || { achievement_id: achievement.id, progress: 0, unlocked: false };
        
        const card = document.createElement('div');
        card.className = `achievement-card ${userAch.unlocked ? 'unlocked' : 'locked'}`;
        card.innerHTML = `
            <div class="achievement-icon">${achievement.icon}</div>
            <div class="achievement-name">${achievement.name}</div>
            <div class="achievement-desc">${achievement.desc}</div>
        `;
        achievementsGrid.appendChild(card);
    });
    
    console.log('Achievements loaded, total cards:', achievementsGrid.children.length);
}

function updateAchievement(id, value) {
    const achievement = achievementsData.find(a => a.id === id);
    if (!achievement) return;
    
    let userAch = achievements.find(a => a.achievement_id === id);
    if (!userAch) {
        userAch = { achievement_id: id, progress: 0, unlocked: false };
        achievements.push(userAch);
    }
    
    if (userAch.unlocked) return;
    
    userAch.progress = Math.min(value, achievement.target);
    
    if (userAch.progress >= achievement.target) {
        userAch.unlocked = true;
        showNotification(`🏆 ${achievement.name}!`);
        tg.HapticFeedback.notificationOccurred('success');
    }
}

function openAchievementsModal() {
    console.log('Opening achievements modal');
    loadAchievements();
    document.getElementById('achievementsModal').classList.add('active');
    console.log('Modal opened');
}

function closeAchievementsModal() {
    console.log('Closing achievements modal');
    document.getElementById('achievementsModal').classList.remove('active');
}

// Приглашение друзей
function inviteFriend() {
    const botUsername = 'turbo_tkn_bot';
    
    // Проверяем, есть ли реферальный код
    if (!userData.referralCode) {
        showNotification('⏳ Загрузка реферальной ссылки...');
        // Пытаемся загрузить реферальные данные
        loadReferralData().then(() => {
            if (userData.referralCode) {
                inviteFriend(); // Повторяем попытку
            } else {
                showNotification('❌ Ошибка загрузки ссылки');
            }
        });
        return;
    }
    
    const inviteLink = `https://t.me/${botUsername}?start=ref_${userData.referralCode}`;
    const shareText = `🎮 Присоединяйся к Turbo Token!\n\n🎁 Получи бонус при регистрации!\n💰 Открывай кейсы и зарабатывай монеты!\n\n`;
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(inviteLink)}&text=${encodeURIComponent(shareText)}`;
    
    console.log('📤 Invite link:', inviteLink);
    tg.openTelegramLink(shareUrl);
}

function copyReferralLink() {
    const botUsername = 'turbo_tkn_bot';
    
    // Проверяем, есть ли реферальный код
    if (!userData.referralCode) {
        showNotification('⏳ Загрузка реферальной ссылки...');
        // Пытаемся загрузить реферальные данные
        loadReferralData().then(() => {
            if (userData.referralCode) {
                copyReferralLink(); // Повторяем попытку
            } else {
                showNotification('❌ Ошибка загрузки ссылки');
            }
        });
        return;
    }
    
    const inviteLink = `https://t.me/${botUsername}?start=ref_${userData.referralCode}`;
    
    console.log('📋 Copying link:', inviteLink);
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(inviteLink).then(() => {
            showNotification('✅ Ссылка скопирована!');
            tg.HapticFeedback.notificationOccurred('success');
        }).catch(() => {
            showNotification('❌ Не удалось скопировать');
        });
    } else {
        showNotification('❌ Копирование не поддерживается');
    }
}

// Загрузка реферальных данных
async function loadReferralData() {
    try {
        console.log('🔄 Loading referral data for user:', userData.userId);
        const response = await fetch(`${API_URL}/api/referral_data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.userId })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('📦 Referral data received:', data);
            userData.referralCode = data.referral_code || '';
            userData.referralsCount = data.referrals_count || 0;
            userData.referralsEarned = data.referrals_earned || 0;
            const referralsList = data.referrals_list || [];
            
            console.log('🔗 Referral code set to:', userData.referralCode);
            
            // Обновляем отображение реферальной ссылки
            const referralLinkText = document.getElementById('referralLinkText');
            if (referralLinkText) {
                if (userData.referralCode) {
                    const botUsername = 'turbo_tkn_bot';
                    const inviteLink = `https://t.me/${botUsername}?start=ref_${userData.referralCode}`;
                    referralLinkText.textContent = inviteLink;
                } else {
                    referralLinkText.textContent = 'Ошибка: код не сгенерирован';
                    referralLinkText.style.color = '#ff6b6b';
                }
            }
            
            // Обновляем UI
            document.getElementById('friendsCount').textContent = userData.referralsCount;
            document.getElementById('friendsEarned').textContent = userData.referralsEarned.toLocaleString();
            
            // Отображаем список рефералов
            displayReferralsList(referralsList);
            
            // Обновляем достижения
            updateAchievement('referrer', userData.referralsCount);
            updateAchievement('referrer_5', userData.referralsCount);
            updateAchievement('referrer_pro', userData.referralsCount);
            updateAchievement('referrer_master', userData.referralsCount);
            updateAchievement('referrer_legend', userData.referralsCount);
        } else {
            console.error('❌ Failed to load referral data, status:', response.status);
            const referralLinkText = document.getElementById('referralLinkText');
            if (referralLinkText) {
                referralLinkText.textContent = 'Ошибка загрузки';
                referralLinkText.style.color = '#ff6b6b';
            }
        }
    } catch (error) {
        console.error('❌ Error loading referral data:', error);
        const referralLinkText = document.getElementById('referralLinkText');
        if (referralLinkText) {
            referralLinkText.textContent = 'Ошибка: ' + error.message;
            referralLinkText.style.color = '#ff6b6b';
        }
    }
}

// Отображение списка рефералов
function displayReferralsList(referrals) {
    const referralsListEl = document.getElementById('referralsList');
    if (!referralsListEl) return;
    
    referralsListEl.innerHTML = '';
    
    if (referrals.length === 0) {
        referralsListEl.innerHTML = '<p style="text-align:center;opacity:0.5;padding:20px;">Пока нет приглашенных друзей</p>';
        return;
    }
    
    referrals.forEach((referral, index) => {
        const item = document.createElement('div');
        item.className = 'referral-item';
        item.innerHTML = `
            <div class="referral-number">${index + 1}</div>
            <div class="referral-info">
                <div class="referral-name">${referral.first_name}</div>
                <div class="referral-stats">Уровень ${referral.level} • 💰 ${referral.balance.toLocaleString()}</div>
            </div>
            <div class="referral-earned">+${referral.earned.toLocaleString()}</div>
        `;
        referralsListEl.appendChild(item);
    });
}

// Загрузка рейтинга
async function loadLeaderboard() {
    try {
        const response = await fetch(`${API_URL}/api/leaderboard`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.userId, limit: 100 })
        });
        
        if (response.ok) {
            const data = await response.json();
            leaderboard = data.leaderboard || [];
            userData.userRank = data.user_rank || 0;
            
            // Обновляем достижения по рейтингу
            if (userData.userRank > 0) {
                if (userData.userRank <= 100) updateAchievement('top_100', 1);
                if (userData.userRank <= 50) updateAchievement('top_50', 1);
                if (userData.userRank <= 10) updateAchievement('top_10', 1);
                if (userData.userRank === 1) updateAchievement('top_1', 1);
            }
            
            displayLeaderboard();
        }
    } catch (error) {
        console.error('Error loading leaderboard:', error);
    }
}

// Отображение рейтинга
function displayLeaderboard() {
    const leaderboardList = document.getElementById('leaderboardList');
    if (!leaderboardList) return;
    
    leaderboardList.innerHTML = '';
    
    if (leaderboard.length === 0) {
        leaderboardList.innerHTML = '<p style="text-align:center;opacity:0.5;">Рейтинг пуст</p>';
        return;
    }
    
    leaderboard.forEach((player, index) => {
        const item = document.createElement('div');
        item.className = `leaderboard-item ${player.user_id === userData.userId ? 'current-user' : ''}`;
        
        let rankIcon = '👤';
        if (index === 0) rankIcon = '🥇';
        else if (index === 1) rankIcon = '🥈';
        else if (index === 2) rankIcon = '🥉';
        
        item.innerHTML = `
            <div class="rank">${rankIcon} ${index + 1}</div>
            <div class="player-info">
                <div class="player-name">${player.username}</div>
                <div class="player-stats">Уровень ${player.level} • 💰 ${player.balance.toLocaleString()}</div>
            </div>
            <div class="player-score">${player.rating_score.toLocaleString()}</div>
        `;
        leaderboardList.appendChild(item);
    });
    
    // Показываем позицию текущего пользователя
    const userRankEl = document.getElementById('userRank');
    if (userRankEl && userData.userRank > 0) {
        userRankEl.textContent = `Ваша позиция: #${userData.userRank}`;
    }
}

// Обновление рейтинга пользователя
function updateRatingScore() {
    // Рейтинг = уровень * 100 + баланс / 10 + клики / 100
    userData.ratingScore = Math.floor(
        userData.level * 100 + 
        userData.balance / 10 + 
        userData.totalClicks / 100
    );
}

// Уведомления
function showNotification(text) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0,0,0,0.9);
        color: white;
        padding: 12px 24px;
        border-radius: 10px;
        font-weight: bold;
        z-index: 10000;
        animation: slideDown 0.3s;
    `;
    notification.textContent = text;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideUp 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

// Loading
function showLoading() {
    isLoading = true;
}

function hideLoading() {
    isLoading = false;
}

// LocalStorage fallback
function saveToLocalStorage() {
    try {
        localStorage.setItem('userData', JSON.stringify(userData));
        localStorage.setItem('upgrades', JSON.stringify(upgrades));
        localStorage.setItem('achievements', JSON.stringify(achievements));
        localStorage.setItem('history', JSON.stringify(openHistory));
        localStorage.setItem('lastSave', new Date().toISOString());
        console.log('Data saved to localStorage');
    } catch (error) {
        console.error('Error saving to localStorage:', error);
    }
}

function loadFromLocalStorage() {
    try {
        const saved = localStorage.getItem('userData');
        if (saved) {
            const savedData = JSON.parse(saved);
            userData = { ...userData, ...savedData };
        }
        
        const savedUpgrades = localStorage.getItem('upgrades');
        if (savedUpgrades) upgrades = JSON.parse(savedUpgrades);
        
        const savedAch = localStorage.getItem('achievements');
        if (savedAch) achievements = JSON.parse(savedAch);
        
        const savedHistory = localStorage.getItem('history');
        if (savedHistory) openHistory = JSON.parse(savedHistory);
        
        console.log('Data loaded from localStorage');
    } catch (error) {
        console.error('Error loading from localStorage:', error);
    }
}

// Стили для анимаций
const style = document.createElement('style');
style.textContent = `
    @keyframes slideDown {
        from { transform: translate(-50%, -100%); opacity: 0; }
        to { transform: translate(-50%, 0); opacity: 1; }
    }
    @keyframes slideUp {
        from { transform: translate(-50%, 0); opacity: 1; }
        to { transform: translate(-50%, -100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// ==================== ИНВЕНТАРЬ ====================

async function loadInventory() {
    try {
        const response = await fetch(`${API_URL}/api/inventory`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.userId })
        });
        
        if (response.ok) {
            const data = await response.json();
            inventory = data.inventory || [];
            displayInventory();
        }
    } catch (error) {
        console.error('Error loading inventory:', error);
    }
}

function displayInventory() {
    const inventoryGrid = document.getElementById('inventoryGrid');
    if (!inventoryGrid) return;
    
    inventoryGrid.innerHTML = '';
    
    if (inventory.length === 0) {
        inventoryGrid.innerHTML = '<p style="text-align:center;opacity:0.5;padding:40px;">Инвентарь пуст</p>';
        return;
    }
    
    inventory.forEach(item => {
        const card = document.createElement('div');
        card.className = `inventory-item ${item.rarity} clickable`;
        card.innerHTML = `
            <div class="item-image">${item.image}</div>
            <div class="item-name">${item.name}</div>
            <div class="item-value">💎 ${item.value}</div>
            <div class="item-count">x${item.count}</div>
            <button class="btn-quick-sell" data-item='${JSON.stringify(item)}'>
                💰 Продать за ${Math.floor(item.value / 2)}
            </button>
        `;
        
        // Кнопка быстрой продажи
        const quickSellBtn = card.querySelector('.btn-quick-sell');
        quickSellBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            quickSellItem(item);
        });
        
        inventoryGrid.appendChild(card);
    });
}

// ==================== ТОРГОВАЯ ПЛОЩАДКА ====================

async function loadMarketplace() {
    try {
        const response = await fetch(`${API_URL}/api/marketplace/listings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit: 50 })
        });
        
        if (response.ok) {
            const data = await response.json();
            marketListings = data.listings || [];
            displayMarketplace();
        }
    } catch (error) {
        console.error('Error loading marketplace:', error);
    }
}

function displayMarketplace() {
    const marketList = document.getElementById('marketList');
    if (!marketList) return;
    
    marketList.innerHTML = '';
    
    if (marketListings.length === 0) {
        marketList.innerHTML = '<p style="text-align:center;opacity:0.5;padding:40px;">Нет товаров на продажу</p>';
        return;
    }
    
    marketListings.forEach(listing => {
        const item = document.createElement('div');
        item.className = `market-item ${listing.item_rarity}`;
        item.innerHTML = `
            <div class="market-item-image">${listing.item_image}</div>
            <div class="market-item-info">
                <div class="market-item-name">${listing.item_name}</div>
                <div class="market-item-seller">Продавец: ${listing.seller_name}</div>
                <div class="market-item-value">Ценность: 💎 ${listing.item_value}</div>
            </div>
            <div class="market-item-actions">
                <div class="market-item-price">💰 ${listing.price}</div>
                <button class="btn-buy-item" data-listing-id="${listing.id}" ${listing.seller_id === userData.userId ? 'disabled' : ''}>
                    ${listing.seller_id === userData.userId ? 'Ваш товар' : 'Купить'}
                </button>
            </div>
        `;
        
        const buyBtn = item.querySelector('.btn-buy-item');
        if (listing.seller_id !== userData.userId) {
            buyBtn.addEventListener('click', () => buyMarketItem(listing.id));
        }
        
        marketList.appendChild(item);
    });
}

async function buyMarketItem(listingId) {
    try {
        const response = await fetch(`${API_URL}/api/marketplace/buy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.userId, listing_id: listingId })
        });
        
        if (response.ok) {
            const data = await response.json();
            userData.balance = data.balance;
            updateUI();
            showNotification('✅ Предмет куплен!');
            tg.HapticFeedback.notificationOccurred('success');
            loadMarketplace();
            loadInventory();
        } else {
            const error = await response.json();
            showNotification('❌ ' + (error.error || 'Ошибка покупки'));
        }
    } catch (error) {
        console.error('Error buying item:', error);
        showNotification('❌ Ошибка покупки');
    }
}

async function loadSellInventory() {
    const sellInventoryGrid = document.getElementById('sellInventoryGrid');
    if (!sellInventoryGrid) return;
    
    sellInventoryGrid.innerHTML = '';
    
    if (inventory.length === 0) {
        sellInventoryGrid.innerHTML = '<p style="text-align:center;opacity:0.5;padding:40px;">Инвентарь пуст</p>';
        return;
    }
    
    inventory.forEach(item => {
        const card = document.createElement('div');
        card.className = `inventory-item ${item.rarity} clickable`;
        card.innerHTML = `
            <div class="item-image">${item.image}</div>
            <div class="item-name">${item.name}</div>
            <div class="item-value">💎 ${item.value}</div>
            <div class="item-count">x${item.count}</div>
        `;
        card.addEventListener('click', () => openSellModal(item));
        sellInventoryGrid.appendChild(card);
    });
}

function openSellModal(item) {
    currentSellItem = item;
    
    const sellItemPreview = document.getElementById('sellItemPreview');
    sellItemPreview.innerHTML = `
        <div class="sell-item-card ${item.rarity}">
            <div class="sell-item-image">${item.image}</div>
            <div class="sell-item-name">${item.name}</div>
            <div class="sell-item-value">Ценность: 💎 ${item.value}</div>
        </div>
    `;
    
    document.getElementById('sellPrice').value = item.value;
    document.getElementById('sellModal').classList.add('active');
}

function closeSellModal() {
    document.getElementById('sellModal').classList.remove('active');
    currentSellItem = null;
}

async function confirmSell() {
    if (!currentSellItem) return;
    
    const price = parseInt(document.getElementById('sellPrice').value);
    if (!price || price < 1) {
        showNotification('❌ Укажите корректную цену');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/marketplace/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userData.userId,
                item_name: currentSellItem.name,
                item_rarity: currentSellItem.rarity,
                item_value: currentSellItem.value,
                item_image: currentSellItem.image,
                price: price
            })
        });
        
        if (response.ok) {
            showNotification('✅ Товар выставлен на продажу!');
            tg.HapticFeedback.notificationOccurred('success');
            closeSellModal();
            loadInventory();
            loadSellInventory();
            switchMarketTab('my');
        } else {
            const error = await response.json();
            showNotification('❌ ' + (error.error || 'Ошибка'));
        }
    } catch (error) {
        console.error('Error creating listing:', error);
        showNotification('❌ Ошибка создания объявления');
    }
}

async function loadMyListings() {
    try {
        const response = await fetch(`${API_URL}/api/marketplace/my_listings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.userId })
        });
        
        if (response.ok) {
            const data = await response.json();
            myListings = data.listings || [];
            displayMyListings();
        }
    } catch (error) {
        console.error('Error loading my listings:', error);
    }
}

function displayMyListings() {
    const myListingsList = document.getElementById('myListingsList');
    if (!myListingsList) return;
    
    myListingsList.innerHTML = '';
    
    if (myListings.length === 0) {
        myListingsList.innerHTML = '<p style="text-align:center;opacity:0.5;padding:40px;">У вас нет объявлений</p>';
        return;
    }
    
    myListings.forEach(listing => {
        const item = document.createElement('div');
        item.className = `market-item ${listing.item_rarity}`;
        
        let statusText = '';
        let statusClass = '';
        if (listing.status === 'active') {
            statusText = 'Активно';
            statusClass = 'status-active';
        } else if (listing.status === 'sold') {
            statusText = 'Продано';
            statusClass = 'status-sold';
        } else if (listing.status === 'cancelled') {
            statusText = 'Отменено';
            statusClass = 'status-cancelled';
        }
        
        item.innerHTML = `
            <div class="market-item-image">${listing.item_image}</div>
            <div class="market-item-info">
                <div class="market-item-name">${listing.item_name}</div>
                <div class="market-item-status ${statusClass}">${statusText}</div>
                <div class="market-item-value">Ценность: 💎 ${listing.item_value}</div>
            </div>
            <div class="market-item-actions">
                <div class="market-item-price">💰 ${listing.price}</div>
                ${listing.status === 'active' ? `<button class="btn-cancel-listing" data-listing-id="${listing.id}">Отменить</button>` : ''}
            </div>
        `;
        
        if (listing.status === 'active') {
            const cancelBtn = item.querySelector('.btn-cancel-listing');
            cancelBtn.addEventListener('click', () => cancelListing(listing.id));
        }
        
        myListingsList.appendChild(item);
    });
}

async function cancelListing(listingId) {
    try {
        const response = await fetch(`${API_URL}/api/marketplace/cancel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.userId, listing_id: listingId })
        });
        
        if (response.ok) {
            showNotification('✅ Объявление отменено');
            tg.HapticFeedback.notificationOccurred('success');
            loadMyListings();
            loadInventory();
        } else {
            const error = await response.json();
            showNotification('❌ ' + (error.error || 'Ошибка'));
        }
    } catch (error) {
        console.error('Error cancelling listing:', error);
        showNotification('❌ Ошибка отмены');
    }
}

// ==================== TURBO PASS ====================

const TURBO_PASS_REWARDS = [
    { day: 1, reward: '💰', value: 100, type: 'coins' },
    { day: 2, reward: '💎', value: 200, type: 'coins' },
    { day: 3, reward: '⚡', value: 50, type: 'energy' },
    { day: 4, reward: '💰', value: 300, type: 'coins' },
    { day: 5, reward: '🎁', value: 500, type: 'coins' },
    { day: 6, reward: '💎', value: 400, type: 'coins' },
    { day: 7, reward: '🏆', value: 1000, type: 'coins' },
    { day: 8, reward: '💰', value: 600, type: 'coins' },
    { day: 9, reward: '⚡', value: 100, type: 'energy' },
    { day: 10, reward: '💎', value: 800, type: 'coins' },
    { day: 11, reward: '💰', value: 700, type: 'coins' },
    { day: 12, reward: '🎁', value: 900, type: 'coins' },
    { day: 13, reward: '💎', value: 1000, type: 'coins' },
    { day: 14, reward: '🏆', value: 2000, type: 'coins' },
    { day: 15, reward: '💰', value: 1200, type: 'coins' },
    { day: 16, reward: '⚡', value: 150, type: 'energy' },
    { day: 17, reward: '💎', value: 1500, type: 'coins' },
    { day: 18, reward: '💰', value: 1300, type: 'coins' },
    { day: 19, reward: '🎁', value: 1600, type: 'coins' },
    { day: 20, reward: '💎', value: 1800, type: 'coins' },
    { day: 21, reward: '🏆', value: 3000, type: 'coins' },
    { day: 22, reward: '💰', value: 2000, type: 'coins' },
    { day: 23, reward: '⚡', value: 200, type: 'energy' },
    { day: 24, reward: '💎', value: 2500, type: 'coins' },
    { day: 25, reward: '💰', value: 2800, type: 'coins' },
    { day: 26, reward: '🎁', value: 3000, type: 'coins' },
    { day: 27, reward: '💎', value: 3500, type: 'coins' },
    { day: 28, reward: '💰', value: 4000, type: 'coins' },
    { day: 29, reward: '🏆', value: 5000, type: 'coins' },
    { day: 30, reward: '👑', value: 10000, type: 'coins' }
];

async function loadTurboPass() {
    try {
        const response = await fetch(`${API_URL}/api/turbo_pass`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.userId })
        });
        
        if (response.ok) {
            turboPassData = await response.json();
            displayTurboPass();
        }
    } catch (error) {
        console.error('Error loading turbo pass:', error);
    }
}

function displayTurboPass() {
    if (!turboPassData) return;
    
    const grid = document.getElementById('turboPassGrid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    document.getElementById('currentPassDay').textContent = turboPassData.current_day;
    document.getElementById('passStreakCount').textContent = turboPassData.streak;
    
    TURBO_PASS_REWARDS.forEach((reward, index) => {
        const dayNum = index + 1;
        const isCompleted = turboPassData.claimed_days.includes(dayNum);
        const isCurrent = dayNum === turboPassData.current_day;
        const isLocked = dayNum > turboPassData.current_day;
        
        const card = document.createElement('div');
        card.className = `pass-day-card ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''} ${isLocked ? 'locked' : ''}`;
        
        let valueText = reward.type === 'coins' ? `${reward.value} 💰` : `+${reward.value} ⚡`;
        
        card.innerHTML = `
            <div class="pass-day-number">День ${dayNum}</div>
            <div class="pass-day-reward">${reward.reward}</div>
            <div class="pass-day-value">${valueText}</div>
            ${isCompleted ? '<div class="pass-checkmark">✅</div>' : ''}
            ${isCurrent && !isCompleted ? '<button class="pass-claim-btn" onclick="claimTurboPassReward()">Забрать</button>' : ''}
        `;
        
        grid.appendChild(card);
    });
}

async function claimTurboPassReward() {
    try {
        const response = await fetch(`${API_URL}/api/turbo_pass/claim`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.userId })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            userData.balance = data.balance;
            if (data.energy) {
                userData.energy = Math.min(userData.maxEnergy, userData.energy + data.reward_value);
            }
            
            updateUI();
            
            const reward = TURBO_PASS_REWARDS[turboPassData.current_day - 1];
            showNotification(`✅ Получено: ${reward.value} ${reward.type === 'coins' ? '💰' : '⚡'}`);
            tg.HapticFeedback.notificationOccurred('success');
            
            await loadTurboPass();
            saveGameData();
        } else {
            const error = await response.json();
            showNotification('❌ ' + (error.error || 'Ошибка'));
        }
    } catch (error) {
        console.error('Error claiming turbo pass reward:', error);
        showNotification('❌ Ошибка получения награды');
    }
}

function openTurboPassModal() {
    loadTurboPass();
    document.getElementById('turboPassModal').classList.add('active');
}

function closeTurboPassModal() {
    document.getElementById('turboPassModal').classList.remove('active');
}

// Быстрая продажа предмета за полцены
async function quickSellItem(item) {
    const sellPrice = Math.floor(item.value / 2);
    
    // Подтверждение
    if (!confirm(`Продать "${item.name}" за ${sellPrice} монет?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/quick_sell_item`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userData.userId,
                item_name: item.name,
                item_rarity: item.rarity,
                item_value: item.value,
                item_image: item.image
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            userData.balance = data.balance;
            updateUI();
            showNotification(`✅ Продано за ${data.amount} монет!`);
            tg.HapticFeedback.notificationOccurred('success');
            loadInventory();
        } else {
            const error = await response.json();
            showNotification('❌ ' + (error.error || 'Ошибка продажи'));
        }
    } catch (error) {
        console.error('Error quick selling item:', error);
        showNotification('❌ Ошибка продажи');
    }
}

// Проверка обновлений в реальном времени
async function checkForUpdates() {
    if (isLoading) return;
    
    try {
        const response = await fetch(`${API_URL}/api/check_updates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.userId })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Проверяем бан
            if (data.is_banned) {
                document.body.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; padding: 20px; text-align: center; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);">
                        <div style="background: rgba(255,255,255,0.05); padding: 30px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); max-width: 400px; border: 2px solid #ff6b6b;">
                            <div style="font-size: 60px; margin-bottom: 20px;">🚫</div>
                            <h2 style="color: #ff6b6b; margin-bottom: 15px;">Аккаунт заблокирован</h2>
                            <p style="color: #fff; margin-bottom: 15px; line-height: 1.6;">
                                <strong>Причина:</strong><br>${data.ban_reason}
                            </p>
                            <p style="color: #a0a0a0; margin-bottom: 25px; line-height: 1.6; font-size: 14px;">
                                Если вы не согласны с блокировкой, обратитесь в <a href="https://t.me/turbo_token_support" style="color: #667eea; text-decoration: none;">поддержку</a>.
                            </p>
                            <button onclick="window.Telegram.WebApp.close()" style="background: #667eea; color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 16px; cursor: pointer; font-weight: bold;">
                                Закрыть
                            </button>
                        </div>
                    </div>
                `;
                return;
            }
            
            // Обновляем баланс если изменился
            if (data.balance !== undefined && data.balance !== userData.balance) {
                const diff = data.balance - userData.balance;
                userData.balance = data.balance;
                updateUI();
                
                if (diff > 0) {
                    showNotification(`💰 +${diff} монет`);
                } else if (diff < 0) {
                    showNotification(`💰 ${diff} монет`);
                }
            }
            
            // Обновляем другие данные если изменились
            if (data.game_data) {
                if (data.game_data.energy !== undefined) {
                    userData.energy = data.game_data.energy;
                }
                if (data.game_data.max_energy !== undefined) {
                    userData.maxEnergy = data.game_data.max_energy;
                }
                updateUI();
            }
        }
    } catch (error) {
        // Игнорируем ошибки при проверке обновлений
        console.log('Update check failed:', error);
    }
}

// Обработка выбора награды из кейса
async function handleRewardChoice(choice) {
    if (!currentRewardItem) return;
    
    try {
        // Блокируем кнопки
        const btnKeep = document.getElementById('btnKeepItem');
        const btnSell = document.getElementById('btnSellItem');
        if (btnKeep) btnKeep.disabled = true;
        if (btnSell) btnSell.disabled = true;
        
        const response = await fetch(`${API_URL}/api/case_reward_choice`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userData.userId,
                item: currentRewardItem,
                choice: choice === 'money' ? 'sell' : choice  // Деньги обрабатываем как продажу
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Обновляем баланс
            userData.balance = data.balance;
            updateUI();
            
            // Показываем уведомление
            if (choice === 'keep') {
                showNotification(`✅ ${currentRewardItem.name} добавлен в инвентарь!`);
                loadInventory();
            } else if (choice === 'money') {
                showNotification(`💰 Получено ${currentRewardItem.value} монет!`);
            } else {
                showNotification(`💰 Получено ${data.amount} монет за продажу!`);
            }
            
            tg.HapticFeedback.notificationOccurred('success');
            
            // Обновляем достижения
            addToHistory(currentCase.name, currentRewardItem);
            updateAchievement('first_case', 1);
            updateAchievement('case_10', openHistory.length);
            updateAchievement('case_50', openHistory.length);
            updateAchievement('case_100', openHistory.length);
            updateAchievement('case_500', openHistory.length);
            updateAchievement('case_1000', openHistory.length);
            updateAchievement('rich', userData.balance);
            updateAchievement('very_rich', userData.balance);
            updateAchievement('millionaire', userData.balance);
            updateAchievement('multimillionaire', userData.balance);
            
            if (currentRewardItem.rarity === 'legendary') {
                updateAchievement('legendary_item', 1);
            }
            
            // Обновляем рейтинг
            updateRatingScore();
            
            // Сохраняем данные
            saveGameData();
            
            // Скрываем выбор и показываем кнопку "Открыть еще"
            document.getElementById('rewardChoice').style.display = 'none';
            const openBtn = document.getElementById('openCaseBtn');
            openBtn.disabled = false;
            openBtn.querySelector('.btn-text').textContent = 'Открыть еще';
            
            // Очищаем текущую награду
            currentRewardItem = null;
            
            // Разблокируем кнопки для следующего раза
            if (btnKeep) btnKeep.disabled = false;
            if (btnSell) btnSell.disabled = false;
        } else {
            const error = await response.json();
            showNotification('❌ ' + (error.error || 'Ошибка'));
            
            // Разблокируем кнопки
            if (btnKeep) btnKeep.disabled = false;
            if (btnSell) btnSell.disabled = false;
        }
    } catch (error) {
        console.error('Error handling reward choice:', error);
        showNotification('❌ Ошибка обработки выбора');
        
        // Разблокируем кнопки
        const btnKeep = document.getElementById('btnKeepItem');
        const btnSell = document.getElementById('btnSellItem');
        if (btnKeep) btnKeep.disabled = false;
        if (btnSell) btnSell.disabled = false;
    }
}

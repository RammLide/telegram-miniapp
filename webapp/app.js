// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

// API URL
const API_URL = window.location.origin;

// Данные пользователя
let userData = {
    userId: tg.initDataUnsafe?.user?.id || 12345,
    username: tg.initDataUnsafe?.user?.username || tg.initDataUnsafe?.user?.first_name || 'Guest',
    balance: 1000,
    level: 1,
    exp: 0,
    expToNextLevel: 100,
    energy: 1000,
    maxEnergy: 1000,
    coinsPerClick: 1,
    totalClicks: 0
};

// Игровые данные
let inventory = [];
let openHistory = [];
let upgrades = [];
let achievements = [];
let isLoading = false;

// Улучшения
const upgradesData = [
    { id: 'click_power', name: 'Сила клика', desc: 'Увеличивает монеты за клик', icon: '💪', baseCost: 100, costMultiplier: 1.5, effect: 1 },
    { id: 'max_energy', name: 'Больше энергии', desc: 'Увеличивает максимум энергии', icon: '⚡', baseCost: 200, costMultiplier: 1.6, effect: 100 },
    { id: 'energy_regen', name: 'Регенерация', desc: 'Быстрее восстанавливает энергию', icon: '🔋', baseCost: 300, costMultiplier: 1.7, effect: 1 },
    { id: 'auto_clicker', name: 'Авто-клик', desc: 'Монеты в секунду', icon: '🤖', baseCost: 500, costMultiplier: 2.0, effect: 1 }
];

// Достижения
const achievementsData = [
    { id: 'first_click', name: 'Первый клик', desc: 'Сделай первый клик', icon: '👆', target: 1, progress: 0, unlocked: false },
    { id: 'clicker_100', name: 'Кликер', desc: 'Сделай 100 кликов', icon: '🖱️', target: 100, progress: 0, unlocked: false },
    { id: 'first_case', name: 'Первый кейс', desc: 'Открой первый кейс', icon: '🎁', target: 1, progress: 0, unlocked: false },
    { id: 'rich', name: 'Богач', desc: 'Накопи 10000 монет', icon: '💰', target: 10000, progress: 0, unlocked: false },
    { id: 'level_5', name: 'Опытный', desc: 'Достигни 5 уровня', icon: '⭐', target: 5, progress: 0, unlocked: false },
    { id: 'upgrader', name: 'Улучшатель', desc: 'Купи 5 улучшений', icon: '⬆️', target: 5, progress: 0, unlocked: false }
];

// Кейсы
const cases = [
    {
        id: 1,
        name: 'Бронзовый',
        price: 100,
        emoji: '📦',
        items: [
            { name: 'Монета', rarity: 'common', value: 10, image: '🪙', exp: 5 },
            { name: 'Кристалл', rarity: 'rare', value: 50, image: '💎', exp: 15 },
            { name: 'Золото', rarity: 'epic', value: 150, image: '🏆', exp: 30 },
            { name: 'Меч', rarity: 'legendary', value: 500, image: '⚔️', exp: 100 }
        ]
    },
    {
        id: 2,
        name: 'Серебряный',
        price: 250,
        emoji: '🎁',
        items: [
            { name: 'Серебро', rarity: 'common', value: 50, image: '🥈', exp: 10 },
            { name: 'Рубин', rarity: 'rare', value: 150, image: '💍', exp: 25 },
            { name: 'Корона', rarity: 'epic', value: 400, image: '👑', exp: 50 },
            { name: 'Дракон', rarity: 'legendary', value: 1000, image: '🐉', exp: 150 }
        ]
    },
    {
        id: 3,
        name: 'Золотой',
        price: 500,
        emoji: '💎',
        items: [
            { name: 'Золото', rarity: 'common', value: 100, image: '🟡', exp: 20 },
            { name: 'Изумруд', rarity: 'rare', value: 300, image: '💚', exp: 40 },
            { name: 'Посох', rarity: 'epic', value: 800, image: '🪄', exp: 80 },
            { name: 'Феникс', rarity: 'legendary', value: 2000, image: '🔥', exp: 200 }
        ]
    },
    {
        id: 4,
        name: 'Платиновый',
        price: 1000,
        emoji: '👑',
        items: [
            { name: 'Платина', rarity: 'rare', value: 500, image: '⚪', exp: 50 },
            { name: 'Алмаз', rarity: 'epic', value: 1200, image: '💎', exp: 100 },
            { name: 'Щит', rarity: 'legendary', value: 3000, image: '🛡️', exp: 250 },
            { name: 'Единорог', rarity: 'legendary', value: 5000, image: '🦄', exp: 500 }
        ]
    }
];

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    await initApp();
});

async function initApp() {
    showLoading();
    
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
    
    // Запускаем регенерацию энергии
    startEnergyRegen();
    
    // Автосохранение каждые 10 секунд
    setInterval(() => saveGameData(), 10000);
    
    hideLoading();
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
    
    // Модальное окно
    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modalOverlay').addEventListener('click', closeModal);
    document.getElementById('openCaseBtn').addEventListener('click', openCase);
    
    // Приглашение друзей
    document.getElementById('inviteBtn').addEventListener('click', inviteFriend);
}

// Загрузка данных с сервера
async function loadGameData() {
    try {
        const response = await fetch(`${API_URL}/api/game_data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.userId })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Обновляем данные
            if (data.game_data) {
                userData = { ...userData, ...data.game_data };
            }
            if (data.balance !== undefined) {
                userData.balance = data.balance;
            }
            if (data.inventory) {
                inventory = data.inventory;
            }
            if (data.upgrades) {
                upgrades = data.upgrades;
            }
            if (data.achievements) {
                achievements = data.achievements;
            }
            
            // Получаем имя пользователя
            const userInfoResponse = await fetch(`${API_URL}/api/user_info`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userData.userId })
            });
            
            if (userInfoResponse.ok) {
                const userInfo = await userInfoResponse.json();
                if (userInfo.username || userInfo.first_name) {
                    userData.username = userInfo.username || userInfo.first_name;
                }
            }
        }
    } catch (error) {
        console.error('Error loading game data:', error);
        // Загружаем из localStorage как fallback
        loadFromLocalStorage();
    }
}

// Сохранение данных на сервер
async function saveGameData() {
    if (isLoading) return;
    
    try {
        await fetch(`${API_URL}/api/save_game_data`, {
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
                    energy: userData.energy,
                    max_energy: userData.maxEnergy,
                    last_energy_update: new Date().toISOString()
                },
                balance: userData.balance,
                upgrades: upgrades.map(u => ({ upgrade_id: u.id, level: u.level })),
                achievements: achievements.map(a => ({ id: a.id, progress: a.progress, unlocked: a.unlocked }))
            })
        });
        
        // Также сохраняем в localStorage
        saveToLocalStorage();
    } catch (error) {
        console.error('Error saving game data:', error);
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
    
    // Обновляем достижения
    updateAchievement('first_click', 1);
    updateAchievement('clicker_100', 1);
    updateAchievement('rich', userData.balance);
    
    // Показываем анимацию
    showTapAnimation(e, userData.coinsPerClick);
    
    // Обновляем UI
    updateUI();
    
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
    }, 1000);
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
    
    const caseBox = document.querySelector('.case-box-3d');
    caseBox.classList.remove('opening');
    
    const openBtn = document.getElementById('openCaseBtn');
    openBtn.disabled = false;
    openBtn.querySelector('.btn-text').textContent = 'Открыть кейс';
    
    document.getElementById('caseModal').classList.add('active');
}

function closeModal() {
    document.getElementById('caseModal').classList.remove('active');
    currentCase = null;
}

function openCase() {
    if (!currentCase || userData.balance < currentCase.price) {
        showNotification('Недостаточно средств!');
        return;
    }
    
    userData.balance -= currentCase.price;
    updateUI();
    
    const openBtn = document.getElementById('openCaseBtn');
    openBtn.disabled = true;
    openBtn.querySelector('.btn-text').textContent = 'Открываем...';
    
    const caseBox = document.querySelector('.case-box-3d');
    caseBox.classList.add('opening');
    
    tg.HapticFeedback.impactOccurred('medium');
    
    setTimeout(() => {
        const item = getRandomItem(currentCase.items);
        showCaseResult(item);
        
        userData.balance += item.value;
        addExp(item.exp);
        
        addToHistory(currentCase.name, item);
        updateAchievement('first_case', 1);
        updateAchievement('rich', userData.balance);
        
        updateUI();
        saveGameData();
        
        openBtn.disabled = false;
        openBtn.querySelector('.btn-text').textContent = 'Открыть еще';
    }, 1500);
}

function getRandomItem(items) {
    const chances = { common: 50, rare: 30, epic: 15, legendary: 5 };
    const rand = Math.random() * 100;
    let cumulative = 0;
    let rarity = 'common';
    
    for (const [r, chance] of Object.entries(chances)) {
        cumulative += chance;
        if (rand <= cumulative) {
            rarity = r;
            break;
        }
    }
    
    const filtered = items.filter(i => i.rarity === rarity);
    return filtered[Math.floor(Math.random() * filtered.length)] || items[0];
}

function showCaseResult(item) {
    document.getElementById('casePreview').style.display = 'none';
    
    const result = document.getElementById('caseResult');
    document.getElementById('resultRarity').className = `result-rarity ${item.rarity}`;
    document.getElementById('resultEmoji').textContent = item.image;
    document.getElementById('resultName').textContent = item.name;
    document.getElementById('resultValue').textContent = item.value;
    document.getElementById('resultExp').textContent = item.exp;
    
    result.style.display = 'block';
    
    tg.HapticFeedback.notificationOccurred(item.rarity === 'legendary' ? 'success' : 'warning');
}

// Улучшения
function loadUpgrades() {
    const upgradesList = document.getElementById('upgradesList');
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
    const userUpgrade = upgrades.find(u => u.upgrade_id === upgradeId) || { upgrade_id: upgradeId, level: 0 };
    const cost = Math.floor(upgrade.baseCost * Math.pow(upgrade.costMultiplier, userUpgrade.level));
    
    if (userData.balance < cost) {
        showNotification('Недостаточно средств!');
        return;
    }
    
    userData.balance -= cost;
    userUpgrade.level++;
    
    if (!upgrades.find(u => u.upgrade_id === upgradeId)) {
        upgrades.push(userUpgrade);
    }
    
    // Применяем эффект
    if (upgradeId === 'click_power') {
        userData.coinsPerClick += upgrade.effect;
    } else if (upgradeId === 'max_energy') {
        userData.maxEnergy += upgrade.effect;
    }
    
    updateAchievement('upgrader', upgrades.reduce((sum, u) => sum + u.level, 0));
    
    updateUI();
    loadUpgrades();
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

// Приглашение друзей
function inviteFriend() {
    const inviteLink = `https://t.me/share/url?url=https://t.me/${tg.initDataUnsafe?.bot?.username || 'yourbot'}?start=${userData.userId}`;
    tg.openTelegramLink(inviteLink);
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
    localStorage.setItem('userData', JSON.stringify(userData));
    localStorage.setItem('upgrades', JSON.stringify(upgrades));
    localStorage.setItem('achievements', JSON.stringify(achievements));
    localStorage.setItem('history', JSON.stringify(openHistory));
}

function loadFromLocalStorage() {
    const saved = localStorage.getItem('userData');
    if (saved) userData = { ...userData, ...JSON.parse(saved) };
    
    const savedUpgrades = localStorage.getItem('upgrades');
    if (savedUpgrades) upgrades = JSON.parse(savedUpgrades);
    
    const savedAch = localStorage.getItem('achievements');
    if (savedAch) achievements = JSON.parse(savedAch);
    
    const savedHistory = localStorage.getItem('history');
    if (savedHistory) openHistory = JSON.parse(savedHistory);
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

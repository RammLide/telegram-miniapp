// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;
tg.expand();

// Данные пользователя
let userData = {
    userId: tg.initDataUnsafe?.user?.id || 0,
    username: tg.initDataUnsafe?.user?.username || 'Guest',
    balance: 1000,
    level: 1,
    exp: 0,
    expToNextLevel: 100
};

// История открытий
let openHistory = [];

// Достижения
const achievements = [
    { id: 'first_case', name: 'Первый кейс', desc: 'Открой свой первый кейс', icon: '🎁', progress: 0, target: 1, unlocked: false },
    { id: 'case_master', name: 'Мастер кейсов', desc: 'Открой 10 кейсов', icon: '🏆', progress: 0, target: 10, unlocked: false },
    { id: 'lucky_one', name: 'Везунчик', desc: 'Получи легендарный предмет', icon: '⭐', progress: 0, target: 1, unlocked: false },
    { id: 'collector', name: 'Коллекционер', desc: 'Собери 20 предметов', icon: '📦', progress: 0, target: 20, unlocked: false },
    { id: 'rich', name: 'Богач', desc: 'Накопи 5000 монет', icon: '💰', progress: 0, target: 5000, unlocked: false },
    { id: 'level_5', name: 'Опытный', desc: 'Достигни 5 уровня', icon: '🌟', progress: 0, target: 5, unlocked: false }
];

// Данные кейсов
const cases = [
    {
        id: 1,
        name: 'Бронзовый кейс',
        price: 100,
        emoji: '🎁',
        items: [
            { name: 'Монета', rarity: 'common', value: 10, image: '🪙', exp: 5 },
            { name: 'Кристалл', rarity: 'rare', value: 50, image: '💎', exp: 15 },
            { name: 'Золото', rarity: 'epic', value: 150, image: '🏆', exp: 30 },
            { name: 'Легендарный меч', rarity: 'legendary', value: 500, image: '⚔️', exp: 100 }
        ]
    },
    {
        id: 2,
        name: 'Серебряный кейс',
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
        name: 'Золотой кейс',
        price: 500,
        emoji: '🎁',
        items: [
            { name: 'Золотая монета', rarity: 'common', value: 100, image: '🟡', exp: 20 },
            { name: 'Изумруд', rarity: 'rare', value: 300, image: '💚', exp: 40 },
            { name: 'Магический посох', rarity: 'epic', value: 800, image: '🪄', exp: 80 },
            { name: 'Феникс', rarity: 'legendary', value: 2000, image: '🔥', exp: 200 }
        ]
    },
    {
        id: 4,
        name: 'Платиновый кейс',
        price: 1000,
        emoji: '🎁',
        items: [
            { name: 'Платина', rarity: 'rare', value: 500, image: '⚪', exp: 50 },
            { name: 'Алмаз', rarity: 'epic', value: 1200, image: '💎', exp: 100 },
            { name: 'Легендарный щит', rarity: 'legendary', value: 3000, image: '🛡️', exp: 250 },
            { name: 'Единорог', rarity: 'legendary', value: 5000, image: '🦄', exp: 500 }
        ]
    }
];

// Инвентарь пользователя
let inventory = [];

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    loadProgress();
    loadHistoryData();
    loadAchievementsData();
    
    document.getElementById('username').textContent = userData.username;
    updateBalance();
    updateLevel();
    
    loadCases();
    loadInventory();
    loadHistory();
    loadAchievements();
    checkDailyBonus();
    
    // Обработчики навигации
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    
    // Обработчики модального окна
    document.getElementById('closeModal').addEventListener('click', closeModal);
    document.getElementById('openCaseBtn').addEventListener('click', openCase);
    document.getElementById('claimBonus').addEventListener('click', claimDailyBonus);
    
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('openModal');
        if (e.target === modal) closeModal();
    });
}

// Навигация
function switchTab(tabName) {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    if (tabName === 'inventory') loadInventoryDisplay();
    if (tabName === 'history') loadHistory();
    if (tabName === 'achievements') loadAchievements();
}

// Ежедневный бонус
function checkDailyBonus() {
    const lastClaim = localStorage.getItem('lastDailyBonus');
    const today = new Date().toDateString();
    
    if (lastClaim !== today) {
        document.getElementById('dailyBonus').classList.remove('claimed');
        document.getElementById('claimBonus').disabled = false;
    } else {
        document.getElementById('dailyBonus').classList.add('claimed');
        document.getElementById('claimBonus').disabled = true;
        document.querySelector('.bonus-text p').textContent = 'Возвращайся завтра!';
    }
}

function claimDailyBonus() {
    const bonus = 500;
    userData.balance += bonus;
    updateBalance();
    
    localStorage.setItem('lastDailyBonus', new Date().toDateString());
    document.getElementById('dailyBonus').classList.add('claimed');
    document.getElementById('claimBonus').disabled = true;
    document.querySelector('.bonus-text p').textContent = 'Возвращайся завтра!';
    
    tg.HapticFeedback.notificationOccurred('success');
    showNotification(`+${bonus} 💰 получено!`);
}

// Уровни и опыт
function updateLevel() {
    document.getElementById('level').textContent = userData.level;
    document.getElementById('expText').textContent = `${userData.exp} / ${userData.expToNextLevel} XP`;
    
    const progress = (userData.exp / userData.expToNextLevel) * 100;
    document.getElementById('expProgress').style.width = `${progress}%`;
}

function addExp(amount) {
    userData.exp += amount;
    
    while (userData.exp >= userData.expToNextLevel) {
        userData.exp -= userData.expToNextLevel;
        userData.level++;
        userData.expToNextLevel = Math.floor(userData.expToNextLevel * 1.5);
        
        showNotification(`🎉 Уровень повышен! Теперь ${userData.level} уровень!`);
        tg.HapticFeedback.notificationOccurred('success');
        
        // Проверка достижения
        updateAchievement('level_5', userData.level);
    }
    
    updateLevel();
    saveProgress();
}

// Загрузка кейсов
function loadCases() {
    const casesGrid = document.getElementById('casesGrid');
    casesGrid.innerHTML = '';
    
    cases.forEach(caseItem => {
        const caseCard = document.createElement('div');
        caseCard.className = 'case-card';
        caseCard.innerHTML = `
            <div class="case-emoji">${caseItem.emoji}</div>
            <h3>${caseItem.name}</h3>
            <p class="case-price">💰 ${caseItem.price}</p>
        `;
        caseCard.addEventListener('click', () => showCaseModal(caseItem));
        casesGrid.appendChild(caseCard);
    });
}

let currentCase = null;

function showCaseModal(caseItem) {
    currentCase = caseItem;
    const modal = document.getElementById('openModal');
    const caseTitle = document.getElementById('caseTitle');
    const result = document.getElementById('result');
    const openBtn = document.getElementById('openCaseBtn');
    const caseBox = document.querySelector('.case-box');
    
    caseTitle.textContent = caseItem.name;
    result.style.display = 'none';
    caseBox.classList.remove('opening');
    openBtn.disabled = false;
    
    const btnText = openBtn.querySelector('.btn-text');
    const btnPrice = openBtn.querySelector('.btn-price');
    btnText.textContent = 'Открыть кейс';
    btnPrice.textContent = `💰 ${caseItem.price}`;
    
    modal.style.display = 'block';
}

function closeModal() {
    const modal = document.getElementById('openModal');
    modal.style.display = 'none';
    currentCase = null;
}

function openCase() {
    if (!currentCase) return;
    
    if (userData.balance < currentCase.price) {
        tg.showAlert('Недостаточно средств!');
        return;
    }
    
    userData.balance -= currentCase.price;
    updateBalance();
    
    const openBtn = document.getElementById('openCaseBtn');
    const caseBox = document.querySelector('.case-box');
    const result = document.getElementById('result');
    
    openBtn.disabled = true;
    openBtn.querySelector('.btn-text').textContent = 'Открываем...';
    
    caseBox.classList.add('opening');
    tg.HapticFeedback.impactOccurred('medium');
    
    setTimeout(() => {
        const item = getRandomItem(currentCase.items);
        addToInventory(item);
        addToHistory(currentCase.name, item);
        showResult(item);
        
        // Обновление достижений
        updateAchievement('first_case', 1);
        updateAchievement('case_master', 1);
        if (item.rarity === 'legendary') updateAchievement('lucky_one', 1);
        updateAchievement('collector', inventory.length);
        updateAchievement('rich', userData.balance);
        
        openBtn.querySelector('.btn-text').textContent = 'Открыть еще раз';
        openBtn.disabled = false;
    }, 1500);
}

function getRandomItem(items) {
    const rarityChances = {
        common: 50,
        rare: 30,
        epic: 15,
        legendary: 5
    };
    
    const random = Math.random() * 100;
    let cumulativeChance = 0;
    let selectedRarity = 'common';
    
    for (const [rarity, chance] of Object.entries(rarityChances)) {
        cumulativeChance += chance;
        if (random <= cumulativeChance) {
            selectedRarity = rarity;
            break;
        }
    }
    
    const filteredItems = items.filter(item => item.rarity === selectedRarity);
    return filteredItems.length > 0 
        ? filteredItems[Math.floor(Math.random() * filteredItems.length)]
        : items[0];
}

function showResult(item) {
    const result = document.getElementById('result');
    const itemRarity = document.getElementById('itemRarity');
    const itemImage = document.getElementById('itemImage');
    const itemName = document.getElementById('itemName');
    const itemValue = document.getElementById('itemValue');
    const itemExp = document.getElementById('itemExp');
    
    itemRarity.className = `item-rarity ${item.rarity}`;
    itemImage.textContent = item.image;
    itemName.textContent = item.name;
    itemValue.textContent = item.value;
    itemExp.textContent = item.exp;
    
    result.style.display = 'block';
    
    userData.balance += item.value;
    updateBalance();
    
    addExp(item.exp);
    
    tg.HapticFeedback.notificationOccurred(item.rarity === 'legendary' ? 'success' : 'warning');
    
    if (item.rarity === 'legendary') {
        createConfetti();
    }
}

function createConfetti() {
    const confetti = document.querySelector('.confetti');
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: absolute;
            width: 10px;
            height: 10px;
            background: ${['#ffd700', '#ff6b6b', '#4ade80', '#60a5fa'][Math.floor(Math.random() * 4)]};
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            animation: confettiFall ${1 + Math.random() * 2}s ease-out forwards;
            border-radius: 50%;
        `;
        confetti.appendChild(particle);
        setTimeout(() => particle.remove(), 3000);
    }
}

// Инвентарь
function addToInventory(item) {
    const existingItem = inventory.find(i => i.name === item.name);
    
    if (existingItem) {
        existingItem.count++;
    } else {
        inventory.push({ ...item, count: 1 });
    }
    
    saveInventory();
}

function loadInventoryDisplay() {
    const inventoryGrid = document.getElementById('inventoryGrid');
    inventoryGrid.innerHTML = '';
    
    if (inventory.length === 0) {
        inventoryGrid.innerHTML = '<div class="empty-inventory">Ваш инвентарь пуст<br>Открой кейс, чтобы получить предметы!</div>';
        document.getElementById('itemCount').textContent = '0';
        document.getElementById('totalValue').textContent = '0';
        return;
    }
    
    let totalValue = 0;
    let totalItems = 0;
    
    inventory.forEach(item => {
        totalValue += item.value * item.count;
        totalItems += item.count;
        
        const itemCard = document.createElement('div');
        itemCard.className = 'inventory-item';
        itemCard.innerHTML = `
            <div class="item-emoji">${item.image}</div>
            <h4>${item.name}</h4>
            <p class="item-count">x${item.count}</p>
            <p style="color: #ffd700; font-size: 0.9em;">💎 ${item.value}</p>
        `;
        inventoryGrid.appendChild(itemCard);
    });
    
    document.getElementById('itemCount').textContent = totalItems;
    document.getElementById('totalValue').textContent = totalValue;
}

// История
function addToHistory(caseName, item) {
    const historyItem = {
        caseName,
        item,
        timestamp: Date.now()
    };
    
    openHistory.unshift(historyItem);
    if (openHistory.length > 50) openHistory.pop();
    
    saveHistory();
}

function loadHistory() {
    const historyList = document.getElementById('historyList');
    historyList.innerHTML = '';
    
    if (openHistory.length === 0) {
        historyList.innerHTML = '<div class="empty-inventory">История пуста</div>';
        return;
    }
    
    openHistory.slice(0, 20).forEach(entry => {
        const historyItem = document.createElement('div');
        historyItem.className = `history-item ${entry.item.rarity}`;
        
        const timeAgo = getTimeAgo(entry.timestamp);
        
        historyItem.innerHTML = `
            <div class="history-icon">${entry.item.image}</div>
            <div class="history-info">
                <h4>${entry.item.name}</h4>
                <p class="history-time">${entry.caseName} • ${timeAgo}</p>
            </div>
            <div class="history-value">💎 ${entry.item.value}</div>
        `;
        historyList.appendChild(historyItem);
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
    
    achievements.forEach(achievement => {
        const card = document.createElement('div');
        card.className = `achievement-card ${achievement.unlocked ? 'unlocked' : 'locked'}`;
        
        const progress = Math.min((achievement.progress / achievement.target) * 100, 100);
        
        card.innerHTML = `
            <div class="achievement-icon">${achievement.icon}</div>
            <h3>${achievement.name}</h3>
            <p>${achievement.desc}</p>
            <div class="achievement-progress">
                <div class="achievement-progress-fill" style="width: ${progress}%"></div>
            </div>
            <p style="text-align: center; margin-top: 5px; font-size: 0.9em;">
                ${achievement.progress} / ${achievement.target}
            </p>
        `;
        achievementsGrid.appendChild(card);
    });
}

function updateAchievement(id, value) {
    const achievement = achievements.find(a => a.id === id);
    if (!achievement || achievement.unlocked) return;
    
    achievement.progress = Math.min(achievement.progress + value, achievement.target);
    
    if (achievement.progress >= achievement.target && !achievement.unlocked) {
        achievement.unlocked = true;
        showNotification(`🏆 Достижение разблокировано: ${achievement.name}!`);
        tg.HapticFeedback.notificationOccurred('success');
    }
    
    saveAchievements();
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
        color: #fff;
        padding: 15px 30px;
        border-radius: 10px;
        font-weight: bold;
        z-index: 10000;
        animation: slideDown 0.3s ease-out;
    `;
    notification.textContent = text;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideUp 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Сохранение/загрузка
function updateBalance() {
    document.getElementById('balance').textContent = userData.balance;
    saveProgress();
}

function saveProgress() {
    localStorage.setItem('userData', JSON.stringify(userData));
}

function loadProgress() {
    const saved = localStorage.getItem('userData');
    if (saved) {
        const data = JSON.parse(saved);
        userData.balance = data.balance || 1000;
        userData.level = data.level || 1;
        userData.exp = data.exp || 0;
        userData.expToNextLevel = data.expToNextLevel || 100;
    }
}

function saveInventory() {
    localStorage.setItem('inventory', JSON.stringify(inventory));
}

function loadInventory() {
    const saved = localStorage.getItem('inventory');
    if (saved) inventory = JSON.parse(saved);
}

function saveHistory() {
    localStorage.setItem('history', JSON.stringify(openHistory));
}

function loadHistoryData() {
    const saved = localStorage.getItem('history');
    if (saved) openHistory = JSON.parse(saved);
}

function saveAchievements() {
    localStorage.setItem('achievements', JSON.stringify(achievements));
}

function loadAchievementsData() {
    const saved = localStorage.getItem('achievements');
    if (saved) {
        const savedAch = JSON.parse(saved);
        savedAch.forEach((saved, index) => {
            if (achievements[index]) {
                achievements[index].progress = saved.progress;
                achievements[index].unlocked = saved.unlocked;
            }
        });
    }
}

// Добавляем стили для анимаций
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
    @keyframes confettiFall {
        to { transform: translateY(100vh) rotate(360deg); opacity: 0; }
    }
`;
document.head.appendChild(style);

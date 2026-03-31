// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;
tg.expand();

// Данные пользователя
let userData = {
    userId: tg.initDataUnsafe?.user?.id || 0,
    username: tg.initDataUnsafe?.user?.username || 'Guest',
    balance: 1000
};

// Данные кейсов
const cases = [
    {
        id: 1,
        name: 'Бронзовый кейс',
        price: 100,
        image: '🎁',
        items: [
            { name: 'Монета', rarity: 'common', value: 10, image: '🪙' },
            { name: 'Кристалл', rarity: 'rare', value: 50, image: '💎' },
            { name: 'Золото', rarity: 'epic', value: 150, image: '🏆' },
            { name: 'Легендарный меч', rarity: 'legendary', value: 500, image: '⚔️' }
        ]
    },
    {
        id: 2,
        name: 'Серебряный кейс',
        price: 250,
        image: '🎁',
        items: [
            { name: 'Серебро', rarity: 'common', value: 50, image: '🥈' },
            { name: 'Рубин', rarity: 'rare', value: 150, image: '💍' },
            { name: 'Корона', rarity: 'epic', value: 400, image: '👑' },
            { name: 'Дракон', rarity: 'legendary', value: 1000, image: '🐉' }
        ]
    },
    {
        id: 3,
        name: 'Золотой кейс',
        price: 500,
        image: '🎁',
        items: [
            { name: 'Золотая монета', rarity: 'common', value: 100, image: '🟡' },
            { name: 'Изумруд', rarity: 'rare', value: 300, image: '💚' },
            { name: 'Магический посох', rarity: 'epic', value: 800, image: '🪄' },
            { name: 'Феникс', rarity: 'legendary', value: 2000, image: '🔥' }
        ]
    },
    {
        id: 4,
        name: 'Платиновый кейс',
        price: 1000,
        image: '🎁',
        items: [
            { name: 'Платина', rarity: 'rare', value: 500, image: '⚪' },
            { name: 'Алмаз', rarity: 'epic', value: 1200, image: '💎' },
            { name: 'Легендарный щит', rarity: 'legendary', value: 3000, image: '🛡️' },
            { name: 'Единорог', rarity: 'legendary', value: 5000, image: '🦄' }
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
    // Устанавливаем имя пользователя
    document.getElementById('username').textContent = userData.username;
    updateBalance();
    
    // Загружаем кейсы
    loadCases();
    
    // Загружаем инвентарь из localStorage
    loadInventory();
    
    // Обработчики событий
    document.getElementById('closeModal').addEventListener('click', closeModal);
    document.getElementById('openCaseBtn').addEventListener('click', openCase);
    
    // Закрытие модального окна при клике вне его
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('openModal');
        if (e.target === modal) {
            closeModal();
        }
    });
}

function loadCases() {
    const casesGrid = document.getElementById('casesGrid');
    casesGrid.innerHTML = '';
    
    cases.forEach(caseItem => {
        const caseCard = document.createElement('div');
        caseCard.className = 'case-card';
        caseCard.innerHTML = `
            <div style="font-size: 80px;">${caseItem.image}</div>
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
    openBtn.textContent = `Открыть за ${caseItem.price} 💰`;
    
    modal.style.display = 'block';
}

function closeModal() {
    const modal = document.getElementById('openModal');
    modal.style.display = 'none';
    currentCase = null;
}

function openCase() {
    if (!currentCase) return;
    
    // Проверяем баланс
    if (userData.balance < currentCase.price) {
        tg.showAlert('Недостаточно средств!');
        return;
    }
    
    // Списываем средства
    userData.balance -= currentCase.price;
    updateBalance();
    
    const openBtn = document.getElementById('openCaseBtn');
    const caseBox = document.querySelector('.case-box');
    const result = document.getElementById('result');
    
    openBtn.disabled = true;
    openBtn.textContent = 'Открываем...';
    
    // Анимация открытия
    caseBox.classList.add('opening');
    
    setTimeout(() => {
        // Определяем выпавший предмет
        const item = getRandomItem(currentCase.items);
        
        // Добавляем в инвентарь
        addToInventory(item);
        
        // Показываем результат
        showResult(item);
        
        openBtn.textContent = 'Открыть еще раз';
        openBtn.disabled = false;
    }, 1000);
}

function getRandomItem(items) {
    // Шансы выпадения по редкости
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
    
    // Фильтруем предметы по редкости
    const filteredItems = items.filter(item => item.rarity === selectedRarity);
    
    if (filteredItems.length === 0) {
        return items[0];
    }
    
    return filteredItems[Math.floor(Math.random() * filteredItems.length)];
}

function showResult(item) {
    const result = document.getElementById('result');
    const itemRarity = document.getElementById('itemRarity');
    const itemImage = document.getElementById('itemImage');
    const itemName = document.getElementById('itemName');
    const itemValue = document.getElementById('itemValue');
    
    itemRarity.className = `item-rarity ${item.rarity}`;
    itemImage.textContent = item.image;
    itemImage.style.fontSize = '100px';
    itemName.textContent = item.name;
    itemValue.textContent = item.value;
    
    result.style.display = 'block';
    
    // Добавляем баланс за предмет
    userData.balance += item.value;
    updateBalance();
    
    // Вибрация
    tg.HapticFeedback.impactOccurred('medium');
}

function addToInventory(item) {
    const existingItem = inventory.find(i => i.name === item.name);
    
    if (existingItem) {
        existingItem.count++;
    } else {
        inventory.push({ ...item, count: 1 });
    }
    
    saveInventory();
    loadInventoryDisplay();
}

function loadInventoryDisplay() {
    const inventoryGrid = document.getElementById('inventoryGrid');
    inventoryGrid.innerHTML = '';
    
    if (inventory.length === 0) {
        inventoryGrid.innerHTML = '<div class="empty-inventory">Ваш инвентарь пуст</div>';
        return;
    }
    
    inventory.forEach(item => {
        const itemCard = document.createElement('div');
        itemCard.className = 'inventory-item';
        itemCard.innerHTML = `
            <div style="font-size: 50px;">${item.image}</div>
            <h4>${item.name}</h4>
            <p class="item-count">x${item.count}</p>
            <p style="color: #ffd700; font-size: 0.9em;">💎 ${item.value}</p>
        `;
        inventoryGrid.appendChild(itemCard);
    });
}

function updateBalance() {
    document.getElementById('balance').textContent = userData.balance;
    saveBalance();
}

function saveInventory() {
    localStorage.setItem('inventory', JSON.stringify(inventory));
}

function loadInventory() {
    const saved = localStorage.getItem('inventory');
    if (saved) {
        inventory = JSON.parse(saved);
    }
    loadInventoryDisplay();
}

function saveBalance() {
    localStorage.setItem('balance', userData.balance);
}

function loadBalance() {
    const saved = localStorage.getItem('balance');
    if (saved) {
        userData.balance = parseInt(saved);
    }
}

// Загружаем баланс при старте
loadBalance();

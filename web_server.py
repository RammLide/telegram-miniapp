from aiohttp import web
import json
import logging

logger = logging.getLogger(__name__)

# Импортируем функции из database
from database import (
    get_user_balance,
    update_user_balance,
    subtract_balance,
    add_balance,
    add_item_to_inventory,
    get_user_inventory,
    log_case_opening,
    get_case_opening_stats,
    get_user_game_data,
    update_user_game_data,
    get_user_upgrades,
    update_user_upgrade,
    get_user_achievements_db,
    update_user_achievement,
    get_user_info,
    get_referral_code,
    get_referrals_count,
    get_referrals_earned,
    get_referrals_list,
    get_leaderboard,
    get_user_rank,
    update_rating_score,
    create_marketplace_listing,
    get_marketplace_listings,
    buy_marketplace_item,
    cancel_marketplace_listing,
    get_user_marketplace_listings
)

# Данные кейсов (те же, что в app.js)
CASES = [
    {
        "id": 1,
        "name": "Бронзовый кейс",
        "price": 100,
        "items": [
            {"name": "Монета", "rarity": "common", "value": 10, "image": "🪙", "chance": 50},
            {"name": "Кристалл", "rarity": "rare", "value": 50, "image": "💎", "chance": 30},
            {"name": "Золото", "rarity": "epic", "value": 150, "image": "🏆", "chance": 15},
            {"name": "Легендарный меч", "rarity": "legendary", "value": 500, "image": "⚔️", "chance": 5}
        ]
    },
    {
        "id": 2,
        "name": "Серебряный кейс",
        "price": 250,
        "items": [
            {"name": "Серебро", "rarity": "common", "value": 50, "image": "🥈", "chance": 50},
            {"name": "Рубин", "rarity": "rare", "value": 150, "image": "💍", "chance": 30},
            {"name": "Корона", "rarity": "epic", "value": 400, "image": "👑", "chance": 15},
            {"name": "Дракон", "rarity": "legendary", "value": 1000, "image": "🐉", "chance": 5}
        ]
    },
    {
        "id": 3,
        "name": "Золотой кейс",
        "price": 500,
        "items": [
            {"name": "Золотая монета", "rarity": "common", "value": 100, "image": "🟡", "chance": 50},
            {"name": "Изумруд", "rarity": "rare", "value": 300, "image": "💚", "chance": 30},
            {"name": "Магический посох", "rarity": "epic", "value": 800, "image": "🪄", "chance": 15},
            {"name": "Феникс", "rarity": "legendary", "value": 2000, "image": "🔥", "chance": 5}
        ]
    },
    {
        "id": 4,
        "name": "Платиновый кейс",
        "price": 1000,
        "items": [
            {"name": "Платина", "rarity": "rare", "value": 500, "image": "⚪", "chance": 40},
            {"name": "Алмаз", "rarity": "epic", "value": 1200, "image": "💎", "chance": 35},
            {"name": "Легендарный щит", "rarity": "legendary", "value": 3000, "image": "🛡️", "chance": 20},
            {"name": "Единорог", "rarity": "legendary", "value": 5000, "image": "🦄", "chance": 5}
        ]
    },
    {
        "id": 5,
        "name": "Алмазный кейс",
        "price": 2000,
        "items": [
            {"name": "Сапфир", "rarity": "rare", "value": 800, "image": "🔷", "chance": 40},
            {"name": "Топаз", "rarity": "epic", "value": 1800, "image": "🟨", "chance": 35},
            {"name": "Трон", "rarity": "legendary", "value": 4500, "image": "🪑", "chance": 20},
            {"name": "Грифон", "rarity": "legendary", "value": 8000, "image": "🦅", "chance": 5}
        ]
    },
    {
        "id": 6,
        "name": "Мифический кейс",
        "price": 5000,
        "items": [
            {"name": "Опал", "rarity": "epic", "value": 3000, "image": "🔮", "chance": 45},
            {"name": "Скипетр", "rarity": "legendary", "value": 7000, "image": "👑", "chance": 30},
            {"name": "Дракон-король", "rarity": "legendary", "value": 12000, "image": "🐲", "chance": 20},
            {"name": "Экскалибур", "rarity": "legendary", "value": 20000, "image": "⚔️", "chance": 5}
        ]
    },
    {
        "id": 7,
        "name": "Божественный кейс",
        "price": 10000,
        "items": [
            {"name": "Нефрит", "rarity": "epic", "value": 6000, "image": "🟢", "chance": 45},
            {"name": "Крылья ангела", "rarity": "legendary", "value": 15000, "image": "🪽", "chance": 30},
            {"name": "Молот Тора", "rarity": "legendary", "value": 25000, "image": "🔨", "chance": 20},
            {"name": "Корона богов", "rarity": "legendary", "value": 50000, "image": "👑", "chance": 5}
        ]
    }
]


async def get_balance(request):
    """Получение баланса пользователя"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        balance = await get_user_balance(user_id)
        return web.json_response({'balance': balance})
    
    except Exception as e:
        logger.error(f"Error in get_balance: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def open_case_endpoint(request):
    """Открытие кейса"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        case_id = data.get('case_id')
        
        if not user_id or not case_id:
            return web.json_response({'error': 'user_id and case_id required'}, status=400)
        
        # Находим кейс
        case = next((c for c in CASES if c['id'] == case_id), None)
        if not case:
            return web.json_response({'error': 'Case not found'}, status=404)
        
        # Проверяем баланс
        balance = await get_user_balance(user_id)
        if balance < case['price']:
            return web.json_response({'error': 'Insufficient balance'}, status=400)
        
        # Списываем средства
        success = await subtract_balance(user_id, case['price'])
        if not success:
            return web.json_response({'error': 'Failed to subtract balance'}, status=500)
        
        # Определяем выпавший предмет
        import random
        rand = random.random() * 100
        cumulative = 0
        selected_item = case['items'][0]
        
        for item in case['items']:
            cumulative += item['chance']
            if rand <= cumulative:
                selected_item = item
                break
        
        # Добавляем предмет в инвентарь
        await add_item_to_inventory(
            user_id,
            selected_item['name'],
            selected_item['rarity'],
            selected_item['value'],
            selected_item['image']
        )
        
        # Добавляем стоимость предмета к балансу (с начислением процента реферу)
        logger.info(f"💰 Adding {selected_item['value']} to user {user_id} balance")
        await add_balance(user_id, selected_item['value'], give_referrer_bonus=True)
        
        # Логируем открытие
        await log_case_opening(user_id, case['name'], selected_item['name'], selected_item['value'])
        
        # Получаем новый баланс
        new_balance = await get_user_balance(user_id)
        
        return web.json_response({
            'item': selected_item,
            'balance': new_balance
        })
    
    except Exception as e:
        logger.error(f"Error in open_case: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def get_inventory_endpoint(request):
    """Получение инвентаря пользователя"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        inventory = await get_user_inventory(user_id)
        return web.json_response({'inventory': inventory})
    
    except Exception as e:
        logger.error(f"Error in get_inventory: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def get_stats_endpoint(request):
    """Получение статистики пользователя"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        stats = await get_case_opening_stats(user_id)
        return web.json_response(stats)
    
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        return web.json_response({'error': str(e)}, status=500)


def setup_routes(app):
    """Настройка маршрутов API"""
    app.router.add_post('/api/balance', get_balance)
    app.router.add_post('/api/open_case', open_case_endpoint)
    app.router.add_post('/api/inventory', get_inventory_endpoint)
    app.router.add_post('/api/stats', get_stats_endpoint)
    app.router.add_post('/api/game_data', get_game_data_endpoint)
    app.router.add_post('/api/save_game_data', save_game_data_endpoint)
    app.router.add_post('/api/user_info', get_user_info_endpoint)
    app.router.add_post('/api/referral_data', get_referral_data_endpoint)
    app.router.add_post('/api/leaderboard', get_leaderboard_endpoint)
    app.router.add_post('/api/marketplace/listings', get_marketplace_listings_endpoint)
    app.router.add_post('/api/marketplace/create', create_marketplace_listing_endpoint)
    app.router.add_post('/api/marketplace/buy', buy_marketplace_item_endpoint)
    app.router.add_post('/api/marketplace/cancel', cancel_marketplace_listing_endpoint)
    app.router.add_post('/api/marketplace/my_listings', get_user_marketplace_listings_endpoint)
    
    # Статические файлы для Mini App
    app.router.add_static('/webapp/', path='webapp/', name='webapp')


async def get_game_data_endpoint(request):
    """Получение всех игровых данных пользователя"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        # Получаем все данные
        game_data = await get_user_game_data(user_id)
        balance = await get_user_balance(user_id)
        inventory = await get_user_inventory(user_id)
        upgrades = await get_user_upgrades(user_id)
        achievements = await get_user_achievements_db(user_id)
        referral_code = await get_referral_code(user_id)
        
        return web.json_response({
            'game_data': game_data,
            'balance': balance,
            'inventory': inventory,
            'upgrades': upgrades,
            'achievements': achievements,
            'referral_code': referral_code
        })
    
    except Exception as e:
        logger.error(f"Error in get_game_data: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def save_game_data_endpoint(request):
    """Сохранение игровых данных пользователя"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            logger.error("save_game_data: user_id not provided")
            return web.json_response({'error': 'user_id required'}, status=400)
        
        logger.info(f"💾 Saving game data for user {user_id}")
        
        # Сохраняем игровые данные
        if 'game_data' in data:
            await update_user_game_data(user_id, data['game_data'])
            logger.info(f"✅ Game data saved for user {user_id}")
        
        # Сохраняем баланс и начисляем процент реферу
        if 'balance' in data:
            # Получаем текущий баланс
            old_balance = await get_user_balance(user_id)
            new_balance = data['balance']
            
            # Если баланс увеличился, начисляем процент реферу
            if new_balance > old_balance:
                balance_diff = new_balance - old_balance
                logger.info(f"💰 Balance increased by {balance_diff} for user {user_id}")
                
                # Начисляем процент реферу
                from database import give_referrer_percentage
                await give_referrer_percentage(user_id, balance_diff)
            
            await update_user_balance(user_id, new_balance)
            logger.info(f"✅ Balance saved for user {user_id}: {new_balance}")
        
        # Сохраняем улучшения
        if 'upgrades' in data:
            for upgrade in data['upgrades']:
                await update_user_upgrade(user_id, upgrade['upgrade_id'], upgrade['level'])
            logger.info(f"✅ Upgrades saved for user {user_id}")
        
        # Сохраняем достижения
        if 'achievements' in data:
            for achievement in data['achievements']:
                await update_user_achievement(
                    user_id,
                    achievement['id'],
                    achievement['progress'],
                    achievement['unlocked']
                )
            logger.info(f"✅ Achievements saved for user {user_id}")
        
        logger.info(f"✅ All data saved successfully for user {user_id}")
        return web.json_response({'success': True})
    
    except Exception as e:
        logger.error(f"❌ Error in save_game_data for user {user_id}: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def get_user_info_endpoint(request):
    """Получение информации о пользователе"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        user_info = await get_user_info(user_id)
        
        if user_info:
            return web.json_response({
                'username': user_info.get('username'),
                'first_name': user_info.get('first_name'),
                'last_name': user_info.get('last_name')
            })
        else:
            return web.json_response({'error': 'User not found'}, status=404)
    
    except Exception as e:
        logger.error(f"Error in get_user_info: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def get_referral_data_endpoint(request):
    """Получение реферальных данных пользователя"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        referral_code = await get_referral_code(user_id)
        referrals_count = await get_referrals_count(user_id)
        referrals_earned = await get_referrals_earned(user_id)
        referrals_list = await get_referrals_list(user_id)
        
        return web.json_response({
            'referral_code': referral_code,
            'referrals_count': referrals_count,
            'referrals_earned': referrals_earned,
            'referrals_list': referrals_list
        })
    
    except Exception as e:
        logger.error(f"Error in get_referral_data: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def get_leaderboard_endpoint(request):
    """Получение рейтинга игроков"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        limit = data.get('limit', 100)
        
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        leaderboard = await get_leaderboard(limit)
        user_rank = await get_user_rank(user_id)
        
        return web.json_response({
            'leaderboard': leaderboard,
            'user_rank': user_rank
        })
    
    except Exception as e:
        logger.error(f"Error in get_leaderboard: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def get_marketplace_listings_endpoint(request):
    """Получение списка товаров на торговой площадке"""
    try:
        data = await request.json()
        limit = data.get('limit', 50)
        
        listings = await get_marketplace_listings(limit)
        return web.json_response({'listings': listings})
    
    except Exception as e:
        logger.error(f"Error in get_marketplace_listings: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def create_marketplace_listing_endpoint(request):
    """Создание объявления на торговой площадке"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        item_name = data.get('item_name')
        item_rarity = data.get('item_rarity')
        item_value = data.get('item_value')
        item_image = data.get('item_image')
        price = data.get('price')
        
        if not all([user_id, item_name, item_rarity, item_value, item_image, price]):
            return web.json_response({'error': 'Missing required fields'}, status=400)
        
        success = await create_marketplace_listing(user_id, item_name, item_rarity, item_value, item_image, price)
        
        if success:
            return web.json_response({'success': True})
        else:
            return web.json_response({'error': 'Item not found in inventory'}, status=400)
    
    except Exception as e:
        logger.error(f"Error in create_marketplace_listing: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def buy_marketplace_item_endpoint(request):
    """Покупка предмета с торговой площадки"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        listing_id = data.get('listing_id')
        
        if not user_id or not listing_id:
            return web.json_response({'error': 'user_id and listing_id required'}, status=400)
        
        success = await buy_marketplace_item(user_id, listing_id)
        
        if success:
            new_balance = await get_user_balance(user_id)
            return web.json_response({'success': True, 'balance': new_balance})
        else:
            return web.json_response({'error': 'Purchase failed'}, status=400)
    
    except Exception as e:
        logger.error(f"Error in buy_marketplace_item: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def cancel_marketplace_listing_endpoint(request):
    """Отмена объявления на торговой площадке"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        listing_id = data.get('listing_id')
        
        if not user_id or not listing_id:
            return web.json_response({'error': 'user_id and listing_id required'}, status=400)
        
        success = await cancel_marketplace_listing(user_id, listing_id)
        
        if success:
            return web.json_response({'success': True})
        else:
            return web.json_response({'error': 'Cancellation failed'}, status=400)
    
    except Exception as e:
        logger.error(f"Error in cancel_marketplace_listing: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def get_user_marketplace_listings_endpoint(request):
    """Получение объявлений пользователя"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        listings = await get_user_marketplace_listings(user_id)
        return web.json_response({'listings': listings})
    
    except Exception as e:
        logger.error(f"Error in get_user_marketplace_listings: {e}")
        return web.json_response({'error': str(e)}, status=500)

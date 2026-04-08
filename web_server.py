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
            {"name": "50 монет", "rarity": "common", "value": 50, "image": "💰", "chance": 35, "type": "money"},
            {"name": "Монета", "rarity": "common", "value": 10, "image": "🪙", "chance": 25, "type": "item"},
            {"name": "Кристалл", "rarity": "rare", "value": 50, "image": "💎", "chance": 20, "type": "item"},
            {"name": "200 монет", "rarity": "rare", "value": 200, "image": "💵", "chance": 10, "type": "money"},
            {"name": "Золото", "rarity": "epic", "value": 150, "image": "🏆", "chance": 7, "type": "item"},
            {"name": "Меч", "rarity": "legendary", "value": 500, "image": "⚔️", "chance": 3, "type": "item"}
        ]
    },
    {
        "id": 2,
        "name": "Серебряный кейс",
        "price": 250,
        "items": [
            {"name": "150 монет", "rarity": "common", "value": 150, "image": "💰", "chance": 30, "type": "money"},
            {"name": "Серебро", "rarity": "common", "value": 50, "image": "🥈", "chance": 25, "type": "item"},
            {"name": "Рубин", "rarity": "rare", "value": 150, "image": "💍", "chance": 20, "type": "item"},
            {"name": "500 монет", "rarity": "rare", "value": 500, "image": "💵", "chance": 12, "type": "money"},
            {"name": "Корона", "rarity": "epic", "value": 400, "image": "👑", "chance": 10, "type": "item"},
            {"name": "Дракон", "rarity": "legendary", "value": 1000, "image": "🐉", "chance": 3, "type": "item"}
        ]
    },
    {
        "id": 3,
        "name": "Золотой кейс",
        "price": 500,
        "items": [
            {"name": "300 монет", "rarity": "common", "value": 300, "image": "💰", "chance": 30, "type": "money"},
            {"name": "Золото", "rarity": "common", "value": 100, "image": "🟡", "chance": 25, "type": "item"},
            {"name": "Изумруд", "rarity": "rare", "value": 300, "image": "💚", "chance": 20, "type": "item"},
            {"name": "1000 монет", "rarity": "rare", "value": 1000, "image": "💵", "chance": 12, "type": "money"},
            {"name": "Посох", "rarity": "epic", "value": 800, "image": "🪄", "chance": 10, "type": "item"},
            {"name": "Феникс", "rarity": "legendary", "value": 2000, "image": "🔥", "chance": 3, "type": "item"}
        ]
    },
    {
        "id": 4,
        "name": "Платиновый кейс",
        "price": 1000,
        "items": [
            {"name": "800 монет", "rarity": "rare", "value": 800, "image": "💰", "chance": 25, "type": "money"},
            {"name": "Платина", "rarity": "rare", "value": 500, "image": "⚪", "chance": 25, "type": "item"},
            {"name": "Алмаз", "rarity": "epic", "value": 1200, "image": "💎", "chance": 20, "type": "item"},
            {"name": "2500 монет", "rarity": "epic", "value": 2500, "image": "💵", "chance": 15, "type": "money"},
            {"name": "Щит", "rarity": "legendary", "value": 3000, "image": "🛡️", "chance": 12, "type": "item"},
            {"name": "Единорог", "rarity": "legendary", "value": 5000, "image": "🦄", "chance": 3, "type": "item"}
        ]
    },
    {
        "id": 5,
        "name": "Алмазный кейс",
        "price": 2000,
        "items": [
            {"name": "1500 монет", "rarity": "rare", "value": 1500, "image": "💰", "chance": 25, "type": "money"},
            {"name": "Сапфир", "rarity": "rare", "value": 800, "image": "🔷", "chance": 25, "type": "item"},
            {"name": "Топаз", "rarity": "epic", "value": 1800, "image": "🟨", "chance": 20, "type": "item"},
            {"name": "4000 монет", "rarity": "epic", "value": 4000, "image": "💵", "chance": 15, "type": "money"},
            {"name": "Трон", "rarity": "legendary", "value": 4500, "image": "🪑", "chance": 12, "type": "item"},
            {"name": "Грифон", "rarity": "legendary", "value": 8000, "image": "🦅", "chance": 3, "type": "item"}
        ]
    },
    {
        "id": 6,
        "name": "Мифический кейс",
        "price": 5000,
        "items": [
            {"name": "3500 монет", "rarity": "epic", "value": 3500, "image": "💰", "chance": 25, "type": "money"},
            {"name": "Опал", "rarity": "epic", "value": 3000, "image": "🔮", "chance": 25, "type": "item"},
            {"name": "Скипетр", "rarity": "legendary", "value": 7000, "image": "👑", "chance": 20, "type": "item"},
            {"name": "10000 монет", "rarity": "legendary", "value": 10000, "image": "💵", "chance": 15, "type": "money"},
            {"name": "Дракон-король", "rarity": "legendary", "value": 12000, "image": "🐲", "chance": 12, "type": "item"},
            {"name": "Экскалибур", "rarity": "legendary", "value": 20000, "image": "⚔️", "chance": 3, "type": "item"}
        ]
    },
    {
        "id": 7,
        "name": "Божественный кейс",
        "price": 10000,
        "items": [
            {"name": "7000 монет", "rarity": "epic", "value": 7000, "image": "💰", "chance": 25, "type": "money"},
            {"name": "Нефрит", "rarity": "epic", "value": 6000, "image": "🟢", "chance": 25, "type": "item"},
            {"name": "Крылья ангела", "rarity": "legendary", "value": 15000, "image": "🪽", "chance": 20, "type": "item"},
            {"name": "20000 монет", "rarity": "legendary", "value": 20000, "image": "💵", "chance": 15, "type": "money"},
            {"name": "Молот Тора", "rarity": "legendary", "value": 25000, "image": "🔨", "chance": 12, "type": "item"},
            {"name": "Корона богов", "rarity": "legendary", "value": 50000, "image": "👑", "chance": 3, "type": "item"}
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
        
        # Логируем открытие
        await log_case_opening(user_id, case['name'], selected_item['name'], selected_item['value'])
        
        # Получаем новый баланс (после списания за кейс)
        new_balance = await get_user_balance(user_id)
        
        # Возвращаем предмет БЕЗ автоматического начисления
        # Пользователь сам выберет: оставить или продать
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
    app.router.add_post('/api/check_ban', check_ban_endpoint)
    app.router.add_post('/api/marketplace/listings', get_marketplace_listings_endpoint)
    app.router.add_post('/api/marketplace/create', create_marketplace_listing_endpoint)
    app.router.add_post('/api/marketplace/buy', buy_marketplace_item_endpoint)
    app.router.add_post('/api/marketplace/cancel', cancel_marketplace_listing_endpoint)
    app.router.add_post('/api/marketplace/my_listings', get_user_marketplace_listings_endpoint)
    app.router.add_post('/api/case_reward_choice', case_reward_choice_endpoint)
    app.router.add_post('/api/quick_sell_item', quick_sell_item_endpoint)
    app.router.add_post('/api/turbo_pass', get_turbo_pass_endpoint)
    app.router.add_post('/api/turbo_pass/claim', claim_turbo_pass_endpoint)
    app.router.add_post('/api/check_updates', check_updates_endpoint)
    
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


async def check_ban_endpoint(request):
    """Проверка блокировки пользователя"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        from database import is_user_banned
        is_banned, reason = await is_user_banned(user_id)
        
        return web.json_response({
            'is_banned': is_banned,
            'reason': reason
        })
    
    except Exception as e:
        logger.error(f"Error in check_ban: {e}")
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
        
        result = await buy_marketplace_item(user_id, listing_id)
        
        if result["success"]:
            # Отправляем уведомление продавцу
            try:
                from main import bot
                seller_id = result["seller_id"]
                item_name = result["item_name"]
                price = result["price"]
                
                await bot.send_message(
                    seller_id,
                    f"🎉 <b>Ваш предмет продан!</b>\n\n"
                    f"📦 Предмет: {item_name}\n"
                    f"💰 Получено: {price} монет\n\n"
                    f"Деньги зачислены на ваш баланс!",
                    parse_mode="HTML"
                )
                logger.info(f"✅ Notification sent to seller {seller_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to seller: {e}")
            
            new_balance = await get_user_balance(user_id)
            return web.json_response({'success': True, 'balance': new_balance})
        else:
            return web.json_response({'error': result.get("error", "Purchase failed")}, status=400)
    
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


async def case_reward_choice_endpoint(request):
    """Обработка выбора пользователя: оставить предмет или продать"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        item = data.get('item')
        choice = data.get('choice')  # 'keep' или 'sell'
        
        if not all([user_id, item, choice]):
            return web.json_response({'error': 'Missing required fields'}, status=400)
        
        if choice == 'keep':
            # Добавляем предмет в инвентарь
            await add_item_to_inventory(
                user_id,
                item['name'],
                item['rarity'],
                item['value'],
                item['image']
            )
            logger.info(f"✅ User {user_id} kept item: {item['name']}")
            
            new_balance = await get_user_balance(user_id)
            return web.json_response({
                'success': True,
                'action': 'kept',
                'balance': new_balance,
                'message': f'Предмет "{item["name"]}" добавлен в инвентарь!'
            })
            
        elif choice == 'sell':
            # Продаем за половину стоимости
            sell_price = item['value'] // 2
            
            # Начисляем деньги (с процентом реферу)
            await add_balance(user_id, sell_price, give_referrer_bonus=True)
            logger.info(f"💰 User {user_id} sold item {item['name']} for {sell_price}")
            
            new_balance = await get_user_balance(user_id)
            return web.json_response({
                'success': True,
                'action': 'sold',
                'balance': new_balance,
                'amount': sell_price,
                'message': f'Предмет продан за {sell_price} монет!'
            })
        else:
            return web.json_response({'error': 'Invalid choice'}, status=400)
    
    except Exception as e:
        logger.error(f"Error in case_reward_choice: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def quick_sell_item_endpoint(request):
    """Быстрая продажа предмета из инвентаря за полцены"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        item_name = data.get('item_name')
        item_rarity = data.get('item_rarity')
        item_value = data.get('item_value')
        item_image = data.get('item_image')
        
        if not all([user_id, item_name, item_rarity, item_value, item_image]):
            return web.json_response({'error': 'Missing required fields'}, status=400)
        
        # Проверяем наличие предмета в инвентаре
        from database import remove_item_from_inventory
        success = await remove_item_from_inventory(user_id, item_name, item_rarity, item_value, item_image)
        
        if not success:
            return web.json_response({'error': 'Item not found in inventory'}, status=400)
        
        # Продаем за половину стоимости
        sell_price = item_value // 2
        
        # Начисляем деньги (с процентом реферу)
        await add_balance(user_id, sell_price, give_referrer_bonus=True)
        logger.info(f"💰 User {user_id} quick sold item {item_name} for {sell_price}")
        
        new_balance = await get_user_balance(user_id)
        return web.json_response({
            'success': True,
            'balance': new_balance,
            'amount': sell_price
        })
    
    except Exception as e:
        logger.error(f"Error in quick_sell_item: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def get_turbo_pass_endpoint(request):
    """Получение данных Turbo PASS"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        from database import get_turbo_pass_data
        pass_data = await get_turbo_pass_data(user_id)
        
        return web.json_response(pass_data)
    
    except Exception as e:
        logger.error(f"Error in get_turbo_pass: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def claim_turbo_pass_endpoint(request):
    """Получение награды Turbo PASS"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        from database import get_turbo_pass_data, claim_turbo_pass_reward
        
        # Получаем текущие данные
        pass_data = await get_turbo_pass_data(user_id)
        current_day = pass_data['current_day']
        
        # Определяем награду для текущего дня
        REWARDS = [
            { 'day': 1, 'value': 100, 'type': 'coins' },
            { 'day': 2, 'value': 200, 'type': 'coins' },
            { 'day': 3, 'value': 50, 'type': 'energy' },
            { 'day': 4, 'value': 300, 'type': 'coins' },
            { 'day': 5, 'value': 500, 'type': 'coins' },
            { 'day': 6, 'value': 400, 'type': 'coins' },
            { 'day': 7, 'value': 1000, 'type': 'coins' },
            { 'day': 8, 'value': 600, 'type': 'coins' },
            { 'day': 9, 'value': 100, 'type': 'energy' },
            { 'day': 10, 'value': 800, 'type': 'coins' },
            { 'day': 11, 'value': 700, 'type': 'coins' },
            { 'day': 12, 'value': 900, 'type': 'coins' },
            { 'day': 13, 'value': 1000, 'type': 'coins' },
            { 'day': 14, 'value': 2000, 'type': 'coins' },
            { 'day': 15, 'value': 1200, 'type': 'coins' },
            { 'day': 16, 'value': 150, 'type': 'energy' },
            { 'day': 17, 'value': 1500, 'type': 'coins' },
            { 'day': 18, 'value': 1300, 'type': 'coins' },
            { 'day': 19, 'value': 1600, 'type': 'coins' },
            { 'day': 20, 'value': 1800, 'type': 'coins' },
            { 'day': 21, 'value': 3000, 'type': 'coins' },
            { 'day': 22, 'value': 2000, 'type': 'coins' },
            { 'day': 23, 'value': 200, 'type': 'energy' },
            { 'day': 24, 'value': 2500, 'type': 'coins' },
            { 'day': 25, 'value': 2800, 'type': 'coins' },
            { 'day': 26, 'value': 3000, 'type': 'coins' },
            { 'day': 27, 'value': 3500, 'type': 'coins' },
            { 'day': 28, 'value': 4000, 'type': 'coins' },
            { 'day': 29, 'value': 5000, 'type': 'coins' },
            { 'day': 30, 'value': 10000, 'type': 'coins' }
        ]
        
        reward = REWARDS[current_day - 1]
        
        # Получаем награду
        success = await claim_turbo_pass_reward(user_id, reward['type'], reward['value'])
        
        if not success:
            return web.json_response({'error': 'Already claimed today or invalid day'}, status=400)
        
        new_balance = await get_user_balance(user_id)
        
        return web.json_response({
            'success': True,
            'balance': new_balance,
            'reward_type': reward['type'],
            'reward_value': reward['value'],
            'energy': reward['type'] == 'energy'
        })
    
    except Exception as e:
        logger.error(f"Error in claim_turbo_pass: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def check_updates_endpoint(request):
    """Проверка обновлений для пользователя (баланс, бан и т.д.)"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({'error': 'user_id required'}, status=400)
        
        from database import is_user_banned
        
        # Проверяем бан
        is_banned, ban_reason = await is_user_banned(user_id)
        
        # Получаем актуальный баланс
        balance = await get_user_balance(user_id)
        
        # Получаем игровые данные
        game_data = await get_user_game_data(user_id)
        
        return web.json_response({
            'is_banned': is_banned,
            'ban_reason': ban_reason,
            'balance': balance,
            'game_data': {
                'energy': game_data.get('energy'),
                'max_energy': game_data.get('max_energy')
            }
        })
    
    except Exception as e:
        logger.error(f"Error in check_updates: {e}")
        return web.json_response({'error': str(e)}, status=500)

import aiosqlite
import logging
from typing import List, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE_PATH = "bot_users.db"


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                event_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_balance (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 1000,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_name TEXT,
                item_rarity TEXT,
                item_value INTEGER,
                item_image TEXT,
                count INTEGER DEFAULT 1,
                obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS case_openings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                case_name TEXT,
                item_name TEXT,
                item_value INTEGER,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_game_data (
                user_id INTEGER PRIMARY KEY,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                exp_to_next_level INTEGER DEFAULT 100,
                total_clicks INTEGER DEFAULT 0,
                coins_per_click INTEGER DEFAULT 1,
                energy INTEGER DEFAULT 1000,
                max_energy INTEGER DEFAULT 1000,
                last_energy_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_upgrades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                upgrade_id TEXT,
                level INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, upgrade_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_id TEXT,
                progress INTEGER DEFAULT 0,
                unlocked INTEGER DEFAULT 0,
                unlocked_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, achievement_id)
            )
        """)
        await db.commit()
        logger.info("База данных инициализирована")


async def add_user(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None, last_name: Optional[str] = None):
    """Добавление пользователя в базу данных"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, last_name))
        await db.execute("""
            UPDATE users SET last_activity = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        """, (user_id,))
        await db.commit()
        logger.info(f"Пользователь {user_id} добавлен в базу данных")


async def get_all_users() -> List[int]:
    """Получение всех user_id из базы данных"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_users_count() -> int:
    """Получение количества пользователей"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


# ==================== ФУНКЦИИ ДЛЯ АДМИНОВ ====================

async def add_admin(user_id: int, added_by: int):
    """Добавление администратора"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO admins (user_id, added_by)
            VALUES (?, ?)
        """, (user_id, added_by))
        await db.commit()
        logger.info(f"Администратор {user_id} добавлен пользователем {added_by}")


async def remove_admin(user_id: int):
    """Удаление администратора"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await db.commit()
        logger.info(f"Администратор {user_id} удален")


async def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result is not None


async def get_all_admins() -> List[Dict]:
    """Получение списка всех администраторов"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT a.user_id, u.username, u.first_name, a.added_at
            FROM admins a
            LEFT JOIN users u ON a.user_id = u.user_id
        """) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "user_id": row[0],
                    "username": row[1],
                    "first_name": row[2],
                    "added_at": row[3]
                }
                for row in rows
            ]


async def get_admins_count() -> int:
    """Получение количества администраторов"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM admins") as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


# ==================== ФУНКЦИИ ДЛЯ СТАТИСТИКИ ====================

async def log_event(event_type: str, event_data: str = ""):
    """Логирование события"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO statistics (event_type, event_data)
            VALUES (?, ?)
        """, (event_type, event_data))
        await db.commit()


async def get_users_today() -> int:
    """Получение количества новых пользователей за сегодня"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT COUNT(*) FROM users 
            WHERE DATE(created_at) = DATE('now')
        """) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def get_users_week() -> int:
    """Получение количества новых пользователей за неделю"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT COUNT(*) FROM users 
            WHERE created_at >= datetime('now', '-7 days')
        """) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def get_users_month() -> int:
    """Получение количества новых пользователей за месяц"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT COUNT(*) FROM users 
            WHERE created_at >= datetime('now', '-30 days')
        """) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def get_active_users_today() -> int:
    """Получение количества активных пользователей за сегодня"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT COUNT(*) FROM users 
            WHERE DATE(last_activity) = DATE('now')
        """) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def get_user_info(user_id: int) -> Optional[Dict]:
    """Получение информации о пользователе"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT user_id, username, first_name, last_name, created_at, last_activity
            FROM users WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "username": row[1],
                    "first_name": row[2],
                    "last_name": row[3],
                    "created_at": row[4],
                    "last_activity": row[5]
                }
            return None


async def get_broadcast_stats() -> Dict:
    """Получение статистики рассылок"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT COUNT(*) FROM statistics 
            WHERE event_type = 'broadcast'
        """) as cursor:
            result = await cursor.fetchone()
            total_broadcasts = result[0] if result else 0
        
        async with db.execute("""
            SELECT event_data FROM statistics 
            WHERE event_type = 'broadcast'
            ORDER BY created_at DESC LIMIT 1
        """) as cursor:
            result = await cursor.fetchone()
            last_broadcast = result[0] if result else "Нет данных"
        
        return {
            "total": total_broadcasts,
            "last": last_broadcast
        }


# ==================== ФУНКЦИИ ДЛЯ MINI APP ====================

async def get_user_balance(user_id: int) -> int:
    """Получение баланса пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT balance FROM user_balance WHERE user_id = ?
        """, (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0]
            else:
                # Создаем начальный баланс
                await db.execute("""
                    INSERT INTO user_balance (user_id, balance) VALUES (?, 1000)
                """, (user_id,))
                await db.commit()
                return 1000


async def update_user_balance(user_id: int, amount: int):
    """Обновление баланса пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO user_balance (user_id, balance) 
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET balance = ?
        """, (user_id, amount, amount))
        await db.commit()


async def add_balance(user_id: int, amount: int):
    """Добавление к балансу пользователя"""
    current_balance = await get_user_balance(user_id)
    new_balance = current_balance + amount
    await update_user_balance(user_id, new_balance)


async def subtract_balance(user_id: int, amount: int) -> bool:
    """Вычитание из баланса пользователя"""
    current_balance = await get_user_balance(user_id)
    if current_balance >= amount:
        new_balance = current_balance - amount
        await update_user_balance(user_id, new_balance)
        return True
    return False


async def add_item_to_inventory(user_id: int, item_name: str, item_rarity: str, item_value: int, item_image: str):
    """Добавление предмета в инвентарь"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Проверяем, есть ли уже такой предмет
        async with db.execute("""
            SELECT id, count FROM user_inventory 
            WHERE user_id = ? AND item_name = ?
        """, (user_id, item_name)) as cursor:
            result = await cursor.fetchone()
            
            if result:
                # Увеличиваем количество
                await db.execute("""
                    UPDATE user_inventory SET count = count + 1 
                    WHERE id = ?
                """, (result[0],))
            else:
                # Добавляем новый предмет
                await db.execute("""
                    INSERT INTO user_inventory (user_id, item_name, item_rarity, item_value, item_image)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, item_name, item_rarity, item_value, item_image))
        
        await db.commit()


async def get_user_inventory(user_id: int) -> List[Dict]:
    """Получение инвентаря пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT item_name, item_rarity, item_value, item_image, count
            FROM user_inventory WHERE user_id = ?
            ORDER BY item_value DESC
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "name": row[0],
                    "rarity": row[1],
                    "value": row[2],
                    "image": row[3],
                    "count": row[4]
                }
                for row in rows
            ]


async def log_case_opening(user_id: int, case_name: str, item_name: str, item_value: int):
    """Логирование открытия кейса"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO case_openings (user_id, case_name, item_name, item_value)
            VALUES (?, ?, ?, ?)
        """, (user_id, case_name, item_name, item_value))
        await db.commit()


async def get_case_opening_stats(user_id: int) -> Dict:
    """Получение статистики открытий кейсов пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT COUNT(*), SUM(item_value) FROM case_openings WHERE user_id = ?
        """, (user_id,)) as cursor:
            result = await cursor.fetchone()
            total_openings = result[0] if result[0] else 0
            total_value = result[1] if result[1] else 0
        
        return {
            "total_openings": total_openings,
            "total_value": total_value
        }


async def get_total_case_openings() -> int:
    """Получение общего количества открытых кейсов"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM case_openings") as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


# ==================== ФУНКЦИИ ДЛЯ ИГРОВЫХ ДАННЫХ ====================

async def get_user_game_data(user_id: int) -> Dict:
    """Получение игровых данных пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT level, exp, exp_to_next_level, total_clicks, coins_per_click, 
                   energy, max_energy, last_energy_update
            FROM user_game_data WHERE user_id = ?
        """, (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                return {
                    "level": result[0],
                    "exp": result[1],
                    "exp_to_next_level": result[2],
                    "total_clicks": result[3],
                    "coins_per_click": result[4],
                    "energy": result[5],
                    "max_energy": result[6],
                    "last_energy_update": result[7]
                }
            else:
                # Создаем начальные данные
                await db.execute("""
                    INSERT INTO user_game_data (user_id) VALUES (?)
                """, (user_id,))
                await db.commit()
                return {
                    "level": 1,
                    "exp": 0,
                    "exp_to_next_level": 100,
                    "total_clicks": 0,
                    "coins_per_click": 1,
                    "energy": 1000,
                    "max_energy": 1000,
                    "last_energy_update": datetime.now().isoformat()
                }


async def update_user_game_data(user_id: int, data: Dict):
    """Обновление игровых данных пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO user_game_data 
            (user_id, level, exp, exp_to_next_level, total_clicks, coins_per_click, 
             energy, max_energy, last_energy_update)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                level = excluded.level,
                exp = excluded.exp,
                exp_to_next_level = excluded.exp_to_next_level,
                total_clicks = excluded.total_clicks,
                coins_per_click = excluded.coins_per_click,
                energy = excluded.energy,
                max_energy = excluded.max_energy,
                last_energy_update = excluded.last_energy_update
        """, (
            user_id,
            data.get('level', 1),
            data.get('exp', 0),
            data.get('exp_to_next_level', 100),
            data.get('total_clicks', 0),
            data.get('coins_per_click', 1),
            data.get('energy', 1000),
            data.get('max_energy', 1000),
            data.get('last_energy_update', datetime.now().isoformat())
        ))
        await db.commit()


async def get_user_upgrades(user_id: int) -> List[Dict]:
    """Получение улучшений пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT upgrade_id, level FROM user_upgrades WHERE user_id = ?
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [{"upgrade_id": row[0], "level": row[1]} for row in rows]


async def update_user_upgrade(user_id: int, upgrade_id: str, level: int):
    """Обновление уровня улучшения"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO user_upgrades (user_id, upgrade_id, level)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, upgrade_id) DO UPDATE SET level = excluded.level
        """, (user_id, upgrade_id, level))
        await db.commit()


async def get_user_achievements_db(user_id: int) -> List[Dict]:
    """Получение достижений пользователя из БД"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT achievement_id, progress, unlocked, unlocked_at
            FROM user_achievements WHERE user_id = ?
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "achievement_id": row[0],
                    "progress": row[1],
                    "unlocked": bool(row[2]),
                    "unlocked_at": row[3]
                }
                for row in rows
            ]


async def update_user_achievement(user_id: int, achievement_id: str, progress: int, unlocked: bool):
    """Обновление достижения пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        unlocked_at = datetime.now().isoformat() if unlocked else None
        await db.execute("""
            INSERT INTO user_achievements (user_id, achievement_id, progress, unlocked, unlocked_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, achievement_id) DO UPDATE SET
                progress = excluded.progress,
                unlocked = excluded.unlocked,
                unlocked_at = COALESCE(user_achievements.unlocked_at, excluded.unlocked_at)
        """, (user_id, achievement_id, progress, int(unlocked), unlocked_at))
        await db.commit()
from aiohttp import web
import logging
import asyncio
from database import init_db
from web_server import setup_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(request):
    """Health check endpoint"""
    return web.Response(text="OK")

async def init_app():
    """Инициализация приложения"""
    # Инициализируем базу данных
    await init_db()
    logger.info("✅ База данных инициализирована")
    
    app = web.Application()
    
    # Добавляем health check
    app.router.add_get('/health', health_check)
    
    # Подключаем все API маршруты из web_server
    setup_routes(app)
    
    logger.info("✅ Веб-сервер готов к работе")
    
    return app

if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 8080))
    app = asyncio.run(init_app())
    web.run_app(app, host='0.0.0.0', port=port)

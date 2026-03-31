from aiohttp import web
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(request):
    """Health check endpoint"""
    return web.Response(text="OK")

async def init_app():
    """Инициализация приложения"""
    app = web.Application()
    
    # Добавляем health check
    app.router.add_get('/health', health_check)
    
    # Статические файлы для Mini App
    app.router.add_static('/webapp/', path='webapp/', name='webapp')
    
    return app

if __name__ == '__main__':
    app = init_app()
    web.run_app(app, host='0.0.0.0', port=8080)

import os
from quart import Quart
from .views import *
from .model import *

api = Blueprint('api', __name__, url_prefix='/api/v1') 
os.environ['AWS_SHARED_CREDENTIALS_FILE'] = 'credentials'
logger.disabled = True
def create_app(config_overrides=None): 

    app = Quart(__name__) 

    if config_overrides: 
        app.config.update(config_overrides)

    # Load the models 
    from .views import api_concerts, api_tickets, api_users

    app.register_blueprint(api_tickets)
    app.register_blueprint(api_concerts)
    app.register_blueprint(api_users)
    app.register_blueprint(api)

    app.add_url_rule('/', 'index', lambda: app.send_static_file('index.html'))

    
    @app.before_serving
    async def startup():
        asyncio.create_task(check_redis())

    return app


@api.route('/health') 
async def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "healthy"}),200

async def check_redis():
    """Check if redis is running"""
    while True:
        try:
            logger.log(logging.INFO, "Checking Redis")
            await cache.ping()
        except Exception as e:
            logger.error("Redis is not running")
            logger.error(e)
            exit()
        await asyncio.sleep(10)



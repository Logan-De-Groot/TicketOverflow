from quart import Blueprint, jsonify, request 
import ticketoverflow.model.users as user_service
from ticketoverflow.views.common_funcs import confirm_save
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

api_users = Blueprint('api_users', __name__, url_prefix='/api/v1/users') 

@api_users.route('/health', methods=['GET']) 
async def health():
    """Determines if user instance is still healthy"""
    return jsonify({"status": "ok"})

@api_users.route('', methods=['GET']) 
async def get_all_users():
    """Returns a list of users in json format"""
    users = await user_service.get_all_users()
    return jsonify(users), 200

@api_users.route('/<id>', methods=['GET']) 
async def users_by_int(id):
    """Get information for single user in json format"""
    # user = user_service.get_user(str(id))

    user = await user_service.get_user(id)

    if user is None:
        return jsonify("The user does not exist"), 404
    else:
        return jsonify(user), 200

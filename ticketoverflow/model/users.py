from . import cache, conversion_single_item, conversion_list_items
from aiocache import cached, Cache
import json

@cached(ttl=None)
async def get_user(id):

    id = f"user:{id}"
    user = await conversion_single_item(f"{id}")
    return user

@cached(ttl=None)
async def get_all_users():
    users = await conversion_list_items("user:")
    return users
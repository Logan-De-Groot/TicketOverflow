#from dotenv import dotenv_values
import boto3
import redis
import os
import redis.asyncio as redis
import logging
import sys
import json

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.disabled = True

REDIS_URL = os.environ.get("REDIS_URL", "localhost")
cache = redis.Redis(host=REDIS_URL, port=6379, db=0)


session_dymno = boto3.Session(region_name='us-east-1')
db = session_dymno.resource('dynamodb', region_name="us-east-1")

async def conversion_single_item(id):
    item = await cache.hgetall(id)

    if item is None or item == {}:
        return None
    
    new_dict = {}
    for key, value in item.items():
        new_dict[key.decode("utf-8")] = value.decode("utf-8")     
    return new_dict

async def conversion_list_items(prefix, removals=[], conversions=[], loads =[]):
    items = await cache.keys(f"{prefix}*")

    items_converted = []
    for item in items:
        i = await conversion_single_item(item.decode("utf-8"))
    
        for removal in removals:
            del i[removal]
        items_converted.append(i)

        for conversion in conversions:
            i[conversion] = int(i[conversion])

        for load in loads:
            i[load] = json.loads(i[load])    

    return items_converted


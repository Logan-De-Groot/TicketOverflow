import json
import redis
import time
import os
import boto3
from multiprocessing import Pool as ThreadPool



os.environ['AWS_SHARED_CREDENTIALS_FILE'] = 'credentials'



REDIS_URL = os.environ.get("REDIS_URL", "localhost")

def load_redis():
    print("Checking Redis State")
    cache = redis.Redis(host=REDIS_URL, port=6379, db=0)
    print(cache.hgetall('user:00000000-0000-0000-0000-000000000001'))
    if cache.hgetall('user:00000000-0000-0000-0000-000000000001') == {}:
        print("Populating Redis")
        with open("users.json") as f:
            data = json.load(f)
        
        for user in data:
            cache.hmset("user:"+str(user["id"]), user)
        return False
    else:
        print("Skip loading")
        return True


def wait_for_db_redis(retries=12, timeout=15):
    """Wait for the database to be available.

    :param db_url: the database URL
    :param timeout: the maximum number of seconds to wait
    """
    print("Attempting to connect to REDIS")
    for i in range(retries):        
        try:
            cache = redis.Redis(host=REDIS_URL, port=6379, db=0)
            cache.hgetall('00000000-0000-0000-0000-000000000001')
            return
        except Exception as e:
            print(e)
            print(f"Waiting for the database to be available ({i+1}/{retries})")
            time.sleep(timeout)
    raise RuntimeError("Timeout waiting for the database")



def wait_for_db_dynamo(retries=12, timeout=15):

    print("Attempting to connect to DYNMO")
    for i in range(retries):        
        try:
            session_dymno = boto3.Session(region_name='us-east-1')
            db = session_dymno.resource('dynamodb', region_name="us-east-1")
            users = db.Table("users")
           
            users.get_item(Key={'id': '00000000-0000-0000-0000-000000000001'})
            return
        except Exception as e:
            print(e)
            print(f"Waiting for the database to be available ({i+1}/{retries})")
            time.sleep(timeout)
    raise RuntimeError("Timeout waiting for the database")


def load_all_users():
    session_dymno = boto3.Session(region_name='us-east-1')
    db = session_dymno.resource('dynamodb', region_name="us-east-1")
    users = db.Table("users")
    if users.get_item(Key={'id': '00000000-0000-0000-0000-000000000001'}) is not None:
        print("Skip loading")
        return
    
    with open("users.json") as f:
        data = json.load(f)

    items = []
    for batch in range (20):
        items.append(data[batch*250:(batch+1)*250])

    pool = ThreadPool(20)

    pool.map(batch_items, items)

    pool.close()
    pool.join()
    
        
def batch_items(items):
    session_dymno = boto3.Session(region_name='us-east-1')
    db = session_dymno.resource('dynamodb', region_name="us-east-1")
    users = db.Table("users")

    with users.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)


def load_redis_from_backup():
    session_dymno = boto3.Session(region_name='us-east-1')
    db = session_dymno.resource('dynamodb', region_name="us-east-1")
    concerts = db.Table("concerts")
    tickets = db.Table("tickets")
    cache = redis.Redis(host=REDIS_URL, port=6379, db=0)

    concerts_to_count_tickets = {}
    all_concerts = concerts.scan()
    for concert in all_concerts["Items"]:
        concert["capacity"] = str(concert["capacity"])
        id = concert["id"]
        cache.set(f"print:{id}", "False")
        cache.hmset(id, concert)

    all_tickets = tickets.scan()
    for ticket in all_tickets["Items"]:
        id = ticket["id"]
        cache.hmset(f"{id}", ticket)
        concerts_to_count_tickets[ticket["concert_id"]] = concerts_to_count_tickets.get(ticket["concert_id"], 0) + 1

    for id, count in concerts_to_count_tickets.items():
        cache.set(f"tickets_sold:{id}", count)

wait_for_db_redis()
redis_empty = load_redis()
wait_for_db_dynamo()


if redis_empty:
    
    load_all_users()
    load_redis_from_backup()
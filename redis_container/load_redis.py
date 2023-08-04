import json
import redis
import time


def load_redis():
    print("started")
    cache = redis.Redis(host='localhost', port=6379, db=0)

    if cache.hgetall('00000000-0000-0000-0000-000000000001') == {}:
        with open("users.json") as f:
            data = json.load(f)

        for user in data:
            cache.hmset("user:"+str(user["id"]), user)
    else:
        print("Skip loading")


def wait_for_db(retries=12, timeout=15):
    """Wait for the database to be available.
    :param db_url: the database URL
    :param timeout: the maximum number of seconds to wait
    """
    for i in range(retries):
        try:
            cache = redis.Redis(host='localhost', port=6379, db=0)
            cache.hgetall('00000000-0000-0000-0000-000000000001')
            return
        except Exception as e:
            print(e)
            print(f"Waiting for the database to be available ({i+1}/{retries})")
            time.sleep(timeout)
    raise RuntimeError("Timeout waiting for the database")


wait_for_db()
load_redis()

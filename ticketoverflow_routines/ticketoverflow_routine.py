import logging
import sys
import boto3
import time
import json
import os
import redis

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.disabled = True


os.environ['AWS_SHARED_CREDENTIALS_FILE'] = 'credentials'

sqs = boto3.client('sqs', region_name="us-east-1")
concerts_queue_url = sqs.get_queue_url(QueueName='concerts')['QueueUrl']

REDIS_URL = os.environ.get("REDIS_URL", "localhost")
cache = redis.Redis(host=REDIS_URL, port=6379, db=0)

def generate_concert_seating():

    while True:
        try:
            concerts = get_all_concerts()

            for concert in concerts:
                id = concert["id"]
                
                if (get_concert_printable(id)) == "False":
                    concert['seats'] = {"max": int(concert["capacity"]), "purchased": int(get_tickets_sold(id))}

                    logger.info(f"Sending {id} concert to queue")
                    response = sqs.send_message(
                        QueueUrl=concerts_queue_url,
                        MessageBody=json.dumps(concert)
                    )
                    concert_print_true(id)
                    
            time.sleep(30)
        except Exception as e:
            logger.error(e)
            time.sleep(10)

def get_all_concerts():
    concerts = conversion_list_items("concert", ["url"], ['capacity'])

    return concerts

def get_concert_printable(id):
    return (cache.get(f"print:{id}")).decode("utf-8")

def get_tickets_sold(id):

    tickets_sold = cache.get(f"tickets_sold:{id}")
    return tickets_sold

def concert_print_true(id):
    cache.set(f"print:{id}", "True")  


def conversion_single_item(id):
    item = cache.hgetall(id)

    if item is None or item == {}:
        return None
    
    new_dict = {}
    for key, value in item.items():
        new_dict[key.decode("utf-8")] = value.decode("utf-8")     
    return new_dict

def conversion_list_items(prefix, removals=[], conversions=[]):
    logging.info(f"Getting all {prefix}s")
    items = cache.keys(f"{prefix}*")
    logging.info(f"Getting all {prefix}s finished")
    items_converted = []
    for item in items:
        i = conversion_single_item(item.decode("utf-8"))
    
        for removal in removals:
            del i[removal]
        items_converted.append(i)

        for conversion in conversions:
            i[conversion] = int(i[conversion])

    return items_converted


logger.info("Starting generate_concert_seating routine")
generate_concert_seating()
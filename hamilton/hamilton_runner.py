import boto3
import asyncio
import multiprocessing as mp
import redis
import json
import subprocess
import os
import sys
import logging 
import time
import uuid
from datetime import datetime

MAX_TYPE = int(os.environ.get("MAX_NUMBER_ITEMS", 10))

MAX_CONCERTS = MAX_TYPE
MAX_TICKETS = MAX_TYPE
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.disabled = True

#sqs = boto3.client('sqs', endpoint_url="http://localhost:9324", region_name="us-east-1")
os.environ['AWS_SHARED_CREDENTIALS_FILE'] = 'credentials'


sqs = boto3.client('sqs', region_name="us-east-1")
REDIS_URL = os.environ.get("REDIS_URL", "localhost")

session_dymno = boto3.Session()
db = session_dymno.resource('dynamodb', region_name='us-east-1')
#db = session_dymno.resource('dynamodb', endpoint_url="http://localhost:8000", region_name='us-east-1')
concerts_table = db.Table('concerts_svg')
tickets_table = db.Table('tickets_svg')
actual_tickets_table = db.Table('tickets')
cache = redis.Redis(host=REDIS_URL, port=6379, db=0)

def concert_loop():
    queue_url = sqs.get_queue_url(QueueName='concerts')['QueueUrl']
    logger.info("Concert Loop Started")
    id_concert = uuid.uuid4().hex
    cache.set(f"active_concerts:{id_concert}", 0)


    while True:
        try:
            if int(cache.get(f"active_concerts:{id_concert}").decode("utf-8")) < MAX_CONCERTS:
                logging.info(f'Active Concerts:{cache.get(f"active_concerts:{id_concert}").decode("utf-8")}')
                response = sqs.receive_message(
                    QueueUrl=queue_url,
                    AttributeNames=['All'],
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=10,
                )

                if int(cache.get(f"active_concerts:{id_concert}").decode("utf-8")) > MAX_CONCERTS:
                    logger.info("awaiting spot")
                    continue

                    

                if 'Messages' in response:

                    concert_message = response['Messages'][0]
                    concert = concert_message["Body"]
                    logger.info(f"Recieved: {concert}")
                    try:
                        concert = json.loads(concert)
                    except:
                        receipt_handle = concert_message['ReceiptHandle']
                        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                        continue

                    receipt_handle = concert_message['ReceiptHandle']

                    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

                    id = concert["id"]

                    with open(f"concerts/{id}.json", 'w') as f:
                        json.dump(concert, f)

                    cache.incr(f"active_concerts:{id_concert}")
                    process = mp.Process(target=run_hamilton_concerts, args=(id,id_concert,))
                    process.start()
                
                    logging.info(f'Active Concerts:{cache.get(f"active_concerts:{id_concert}").decode("utf-8")}')
            
            else:
                logger.info("awaiting for spot")
                time.sleep(1)

        except Exception as e:
            logger.error(e)

def run_hamilton_concerts(id, id_concert):
    
    logger.info(f"Beginning generation of {id}")
    subprocess.run([
        f"./hamilton-v1.1.0-linux-amd64",
        "generate",
        "seating",
        "--input",
        f"concerts/{id}.json",
        "--output",
        f"concerts/{id}"]
    )

    with open(f"concerts/{id}.svg", 'r') as f:
        seating = f.read()

    try:
        concerts_table.put_item(
            Item={
                "id": id,
                "svg": seating
            }
        )
    except Exception as e:
        try:
            cache.set(f"svg:{id}", seating)
        except Exception as e:
            pass

        logger.error(e)

    logger.info(f"Finished generation of {id}")
    cache.decr(f"active_concerts:{id_concert}")
    logging.info(f'Active Concerts:{cache.get(f"active_concerts:{id_concert}").decode("utf-8")}')

# I may as well as hang up my hat to being a programmer. Thank god no one will look at this
def ticket_loop():
    queue_url = sqs.get_queue_url(QueueName='tickets')['QueueUrl']
    logger.info("Ticket Loop Started")
    id_concert = uuid.uuid4().hex
    cache.set(f"active_tickets:{id_concert}", 0)
    while True:
        try:
            logger.info(f'Active Tickets:{cache.get(f"active_tickets:{id_concert}").decode("utf-8")}')
            if int(cache.get(f"active_tickets:{id_concert}").decode("utf-8")) < MAX_TICKETS:
                count = 0
                date_bucket = {}
                number_tickets = 10
                while number_tickets == 10 and count < MAX_TICKETS:
                    response = sqs.receive_message(
                        QueueUrl=queue_url,
                        AttributeNames=['All'],
                        MaxNumberOfMessages=min(10,max(MAX_TICKETS-count,1)),
                        WaitTimeSeconds=10
                    )
                    number_tickets = len(response.get('Messages', []))
                    count += number_tickets

                    logger.info(f"Recieved {number_tickets} tickets")
                    logger.info(f"Currently have {count} tickets")
                    if 'Messages' in response:
                        for message in response['Messages']:
                            ticket = message["Body"]

                            try:
                                ticket = json.loads(ticket)
                            except:
                                receipt_handle = ticket['ReceiptHandle']
                                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                                continue
                            #print(ticket)
                            date = datetime.strptime(ticket['concert']["date"], "%Y-%m-%d")
                            if date not in date_bucket:
                                date_bucket[date] = []
                            date_bucket[date].append(ticket)

                            receipt_handle = message['ReceiptHandle']
                            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)



                if date_bucket == {}:
                    logger.info("no tickets to print")
                    continue

                tickets_by_date = [(date,tickets) for date, tickets in date_bucket.items()] 
                tickets_by_date.sort(key=lambda x: x[0])
                
                for ticket in tickets_by_date[0][1]:
                    id = ticket["id"]
                    
                    wipe = cache.get(f"ticket_wipe:{id}")

                    if wipe is not None:
                        wipe = wipe.decode("utf-8")
                        if wipe == "True":
                            logger.info(f"Skipping: {id} due to wipe status")
                            continue

                    logger.info(f"Attempting to save message {id}")

                    with open(f"tickets/{id}.json", 'w') as f:
                        json.dump(ticket, f)

                    logger.info(f"Succesfully saved ticket {id}")
                    cache.incr(f"active_tickets:{id_concert}")
                    process = mp.Process(target=run_hamilton_tickets, args=(id,id_concert,))
                    process.start()

                for date_ticket in tickets_by_date[1:]:
                    for ticket in date_ticket[1]:
                        sqs.send_message(
                            QueueUrl=queue_url,
                            MessageBody=json.dumps(ticket)
                        )
            else:
                logger.info("awaiting for spot")
                time.sleep(1)
        except Exception as e:
            logger.error(e)


def run_hamilton_tickets(id, id_concert):
    logger.info(f"Beginning generation of {id}")
    subprocess.run([
        "./hamilton-v1.1.0-linux-amd64",
        "generate",
        "ticket",
        "--input",
        f"tickets/{id}.json",
        "--output",
        f"tickets/{id}"]
    )

    try:
        with open(f"tickets/{id}.svg", 'r') as f:
            seating = f.read()
    

        tickets_table.put_item(
            Item={
                "id": id,
                "svg": seating
            }
        )

        ticket = get_ticket(id)
        set_ticket_status(id, ticket, "PRINTED")
        logger.info(f"Finished generation of {id}")
    except FileNotFoundError:
        ticket = get_ticket(id)
        set_ticket_status(id, ticket, "ERROR")
    cache.decr(f"active_tickets:{id_concert}")
    
def get_ticket(id):
    if "ticket" not in id:
        return None

    ticket = conversion_single_item(id)
    
    return ticket

def set_ticket_status(id, ticket, status):
    ticket['print_status'] = status
    cache.hmset(id, ticket)
    response = actual_tickets_table.put_item(
        Item=ticket
    )

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception("Error adding ticket")
    else:
        logger.info("added ticket worked and confirmed")

    
def conversion_single_item(id):
    item = cache.hgetall(id)

    if item is None or item == {}:
        return None
    
    new_dict = {}
    for key, value in item.items():
        new_dict[key.decode("utf-8")] = value.decode("utf-8")     
    return new_dict

def loop_entry():
    type = os.environ.get("TICKETOVERFLOW_TYPE", "tickets")
    logging.info(f"Starting loop with type {type}")

    if type == "tickets":
        ticket_loop()
    elif type == "concerts":
        concert_loop()    

loop_entry()
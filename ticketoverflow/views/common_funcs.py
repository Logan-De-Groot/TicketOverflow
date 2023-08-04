import boto3
import os
import sys
os.environ['AWS_SHARED_CREDENTIALS_FILE'] = 'credentials'

sqs = boto3.client('sqs', region_name="us-east-1")

session_dymno = boto3.Session()
db = session_dymno.resource('dynamodb', region_name='us-east-1')
concerts_table = db.Table('concerts_svg')
tickets_table = db.Table('tickets_svg')

import asyncio
from ticketoverflow.model import cache
import logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger()

logger.setLevel(logging.INFO)

logger.disabled = True

async def confirm_save():
    await asyncio.sleep(1)
    count = 0
    status = "not okay duh"
    while status != "ok":
        status = await cache.info('persistence')
        status = status.get('aof_last_write_status', None)
        await asyncio.sleep(1)
        if count == 100:
            raise AssertionError

    return True

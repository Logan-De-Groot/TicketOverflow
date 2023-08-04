import json
import os
from quart import Blueprint, jsonify, request, Response
import ticketoverflow.model.concerts as concert_service
import uuid
import asyncio
from ticketoverflow.views.common_funcs import confirm_save, logger, sqs

api_concerts = Blueprint('api_concerts', __name__, url_prefix='/api/v1/concerts') 

queue_url = sqs.get_queue_url(QueueName='concerts')['QueueUrl']

@api_concerts.route('/health', methods=['GET']) 
async def health():
    """Determines if concert instance is still healthy"""
    return jsonify({"status": "ok"})

@api_concerts.route('', methods=['GET']) 
async def get_all_concerts():
    """Returns a list of concerts in json format"""
    concerts = await concert_service.get_all_concerts()
    return jsonify(concerts), 200

@api_concerts.route('', methods=['POST']) 
async def concerts_post():
    """"""
    data = await request.json

    if data is None:
        return jsonify("Body paramter was malformed or invalid"), 400

    for entry in ["name", "venue", "date", "capacity", "status"]:

        if data.get(entry) is None or data.get(entry) == "":
            return jsonify("Body paramter was malformed or invalid"), 400
        
    if data.get('status') not in ["ACTIVE", "CANCELLED", "SOLD_OUT"] or int(data.get('capacity')) < 0:    
        return jsonify("Body paramter was malformed or invalid"), 400
  
    id = uuid.uuid4().hex
    try:
        await concert_service.add_concert(
                id,
                data.get('name'),
                data.get('venue'),
                data.get('date'),
                data.get('capacity'),
                data.get('status'),
                request.base_url)
    except Exception as e:

        return jsonify(f"{e}"), 500

    concert = await concert_service.get_concert(f"concert:{id}")
    concert.pop("url")
    logger.info(f"Concert {id} created")
    return concert, 201

@api_concerts.route('/<id>', methods=['GET']) 
async def get_concert(id):
    """
    """
    concert = await concert_service.get_concert(f"{id}")

    if concert is None:
        return jsonify("The concert does not exist"), 404
    else:
        concert.pop("url")
        logger.info(f"Concert {id} retrieved")
        return jsonify(concert), 200

@api_concerts.route('/<id>', methods=['PUT']) 
async def update_concert(id):
    """
    """


    data = await request.json 

    for entry in ["name", "venue", "date", "status"]:
        if data.get(entry) == "":
            return jsonify("Body paramter was malformed or invalid"), 400

    if data.get("capacity") != None or data.get('status', "ACTIVE") not in ["ACTIVE", "CANCELLED", "SOLD_OUT"] or int(data.get('capacity', 1)) < 0:    
        return jsonify("Body paramter was malformed or invalid"), 400
    

    try:
        concert = await concert_service.update_concert(
            id,
            data.get('name'),
            data.get('venue'),
            data.get('date'),
            data.get('status'))
    except Exception as e:
        return jsonify(f"{e}"), 500

    if concert is False:
        return jsonify("The concert does not exist"), 404
    else:
        logger.info(f"Concert {id} updated")
        return concert, 200

@api_concerts.route('/<id>/seats', methods=['GET'])
async def generate_seating(id):
    concert = await concert_service.get_concert(f"{id}")

    if concert is None:
        return jsonify("The concert does not exist"), 404

    sleep_counter = 0
    while True:
        seating = await concert_service.get_concert_svg(id)
        if seating is None:
            await asyncio.sleep(3)
            sleep_counter += 3
        elif sleep_counter > 180:
            return 404
        else:
            logger.info(f"Concert {id} seating retrieved")
            return Response(seating, content_type='image/svg+xml'), 200



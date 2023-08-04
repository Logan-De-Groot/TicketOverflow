import asyncio
import json
import uuid
from quart import Blueprint, jsonify, request, Response
import ticketoverflow.model.tickets as ticket_service
import ticketoverflow.model.concerts as concert_service
import ticketoverflow.model.users as user_service
from ticketoverflow.views.common_funcs import confirm_save, logger, sqs

api_tickets = Blueprint('api_tickets', __name__, url_prefix='/api/v1/tickets') 

queue_url = sqs.get_queue_url(QueueName='tickets')['QueueUrl']

seen_concerts = []

@api_tickets.route('/health', methods=['GET']) 
async def health():
    """Determines if ticket service is healthy"""
    return jsonify({"status": "ok"})

@api_tickets.route('', methods=['GET']) 
async def get_all_tickets():
    """
    OPTIONAL INPUTS USERID, CONCERT ID
    Returns a list of all tickets in json format"""
    user_id = request.args.get('user_id')
    concert_id = request.args.get('concert_id')

    if user_id is not None:
        if await user_service.get_user(user_id) is None:
            logger.info(f"user {user_id} does not exist")
            return jsonify("User or Concert does not exist"), 404

    if concert_id is not None:
        if await concert_service.get_concert(concert_id) is None:
            logger.info(f"Concert {concert_id} does not exist")
            return jsonify("User or Concert does not exist"), 404    


    for args in request.args:
        if args not in ["user_id", "concert_id"]:
            logger.info(f"Unknown identifier {args} provided as filter parameter")
            return jsonify(" Unknown identifier provided as filter parameter"), 404

    if user_id is None and concert_id is None:
        data = await ticket_service.get_all_tickets()
    elif user_id is not None and concert_id is not None:
        data = await ticket_service.get_tickets_by_concert_user(concert_id,user_id)
    elif user_id is not None and concert_id is None:
        data = await ticket_service.get_tickets_by_userid(user_id)
    else:
        data = await ticket_service.get_tickets_by_concert(concert_id)
    
    for item in data:
        item.pop("user_id")
        item.pop("concert_id")
    logger.info(f"All tickets retrieved")
    return jsonify(data), 200


@api_tickets.route('', methods=['POST']) 
async def purchase_ticket():
    """Get information for single user in json format"""
    data = await request.get_json()

    user_id = data.get('user_id')
    concert_id = data.get('concert_id')

    if user_id is None or concert_id is None:
        logger.info(f"User_ID or Concert_ID was not specified")
        return jsonify("User_ID or Concert_ID was not specified"), 400
    

    user =  await user_service.get_user(user_id)
    concert = await concert_service.get_concert(concert_id)

    if user is None or concert is None:
        logger.info(f"Concert {concert_id} does not exist or user {user_id} does not exist")

        return jsonify("User or concert does not exist"), 400


    tickets_sold = int(await concert_service.get_tickets_sold(concert_id)) + 1
    
    if tickets_sold == int(concert["capacity"]):
        await concert_service.increment_concert(concert_id)
        await concert_service.update_concert(concert_id, status="SOLD_OUT")
        
    elif tickets_sold > int(concert["capacity"]):
        logger.info(f"Concert {concert_id} is sold out")
        return jsonify("Concert is sold out"), 422
    else:
        await concert_service.increment_concert(concert_id)
    
    id = uuid.uuid4().hex

    await ticket_service.add_ticket(f"ticket:{id}", "NOT_PRINTED", concert_id, user_id,
                              f'{{"id":\"{concert_id}\", "url":\"{concert["url"]}\"}}',
                              f'{{"id": \"{user_id}\","url": \"{request.base_url.rstrip("tickets/")+"/users/"+user_id}\"}}')

    logger.info(f"Ticket {id} created")
    return jsonify({"id": f"ticket:{id}", 
                    "concert": {
                                "id": concert_id,
                                "url": concert["url"]
                            },
                    "user": {
                                "id": user_id,
                                "url": request.base_url.rstrip("tickets/")+"/users/"+user_id
                            },
                    "print_status": "NOT_PRINTED",
                    }
                ), 201


@api_tickets.route('<id>', methods=['GET']) 
async def get_ticket(id):
    """
    OPTIONAL INPUTS USERID, CONCERT ID
    Returns a list of all tickets in json format"""
    ticket = await ticket_service.get_ticket(id, None)

    if ticket == None:
        return jsonify("The ticket does not exist"), 404
    
    ticket.pop("user_id")
    ticket.pop("concert_id")

    logger.info(f"Ticket {id} retrieved")
    return jsonify(ticket), 200


@api_tickets.route('/<id>/print', methods=['POST'])
async def generate_ticket(id):
    ticket = await ticket_service.get_ticket(id, None)
    
    if ticket is None:
        return jsonify("The ticket does not exist"), 404

    concert = await concert_service.get_concert(ticket["concert_id"])
    user = await user_service.get_user(ticket["user_id"])

    await ticket_service.set_ticket_status(id, ticket, "PENDING")
    await ticket_service.wipe_failed_ticket(id)

    ticket_print = {}
    ticket_print["id"]= id
    ticket_print["name"] = user["name"]
    ticket_print["email"] = user["email"]
    ticket_print["concert"] = {"id": concert["id"], "name": concert["name"], "date": concert["date"], "venue": concert["venue"]}    

    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(ticket_print)
    )

    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        print("Ticket failed to send to queue")

    logger.info(f"Ticket sent to queue: {id}")

    ticket.pop("user_id")
    ticket.pop("concert_id")
    return jsonify(ticket), 202


@api_tickets.route('/<id>/print', methods=['GET'])
async def get_seating(id):
    ticket = await ticket_service.get_ticket(id, None)
    status = ticket["print_status"]

    seating = ticket_service.get_ticket_svg(id)

    if ticket is None or seating is None or status != "PRINTED":
        return jsonify("Ticket does not exist or not printed"),404
    logger.info(f"Ticket {id} seating retrieved")
    return Response(seating, content_type='image/svg+xml'), 200
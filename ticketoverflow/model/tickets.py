from . import *
import json 

tickets_table_svg = db.Table('tickets_svg')
tickets_table = db.Table('tickets')

async def add_ticket(id, status, concert_id=None, user_id=None, concert_details=None, user_details=None):
    data = {}

    for mapping, current_data in [("id",id), ("print_status", status), ("concert_id", f"{concert_id}"), 
                                  ("user_id", user_id), ("concert",concert_details), ("user",user_details)]:
        if current_data is not None:
            data[mapping] = current_data

    await cache.hmset(id, data)

    response = tickets_table.put_item(
        Item=data
    )

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception("Error adding ticket")
    else:
        logger.info("added ticket worked and confirmed")

async def get_ticket(id, base=None):
    if "ticket" not in id:
        return None

    ticket = await conversion_single_item(id)

    if ticket is None:
        return None
    
    if ticket is not None and base is not None:
        ticket["url"] = base+ f"/{id}"

    ticket["user"] = json.loads(ticket["user"])
    ticket["concert"] = json.loads(ticket["concert"])
  
    return ticket

async def get_tickets_by_concert(concert_id):
    tickets = await get_all_tickets()

    return [ticket for ticket in tickets if ticket['concert_id'] == concert_id]

async def get_tickets_by_userid(user_id):
    tickets = await get_all_tickets()

    return [ticket for ticket in tickets if ticket['user_id'] == user_id]


async def get_tickets_by_concert_user(concert_id, user_id):
    tickets = await get_all_tickets()

    return [ticket for ticket in tickets if ticket['user_id'] == user_id and ticket['concert_id'] == concert_id]

async def get_all_tickets():
    tickets = await conversion_list_items("ticket:", loads=["concert", "user"])
    return tickets

async def set_ticket_status(id, ticket, status):
    ticket['print_status'] = status

    ticket['user'] = json.dumps(ticket['user'])
    ticket['concert'] = json.dumps(ticket['concert'])
    
    await cache.hmset(id, ticket)
    response = tickets_table.put_item(
        Item=ticket
    )

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception("Error adding ticket")
    else:
        logger.info("added ticket worked and confirmed")
    
async def wipe_failed_ticket(id):
    await cache.set(f"ticket_wipe:{id}", "False")  

def get_ticket_svg(id):
    return tickets_table_svg.get_item(Key={'id': id})['Item']['svg'] if tickets_table_svg.get_item(Key={'id': id}).get("Item") is not None else None

async def reset_all_tickets(concert_id):
    tickets = await get_tickets_by_concert(concert_id)

    for ticket in tickets:
        if ticket["print_status"] == "PENDING":
            id = ticket["id"]
            await cache.set(f"ticket_wipe:{id}", "True")  

        await set_ticket_status(ticket["id"], ticket, "NOT_PRINTED")
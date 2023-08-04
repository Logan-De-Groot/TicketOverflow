from . import *
from ticketoverflow.model.tickets import reset_all_tickets
from cachetools.func import ttl_cache

concerts_table_svg = db.Table('concerts_svg')
concerts_table = db.Table('concerts')

async def add_concert(id, name, venue, date, capacity, status, base):
    
    id =  f"concert:{id}"
    concert = {
        "id": id,
        "name": name,
        "venue": venue,
        "date": date,
        "capacity": capacity,
        "status": status,
        "url": base+id
    }
    await cache.set(f"print:{id}", "False")
    await cache.set(f"tickets_sold:{id}", 0)
    await cache.hmset(id, concert)
    

    response = concerts_table.put_item(
        Item=concert
    )

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception("Error adding ticket")
    else:
        logger.info("added concert worked and confirmed")


async def get_concert(id):
    if "concert" not in id:
        return None
    
    concert = await conversion_single_item(id)

    if concert is None or concert == {}:
        return None
    
    concert['capacity'] = int(concert['capacity'])

    return concert

async def get_all_concerts():
    concerts = await conversion_list_items("concert", ["url"], ['capacity'])

    return concerts

async def update_concert(id, name=None, venue=None, date=None, status=None):

    concert = await get_concert(id)

    if concert is None:
        return False

    for item, update_value in [("name", name), ("venue", venue), ("date", date), ("status", status)]:
        if update_value is not None:
            concert[item] = update_value

    await cache.hmset(f"{id}", concert)
    await cache.set(f"print:{id}", "False")  

    if name is not None or venue is not None or date is not None or status is not None:
        
        await reset_all_tickets(id)
    
    response = concerts_table.put_item(
        Item=concert
    )    

    
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception("Error adding ticket")
    else:
        logger.info("added ticket worked and confirmed")


    return concert

async def increment_concert(id):
    await cache.set(f"print:{id}", "False")
    await cache.incr(f"tickets_sold:{id}")

async def get_tickets_sold(id):

    tickets_sold = await cache.get(f"tickets_sold:{id}")
    return tickets_sold

async def get_concert_printable(id):
    return (await cache.get(f"print:{id}")).decode("utf-8")


async def get_concert_svg(id):
    data = concerts_table_svg.get_item(Key={'id': id}).get("Item")
    if data is None:
        data = (await cache.get(f"svg:{id}"))
        if data is None:
            return None
        else:
            return data.decode("utf-8")
    return data["svg"]




async def concert_print_true(id):
    await cache.set(f"print:{id}", "True")  


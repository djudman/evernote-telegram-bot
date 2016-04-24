import settings
from motor.motor_asyncio import AsyncIOMotorClient


async def get_start_session(user_id=None, sid=None):
    # TODO: use global AsyncIOMotorClient instance
    with AsyncIOMotorClient(settings.MONGODB_URI) as client:
        db = client.evernoterobot
        query = {}
        if user_id is not None:
            query['user_id'] = user_id
        if sid is not None:
            query['_id'] = sid
        result = await db.sessions.find_one(query)
    return result


async def save_start_session(user_id, ouath_url, sid=None):
    session = {
        'user_id': user_id,
        'oauth_url': ouath_url,
    }
    if sid is not None:
        session['_id'] = sid
    # TODO: use global AsyncIOMotorClient instance
    with AsyncIOMotorClient(settings.MONGODB_URI) as client:
        db = client.evernoterobot
        await db.sessions.save(session)

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import MONGODB_DB_NAME, MONGODB_URI

client = AsyncIOMotorClient(MONGODB_URI) if MONGODB_URI else None
db = client[MONGODB_DB_NAME] if client else None
reviews_collection = db["reviews"] if db is not None else None


async def ensure_indexes() -> None:
    if reviews_collection is None:
        return
    await reviews_collection.create_index(
        [("repo_owner", 1), ("repo_name", 1), ("created_at", 1)]
    )

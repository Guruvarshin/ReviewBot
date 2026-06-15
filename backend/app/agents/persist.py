from app.db import reviews_collection


async def persist_node(state: dict) -> dict:
    if reviews_collection is None:
        print("MONGODB_URI not set, skipping persistence")
        return {}

    review = state["final_review"]
    await reviews_collection.insert_one(review.model_dump())
    return {}

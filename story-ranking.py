from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


def get_id_from_object_id(object_id: ObjectId):
    """
    Returns the id from an ObjectId.

    Parameters:
        object_id (ObjectId): The ObjectId to get the id from.

    Returns:
        str: The id from the ObjectId.
    """

    return str(object_id) if object_id is not None else None


def get_id(entry: dict):
    """
    Returns the id from an entry.

    Parameters:
        entry (dict): The entry to get the id from.

    Returns:
        str: The id from the entry.
    """

    return get_id_from_object_id(entry["_id"]) if entry["_id"] is not None else None


def get_entries_map(
    uri: str = MONGO_URI,
    db_name: str = DATABASE_NAME,
    collection_name: str = COLLECTION_NAME,
):
    """
    Returns a map of entries with the id as the key.

    Parameters:
        uri (str): The URI of the MongoDB instance.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.

    Returns:
        dict: A map of entries with the id as the key.
    """

    client = MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]

    entries_map = {get_id(entry): entry for entry in collection.find()}

    client.close()
    return entries_map


if __name__ == "__main__":
    # Get all stories from database
    entries_map = get_entries_map()

    # Calculate weighted scores for each story and its parent chain
    story_scores = {}
    PARENT_WEIGHT_DECAY = 0.9  # How much parent stories' votes are weighted

    for story in entries_map.values():
        current_weight = 1.0
        current_story_id = get_id(story)
        chain_total_score = 0

        # Traverse up the story chain, accumulating weighted scores
        while current_story_id is not None:
            current_story = entries_map[current_story_id]

            # Calculate vote score for current story
            vote_score = sum(
                {"upvote": 1, "downvote": -1}.get(vote["voteType"], 0)
                for vote in current_story["votes"]
            )

            # Add weighted score to total
            chain_total_score += vote_score * current_weight

            # Move up to parent story
            current_story_id = get_id_from_object_id(current_story["parentId"])
            current_weight *= PARENT_WEIGHT_DECAY

        story_scores[get_id(story)] = chain_total_score

    # Sort stories by their total scores
    sorted_stories = sorted(story_scores.items(), key=lambda x: x[1], reverse=True)

    # Print raw scores (for debugging)
    for story_id, score in sorted_stories:
        print((story_id, score))

    # Print formatted story text with scores
    for story_id, total_score in sorted_stories:
        story = entries_map[story_id]
        full_text = f"{story['storyChain']} {story['text']}"
        print(f'{total_score:.2f}: "{full_text}"')

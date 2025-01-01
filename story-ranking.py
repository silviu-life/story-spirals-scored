from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
import json
import datetime
import argparse

load_dotenv()


def serialize_entity(entity: dict) -> dict:
    """
    Recursively converts MongoDB-specific types in an entity to their string representations.

    This function traverses through a dictionary and converts:
    - ObjectId fields to their string representation
    - Datetime objects to ISO format strings
    - Handles nested dictionaries and lists recursively

    Parameters:
        entity (dict): A dictionary containing MongoDB document data, potentially
                      with ObjectId fields, datetime objects, and nested structures.

    Returns:
        dict: The same dictionary with all MongoDB-specific types converted to strings.
                The conversion is done in-place, but the dictionary is also returned.

    Example:
        >>> doc = {'_id': ObjectId('507f1f77bcf86cd799439011'),
                  'timestamp': datetime.datetime(2023, 1, 1),
                  'nested': {'id': ObjectId('507f1f77bcf86cd799439012')}}
        >>> object_ids_to_str_in_entity(doc)
        {
            '_id': '507f1f77bcf86cd799439011',
            'timestamp': '2023-01-01T00:00:00',
            'nested': {'id': '507f1f77bcf86cd799439012'}
        }
    """

    for key, value in entity.items():
        if isinstance(value, ObjectId):
            entity[key] = str(value)
        elif isinstance(value, dict):
            serialize_entity(value)
        elif isinstance(value, list):
            for item in value:
                serialize_entity(item)
        elif isinstance(value, datetime.datetime):
            entity[key] = value.isoformat()

    return entity


def get_entries_map_from_db():
    """
    Returns a map of entries with the id as the key.

    Returns:
        dict: A map of entries with the id as the key.
    """

    MONGO_URI = os.getenv("MONGO_URI")
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME")

    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    entries_map = {
        str(entry["_id"]): serialize_entity(entry) for entry in collection.find()
    }

    client.close()
    return entries_map


def get_entries_map_from_json(file_path: str) -> dict:
    """
    Returns a map of entries from a JSON file.

    Parameters:
        file_path (str): The path to the JSON file.

    Returns:
        dict: A map of entries from the JSON file.
    """

    with open(file_path, "r") as file:
        entries_map = json.load(file)
    return entries_map


if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Story ranking script")
    parser.add_argument(
        "--use-file",
        type=str,
        help="Path to JSON file to use instead of database",
        default=None,
    )
    args = parser.parse_args()

    # Get all stories from database or file
    if args.use_file:
        entries_map = get_entries_map_from_json(args.use_file)
    else:
        entries_map = get_entries_map_from_db()

    # Calculate weighted scores for each story and its parent chain
    story_scores = {}
    PARENT_WEIGHT_DECAY = 0.9  # How much parent stories' votes are weighted

    for story in entries_map.values():
        current_weight = 1.0
        current_story_id = story["_id"]
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
            current_story_id = current_story["parentId"]
            current_weight *= PARENT_WEIGHT_DECAY

        story_scores[story["_id"]] = chain_total_score

    # Sort stories by their total scores
    sorted_stories = sorted(story_scores.items(), key=lambda x: x[1], reverse=True)

    # Print formatted story text with scores
    ranked_stories = []
    for story_id, total_score in sorted_stories:
        story = entries_map[story_id]
        full_text = f"{story['storyChain']} {story['text']}"
        ranked_stories.append(f'{total_score:.2f}: "{full_text}"')

    with open("data/ranked_stories.json", "w") as file:
        json.dump(ranked_stories, file, indent=4)

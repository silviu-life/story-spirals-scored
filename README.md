# Story Ranking System

This Python script implements a weighted scoring system for hierarchical stories, where each story can have parent stories and associated votes.

## Overview

The script processes story data from either MongoDB or a JSON file to rank stories based on their votes and their parent stories' votes. Each story's final score is calculated by considering:
- Direct votes on the story itself
- Votes on parent stories (with diminishing weight)

## Features

- Flexible data source: Can read from MongoDB or local JSON file
- Calculates weighted scores for stories considering their entire parent chain
- Upvotes count as +1, downvotes as -1
- Parent stories' votes are weighted with a decay factor (0.9 by default)
- Outputs both raw scores and formatted story text with scores

## Configuration

When using MongoDB, the script requires the following environment variables:
- `MONGO_URI`: MongoDB connection string
- `DATABASE_NAME`: Name of the database
- `COLLECTION_NAME`: Name of the collection containing stories

## Data Structure

Expected document structure for stories: 

```json
{
  "_id": "...",
  "parentId": "..." | null,
  "text": "...",
  "storyChain": "...",
  "votes": [
    {
      "userId": "...",
      "username": "...",
      "voteType": "upvote" | "downvote",
      "updateTime": "..."
    }
  ]
}
```

## Usage

To run the script with MongoDB:
```bash
python3 story-ranking.py
```

To run with a local JSON file:
```bash
python3 story-ranking.py --use-file path/to/stories.json
```

The script will output:
1. Raw scores for each story ID
2. Formatted story text with their calculated scores

## How Scoring Works

1. Each story's base score is calculated from its direct votes
2. Parent stories' votes are included with diminishing weight
3. The weight decay factor (0.9) is applied for each level up the parent chain
4. Final score is the sum of weighted votes across the entire story chain

For example, if a story has:
- 2 upvotes (score: 2)
- Parent story has 1 upvote (weighted score: 1 * 0.9 = 0.9)
- Grandparent story has 1 upvote (weighted score: 1 * 0.9 * 0.9 = 0.81)
- Final score would be: 2 + 0.9 + 0.81 = 3.71



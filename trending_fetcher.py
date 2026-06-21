#!/usr/bin/env python3
"""
Fetches trending tech topics from Hacker News (Free, No API Key required)
and saves them to a local JSON file for the homepage.
"""
import json
import urllib.request
import os
import time

OUTPUT_FILE = "os.path.join(os.path.dirname(os.path.abspath(__file__)), "searx", "static", "themes", "simple", "img", "trending.json")"
CACHE_TIME = 3600  # Cache for 1 hour

def fetch_trending():
    # If file exists and is fresh, don't fetch
    if os.path.exists(OUTPUT_FILE):
        if (time.time() - os.path.getmtime(OUTPUT_FILE)) < CACHE_TIME:
            print("Cache is fresh. Skipping fetch.")
            return

    try:
        # Fetch top story IDs from Hacker News
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        with urllib.request.urlopen(url, timeout=10) as response:
            story_ids = json.loads(response.read().decode())[:10]  # Get top 10
        
        trending = []
        for story_id in story_ids:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            with urllib.request.urlopen(story_url, timeout=10) as story_response:
                story = json.loads(story_response.read().decode())
                if story and 'title' in story:
                    trending.append({
                        'title': story['title'],
                        'url': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                        'score': story.get('score', 0)
                    })
        
        # Sort by score
        trending.sort(key=lambda x: x['score'], reverse=True)
        
        # Save to file
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(trending, f, indent=2)
        print(f"Successfully fetched {len(trending)} trending topics.")
        
    except Exception as e:
        print(f"Error fetching trending topics: {e}")

if __name__ == "__main__":
    fetch_trending()

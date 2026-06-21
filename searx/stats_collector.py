"""
Simple stats collector for SearXNG using Redis
"""
import redis
import json
import time
from datetime import datetime, timedelta

_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            _redis_client.ping()
        except Exception as e:
            print(f"[STATS] Redis connection failed: {e}")
            return None
    return _redis_client

def record_search(query, engines_used, results_count, duration):
    """Record a search in Redis (privacy-focused: only counts, no query storage)"""
    r = get_redis()
    if not r:
        return
    
    # Only increment counters - don't store actual queries
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Increment total searches
    r.incr('searxng:total_searches')
    
    # Increment daily count
    r.incr(f'searxng:searches:{today}')
    r.expire(f'searxng:searches:{today}', 30 * 24 * 3600)  # 30 days retention
    
    # Count engine usage (aggregate only)
    for engine in engines_used:
        r.incr(f'searxng:engine:{engine}:requests')
        r.incr(f'searxng:engine:{engine}:requests:{today}')
        r.expire(f'searxng:engine:{engine}:requests:{today}', 30 * 24 * 3600)
    
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        r.incr(f'searxng:searches:{today}')
        r.incr('searxng:total_searches')
        
        for engine in engines_used:
            r.incr(f'searxng:engine:{engine}:requests')
            r.incr(f'searxng:engine:{engine}:requests:{today}')
        
        r.incrby('searxng:total_results', results_count)
        r.incrbyfloat('searxng:total_duration', duration)
        r.expire(f'searxng:searches:{today}', 30 * 24 * 3600)
        
    except Exception as e:
        print(f"[STATS] Error recording search: {e}")

def get_stats():
    """Get all stats from Redis"""
    r = get_redis()
    if not r:
        return {}
    
    try:
        stats = {}
        stats['total_searches'] = int(r.get('searxng:total_searches') or 0)
        stats['total_results'] = int(r.get('searxng:total_results') or 0)
        stats['total_duration'] = float(r.get('searxng:total_duration') or 0)
        
        today = datetime.now().strftime('%Y-%m-%d')
        stats['today_searches'] = int(r.get(f'searxng:searches:{today}') or 0)
        
        engine_stats = {}
        engine_keys = r.keys('searxng:engine:*:requests')
        for key in engine_keys:
            engine_name = key.split(':')[2]
            requests = int(r.get(key) or 0)
            today_requests = int(r.get(f'searxng:engine:{engine_name}:requests:{today}') or 0)
            engine_stats[engine_name] = {
                'total_requests': requests,
                'today_requests': today_requests
            }
        
        stats['engines'] = engine_stats
        return stats
        
    except Exception as e:
        print(f"[STATS] Error getting stats: {e}")
        return {}

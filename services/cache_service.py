"""Response caching service for faster query responses."""
import hashlib
from typing import Optional, Dict
import time

class ResponseCache:
    """Simple in-memory cache for chatbot responses."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of cached responses
            ttl_seconds: Time-to-live for cached responses (default: 1 hour)
        """
        self.cache: Dict[str, dict] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def _get_key(self, query: str, language: str) -> str:
        """Generate cache key from query + language."""
        # Normalize query for better cache hits
        normalized = query.lower().strip()
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        return hashlib.md5(f"{normalized}:{language}".encode()).hexdigest()
    
    def get(self, query: str, language: str) -> Optional[dict]:
        """
        Get cached response if exists and not expired.
        
        Args:
            query: User query
            language: Detected language
            
        Returns:
            Cached response dict or None
        """
        key = self._get_key(query, language)
        cached_item = self.cache.get(key)
        
        if cached_item:
            # Check if expired
            age = time.time() - cached_item['timestamp']
            if age < self.ttl_seconds:
                print(f"[CACHE] HIT - Query: '{query[:50]}...'")
                return cached_item['response']
            else:
                # Remove expired item
                del self.cache[key]
                print(f"[CACHE] EXPIRED - Removed stale entry")
        
        print(f"[CACHE] MISS - Query: '{query[:50]}...'")
        return None
    
    def set(self, query: str, language: str, response: dict):
        """
        Cache response.
        
        Args:
            query: User query
            language: Detected language
            response: Response dict to cache
        """
        # Clean up if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest 20% when full
            remove_count = self.max_size // 5
            
            # Sort by timestamp and remove oldest
            sorted_items = sorted(
                self.cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            keys_to_remove = [k for k, v in sorted_items[:remove_count]]
            
            for k in keys_to_remove:
                del self.cache[k]
            
            print(f"[CACHE] Cleaned {remove_count} oldest entries")
        
        key = self._get_key(query, language)
        self.cache[key] = {
            'response': response,
            'timestamp': time.time()
        }
        print(f"[CACHE] STORED - Total cached: {len(self.cache)}")
    
    def clear(self):
        """Clear all cached responses."""
        self.cache.clear()
        print("[CACHE] Cleared all entries")
    
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds
        }


# Global cache instance
response_cache = ResponseCache(max_size=1000, ttl_seconds=3600)

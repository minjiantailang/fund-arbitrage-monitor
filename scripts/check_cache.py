
from src.models.database import get_database
import json

def check_cache():
    db = get_database()
    blob = db.get_setting("nav_cache_blob")
    updated_at = db.get_setting("nav_cache_updated_at")
    
    print(f"Cache updated at: {updated_at}")
    
    if blob:
        data = json.loads(blob)
        print(f"Total Cached Items: {len(data)}")
        if '501018' in data:
            print(f"501018 Value in Cache: {data['501018']}")
        else:
            print("501018 NOT found in cache!")
    else:
        print("No cache blob found")
    
    # 强制清除缓存以修复问题
    print("Clearing cache to force refresh...")
    db.set_setting("nav_cache_updated_at", "0") 
    print("Cache cleared.")

if __name__ == "__main__":
    check_cache()

"""Test the httpx 0.28 compatibility fix for scholarly"""
import sys
sys.path.insert(0, r"c:\Users\IO\research-lab-agents")

# Step 1: Apply the monkey-patch BEFORE any scholarly proxy usage
from scholarly import scholarly, ProxyGenerator
import httpx

print(f"httpx version: {httpx.__version__}")
print(f"scholarly ProxyGenerator loaded")

# Apply the patch directly
from app.agents.bibliometrie_agent import _patched_new_session
ProxyGenerator._new_session = _patched_new_session
print("Monkey-patch applied to ProxyGenerator._new_session")

# Step 2: Set up ScraperAPI
API_KEY = "ff8101b9f2824afe1316cbe140e031f0"
pg = ProxyGenerator()

print("\nSetting up ScraperAPI proxy...")
try:
    success = pg.ScraperAPI(API_KEY)
    print(f"ScraperAPI setup returned: {success}")
except Exception as e:
    print(f"ScraperAPI setup error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if not success:
    print("ScraperAPI proxy failed. Exiting.")
    sys.exit(1)

# Step 3: Search
scholarly.use_proxy(pg)
print("\nSearching for 'Yann LeCun'...")
try:
    results = scholarly.search_author("Yann LeCun")
    author = next(results, None)
    if author:
        name = author.get("name", "unknown")
        sid = author.get("scholar_id", "N/A")
        print(f"SUCCESS! Found: {name} (Scholar ID: {sid})")
    else:
        print("No results found")
except Exception as e:
    print(f"Search error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

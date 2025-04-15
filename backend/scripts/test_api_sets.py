# backend/scripts/test_api_sets.py

print("DEBUG: Starting execution of test_api_sets.py script file...")

import asyncio
import httpx
import sys
import os

# --- Adjust Python Path to Find 'app' Package ---
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
print(f"DEBUG: Python Path includes: {backend_dir}")
# --- End Path Adjustment ---

try:
    # --- Import only necessary local modules ---
    from app.config import settings # Need settings for the API key
    print("DEBUG: Local config module imported successfully.")
except ImportError as e:
    print(f"ERROR: Could not import app.config. Run from 'backend' dir: 'python -m scripts.test_api_sets'. Error: {e}")
    sys.exit(1)

# Constants
POKEMONTCG_API_V2_SETS_URL = "https://api.pokemontcg.io/v2/sets"
PAGE_SIZE_TEST = 50 # Fetch fewer sets just for testing

async def test_fetch_sets():
    """Fetches one page of sets and prints their totalCards value."""
    print("--- Testing API response for Sets ---")
    if not settings.POKEMONTCG_API_KEY:
        print("ERROR: POKEMONTCG_API_KEY not found in .env file or config. Cannot run test.")
        return

    headers = {"X-Api-Key": settings.POKEMONTCG_API_KEY}
    page = 1 # Fetch only the first page for this test

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        print(f"Fetching sets page {page} (up to {PAGE_SIZE_TEST} sets)...")
        params = {'page': page, 'pageSize': PAGE_SIZE_TEST}
        try:
            response = await client.get(POKEMONTCG_API_V2_SETS_URL, params=params)
            response.raise_for_status() # Raise HTTPError for bad responses
            data = response.json()
            api_sets = data.get('data', [])

            if not api_sets:
                print("No sets found on the first page from API.")
                return

            print(f"\n--- Data received for {len(api_sets)} sets on page 1 ---")
            for i, api_set_data in enumerate(api_sets):
                set_id = api_set_data.get('id')
                set_name = api_set_data.get('name')
                # --- Get the raw value for totalCards ---
                raw_total_cards = api_set_data.get('totalCards')
                # --- Print the relevant info ---
                print(f"Set {i+1}: ID={set_id}, Name='{set_name}', Raw 'totalCards' value: {repr(raw_total_cards)} (Type: {type(raw_total_cards)})")

        except httpx.HTTPStatusError as exc:
            print(f"HTTP error fetching sets: {exc.response.status_code} - {exc.response.text}")
        except httpx.RequestError as exc:
            print(f"Network error fetching sets: {exc}")
        except Exception as exc:
            print(f"An unexpected error occurred: {exc}")

    print("\n--- API Test Finished ---")


# ============================================
# Script Execution Block
# ============================================
if __name__ == "__main__":
    print("Running API Set Test Script...")
    try:
        asyncio.run(test_fetch_sets())
    except Exception as e:
        print(f"\n[CRITICAL ERROR] An error occurred in the main execution block: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        print("\nTest script execution attempt finished.")
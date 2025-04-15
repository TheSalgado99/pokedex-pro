# backend/scripts/update_set_counts.py

print("DEBUG: Starting execution of update_set_counts.py script file...")

import asyncio
import httpx
import sys
import os
from typing import List

# --- Adjust Python Path ---
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
print(f"DEBUG: Python Path includes: {backend_dir}")
# --- End Path Adjustment ---

try:
    # --- Local Imports ---
    from sqlmodel import select, SQLModel
    from sqlmodel.ext.asyncio.session import AsyncSession
    from app.config import settings
    from app.db import async_engine
    from app.models import Set
    print("DEBUG: Local modules imported successfully.")
except ImportError as e:
    print(f"ERROR: Could not import local modules. Run from 'backend' dir: 'python -m scripts.update_set_counts'. Error: {e}")
    sys.exit(1)

# Constants
POKEMONTCG_API_V2_CARDS_URL = "https://api.pokemontcg.io/v2/cards" # URL base per a cartes

async def update_missing_card_counts(session: AsyncSession):
    """Fetches total card counts using the /cards endpoint and updates sets with NULL counts."""
    print("--- Starting Set Count Update (using /cards endpoint) ---")
    if not settings.POKEMONTCG_API_KEY:
        print("ERROR: POKEMONTCG_API_KEY not found. Cannot update counts.")
        return

    # 1. Get sets from OUR DB that have total_cards as NULL
    statement = select(Set).where(Set.total_cards == None)
    results = await session.exec(statement)
    sets_to_update = results.all()

    if not sets_to_update:
        print("No sets found with missing total_cards count in the database. Nothing to do.")
        return

    print(f"Found {len(sets_to_update)} sets with missing card counts. Attempting to update...")
    updated_count = 0
    headers = {"X-Api-Key": settings.POKEMONTCG_API_KEY}

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        for i, db_set in enumerate(sets_to_update):
            print(f"Updating set {i+1}/{len(sets_to_update)}: {db_set.name} ({db_set.id})... ", end="")
            try:
                # 2. Fetch card count for this specific set from the CARDS API endpoint
                # We only need 1 result per page to get the totalCount metadata
                query = f'set.id:{db_set.id}'
                params = {'q': query, 'page': 1, 'pageSize': 1}
                response = await client.get(POKEMONTCG_API_V2_CARDS_URL, params=params) # Crida a /cards
                response.raise_for_status()
                api_response_data = response.json()

                # 3. Get totalCount value from the card search response
                total_cards_from_api = api_response_data.get('totalCount')

                # 4. Update if value found and is different (or was NULL)
                if total_cards_from_api is not None:
                    try:
                        card_count = int(total_cards_from_api)
                        # Només actualitzem si realment era NULL (o diferent, encara que no hauria de passar)
                        if db_set.total_cards is None or db_set.total_cards != card_count:
                           db_set.total_cards = card_count # Update the object fetched from DB
                           session.add(db_set) # Add it back to the session to mark it as changed
                           updated_count += 1
                           print(f"OK (Found count: {card_count})")
                        else:
                            print(f"OK (Already had value: {db_set.total_cards})")

                    except (ValueError, TypeError):
                         print(f"FAIL (API returned non-integer count: {total_cards_from_api})")
                else:
                     print("FAIL (API /cards endpoint did not return totalCount)")


            except httpx.HTTPStatusError as exc:
                print(f"FAIL (HTTP error {exc.response.status_code})")
            except Exception as exc:
                print(f"FAIL (Unexpected error: {exc})")

            # Commit periodically
            if (i + 1) % 50 == 0:
                try:
                    await session.commit()
                    print(f"--- Committed batch {i+1} ---")
                except Exception as e:
                    print(f"\nERROR committing batch up to set {db_set.id}: {e}. Rolling back batch.")
                    await session.rollback()

    # Final commit
    try:
        await session.commit()
        print("--- Final commit successful ---")
    except Exception as e:
        print(f"\nERROR during final commit: {e}. Rolling back remaining changes.")
        await session.rollback()

    print(f"--- Set Count Update Finished ---")
    print(f"Attempted to update {len(sets_to_update)} sets.")
    print(f"Successfully updated count for {updated_count} sets.")


async def main():
    """Main async function to run the update task."""
    print("Update Script: Creating session...")
    async with AsyncSession(async_engine) as session:
        print("Session created. Starting update...")
        await update_missing_card_counts(session)
        print("Update task finished.")


if __name__ == "__main__":
    print("Running Set Card Count Update Script (using /cards endpoint)...")
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n[CRITICAL ERROR] An error occurred in the main execution block: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        print("\nUpdate script execution attempt finished.")
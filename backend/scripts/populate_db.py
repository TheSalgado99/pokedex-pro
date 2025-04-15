# backend/scripts/populate_db.py

print("DEBUG: Starting execution of populate_db.py script file (Re-fetch Set before Update Mode)...")

import asyncio
import httpx
import sys
import os
from typing import List, Optional

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
    from app.models import Set, Card
    print("DEBUG: Local modules imported successfully.")
except ImportError as e:
    print(f"ERROR: Could not import local modules. Run from 'backend' dir: 'python -m scripts.populate_db'. Error: {e}")
    sys.exit(1) # Exit if essential imports fail

# Constants
POKEMONTCG_API_V2_SETS_URL = "https://api.pokemontcg.io/v2/sets"
POKEMONTCG_API_V2_CARDS_URL = "https://api.pokemontcg.io/v2/cards"
PAGE_SIZE = 250

# --- populate_sets_basic function remains the same ---
async def populate_sets_basic(session: AsyncSession) -> List[str]:
    """ Fetches sets, adds new ones, ignores total_cards. Returns list of set IDs in DB."""
    print("--- Starting Set Population (Basic Info Only) ---")
    set_ids_in_db = set()
    if not settings.POKEMONTCG_API_KEY:
        print("ERROR: POKEMONTCG_API_KEY not found. Skipping set processing.")
        try: existing_sets_result = await session.exec(select(Set.id)); set_ids_in_db = set(existing_sets_result.all())
        except Exception as e: print(f"Error fetching existing set IDs: {e}")
        return list(set_ids_in_db)
    headers = {"X-Api-Key": settings.POKEMONTCG_API_KEY}
    page = 1; total_fetched = 0; new_sets_added_count = 0; processed_set_ids_api = set()
    try: existing_sets_result = await session.exec(select(Set.id)); set_ids_in_db = set(existing_sets_result.all()); print(f"Found {len(set_ids_in_db)} existing sets in DB.")
    except Exception as e: print(f"Error fetching existing set IDs from DB: {e}."); set_ids_in_db = set()
    async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
        while True:
            print(f"Fetching sets page {page}...")
            params = {'page': page, 'pageSize': PAGE_SIZE}
            try: response = await client.get(POKEMONTCG_API_V2_SETS_URL, params=params); response.raise_for_status(); data = response.json(); api_sets = data.get('data', [])
            except httpx.HTTPStatusError as exc: print(f"HTTP error fetching sets (page {page}): {exc.response.status_code}. Stopping."); break
            except Exception as exc: print(f"Error during set fetching/processing page {page}: {exc}. Stopping."); break
            if not api_sets: print("No more sets found from API."); break
            current_page_fetched = len(api_sets); total_fetched += current_page_fetched; print(f"Fetched {current_page_fetched} sets page {page}. Total: {total_fetched}")
            new_sets_in_batch = []
            for api_set_data in api_sets:
                set_id = api_set_data.get('id')
                if not set_id or set_id in processed_set_ids_api: continue
                processed_set_ids_api.add(set_id)
                if set_id not in set_ids_in_db:
                    new_set = Set(id=set_id, name=api_set_data.get('name'), series=api_set_data.get('series'), release_date=api_set_data.get('releaseDate'), total_cards=None, logo_url=api_set_data.get('images', {}).get('logo'), symbol_url=api_set_data.get('images', {}).get('symbol'))
                    new_sets_in_batch.append(new_set)
            if new_sets_in_batch:
                session.add_all(new_sets_in_batch)
                try: await session.commit(); added_ids = {s.id for s in new_sets_in_batch}; set_ids_in_db.update(added_ids); new_sets_added_count += len(new_sets_in_batch); print(f"  Added {len(new_sets_in_batch)} new sets page {page}.")
                except Exception as e: print(f"ERROR committing sets page {page}: {e}. Rolling back."); await session.rollback()
            page += 1
            if current_page_fetched < PAGE_SIZE: print("Reached last page of sets."); break
    print(f"--- Set Population Finished ---"); print(f"New sets added: {new_sets_added_count}. Total sets in DB: {len(set_ids_in_db)}")
    return list(set_ids_in_db)

# ============================================
# Card Population Function (MODIFIED Set Update Logic)
# ============================================
async def populate_cards_and_update_set_counts(session: AsyncSession, set_ids_to_process: List[str]):
    """
    Fetches cards, saves new ones, AND updates Set total_cards count.
    Re-fetches Set object before updating to avoid lazy loading issues.
    Uses a single commit at the end of processing each set.
    """
    print(f"\n--- Starting Card Population & Set Count Update for {len(set_ids_to_process)} sets ---")
    if not settings.POKEMONTCG_API_KEY: print("ERROR: POKEMONTCG_API_KEY not found."); return

    headers = {"X-Api-Key": settings.POKEMONTCG_API_KEY}
    total_new_cards_added = 0; sets_updated_count = 0

    try: existing_cards_result = await session.exec(select(Card.id)); existing_card_ids = set(existing_cards_result.all()); print(f"Found {len(existing_card_ids)} existing cards in DB.")
    except Exception as e: print(f"Error fetching existing card IDs: {e}."); existing_card_ids = set()

    # No need to pre-fetch Sets into a map anymore, we'll fetch individually before update

    async with httpx.AsyncClient(headers=headers, timeout=120.0) as client:
        for i, set_id in enumerate(set_ids_to_process):
            print(f"\nProcessing Set {i+1}/{len(set_ids_to_process)}: {set_id}")
            page = 1; set_cards_fetched = 0; set_cards_added_this_run = 0; processed_card_ids_api = set()
            current_set_total_count = None
            cards_added_in_set_batch = []

            while True: # Loop through card pages for this set
                query = f'set.id:{set_id}'; params = {'q': query, 'page': page, 'pageSize': PAGE_SIZE, 'orderBy': 'number'}
                print(f"  Fetching cards page {page} for set {set_id}...")
                try: response = await client.get(POKEMONTCG_API_V2_CARDS_URL, params=params); response.raise_for_status(); data = response.json(); api_cards = data.get('data', [])
                except httpx.HTTPStatusError as exc: print(f"  HTTP error fetching cards: {exc.response.status_code}. Skipping set."); break
                except Exception as exc: print(f"  Error fetching/processing cards: {exc}. Skipping set."); break
                if not api_cards: break

                if page == 1: current_set_total_count = data.get('totalCount'); print(f"  Set {set_id} totalCount from API: {current_set_total_count}")
                current_page_fetched = len(api_cards); set_cards_fetched += current_page_fetched
                print(f"  Fetched {current_page_fetched} cards page {page}. Total for set: {set_cards_fetched}")

                for api_card_data in api_cards:
                    card_id = api_card_data.get('id')
                    if not card_id or card_id in processed_card_ids_api: continue
                    processed_card_ids_api.add(card_id)
                    if card_id not in existing_card_ids:
                        # --- Map data ---
                        card_hp_str = api_card_data.get('hp'); card_hp = int(card_hp_str) if card_hp_str and card_hp_str.isdigit() else None
                        subtypes_list = api_card_data.get('subtypes', []); card_subtype = ','.join(subtypes_list) if subtypes_list else None
                        new_card = Card(id=card_id, name=api_card_data.get('name'), number=api_card_data.get('number'), rarity=api_card_data.get('rarity'), type=api_card_data.get('supertype'), subtype=card_subtype, hp=card_hp, image_url_small=api_card_data.get('images', {}).get('small'), image_url_large=api_card_data.get('images', {}).get('large'), set_id=set_id)
                        cards_added_in_set_batch.append(new_card)
                        existing_card_ids.add(card_id) # Add to known IDs

                page += 1
                if current_page_fetched < PAGE_SIZE: break
                # await asyncio.sleep(0.1)

            # --- AFTER processing all cards for the set ---
            set_updated_this_run = False
            # 1. Stage new cards (if any) for commit
            if cards_added_in_set_batch:
                session.add_all(cards_added_in_set_batch)
                set_cards_added_this_run = len(cards_added_in_set_batch)
                total_new_cards_added += set_cards_added_this_run

            # 2. Fetch the Set from DB AGAIN and update its count if needed
            if current_set_total_count is not None:
                try:
                    # --- Re-fetch the Set object ---
                    db_set_to_update = await session.get(Set, set_id)
                    # --------------------------------
                    if db_set_to_update:
                        count_to_save = int(current_set_total_count)
                        if db_set_to_update.total_cards != count_to_save: # Compare with the freshly fetched object
                            print(f"  Updating Set {set_id} total_cards from {db_set_to_update.total_cards} to {count_to_save}")
                            db_set_to_update.total_cards = count_to_save
                            session.add(db_set_to_update) # Stage the update on the fresh object
                            set_updated_this_run = True
                            sets_updated_count += 1
                        else:
                            print(f"  Set {set_id} total_cards ({db_set_to_update.total_cards}) already matches API count ({count_to_save}). No update needed.")
                    else:
                         print(f"  Warning: Set {set_id} not found in DB when trying to update count.")

                except (ValueError, TypeError): print(f"  Warning: Could not convert totalCount '{current_set_total_count}' to int for set {set_id}.")
                except Exception as e: print(f"  ERROR fetching/updating set {set_id} count: {e}") # Catch potential errors during re-fetch or update stage

            # 3. Commit everything for this set (new cards + set update)
            if cards_added_in_set_batch or set_updated_this_run:
                try:
                    await session.commit()
                    print(f"Finished processing set {set_id}. Added: {set_cards_added_this_run} cards. Updated Count: {'Yes' if set_updated_this_run else 'No'}. COMMIT OK.")
                except Exception as e:
                    print(f"ERROR committing changes for set {set_id}: {e}. Rolling back.")
                    await session.rollback() # Rollback if combined commit fails
            else:
                 print(f"Finished processing set {set_id}. No changes to commit.")

    print(f"\n--- Card Population & Set Count Update Finished ---")
    print(f"Total new cards added to DB this run: {total_new_cards_added}")
    print(f"Total sets updated with card count this run: {sets_updated_count}")
    print(f"Total cards now in DB: {len(existing_card_ids)}")


# ============================================
# Main Execution Function (remains the same)
# ============================================
async def main():
    print("DB Population/Update Script: Creating session...")
    async with AsyncSession(async_engine) as session:
        print("Session created. Starting processing...")
        all_set_ids_in_db = await populate_sets_basic(session)
        if all_set_ids_in_db:
            # Call the function that now also updates counts
            await populate_cards_and_update_set_counts(session, all_set_ids_in_db)
        else: print("No sets found in DB to populate cards for.")
        print("\nPopulation/Update tasks finished.")

# ============================================
# Script Execution Block (remains the same)
# ============================================
if __name__ == "__main__":
    print("Running DB Population/Update Script (Re-fetch Set before Update Mode)...")
    try: asyncio.run(main())
    except Exception as e: print(f"\n[CRITICAL ERROR] {e}"); import traceback; print(traceback.format_exc())
    finally: print("\nScript execution attempt finished.")
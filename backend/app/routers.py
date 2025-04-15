# backend/app/routers.py

# --- Third Party Imports ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List # Or list

# --- Local Imports (Corrected) ---
from .models import Set, Card  # Import models from models.py in the same package
from .db import get_session    # Import the dependency function from db.py

# ============================================
# Router for Set Endpoints
# ============================================
router_sets = APIRouter(
    prefix="/sets",
    tags=["Sets"] # Group endpoints under "Sets" in Swagger UI
)

@router_sets.post("/", response_model=Set, status_code=status.HTTP_201_CREATED)
async def create_set(set_data: Set, session: AsyncSession = Depends(get_session)):
    """ Creates a new Pokémon TCG Set. """
    session.add(set_data)
    await session.commit()
    await session.refresh(set_data)
    return set_data

@router_sets.get("/", response_model=List[Set])
async def read_sets(session: AsyncSession = Depends(get_session), skip: int = 0, limit: int = 100):
    """ Retrieves a list of all Sets. """
    statement = select(Set).offset(skip).limit(limit)
    results = await session.exec(statement)
    sets = results.all()
    return sets

@router_sets.get("/{set_id}", response_model=Set)
async def read_set(set_id: str, session: AsyncSession = Depends(get_session)):
    """ Retrieves a specific Set by ID. """
    db_set = await session.get(Set, set_id)
    if not db_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Set with id '{set_id}' not found")
    return db_set

# TODO: Add PUT/PATCH and DELETE endpoints for Sets later

# ============================================
# Router for Card Endpoints
# ============================================
router_cards = APIRouter(
    prefix="/cards",
    tags=["Cards"] # Group endpoints under "Cards" in Swagger UI
)

@router_cards.post("/", response_model=Card, status_code=status.HTTP_201_CREATED)
async def create_card(card_data: Card, session: AsyncSession = Depends(get_session)):
    """ Creates a new Pokémon Card, ensuring the Set exists. """
    set_exists = await session.get(Set, card_data.set_id)
    if not set_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Set with id '{card_data.set_id}' not found. Cannot create card."
        )
    session.add(card_data)
    await session.commit()
    await session.refresh(card_data)
    return card_data

@router_cards.get("/", response_model=List[Card])
async def read_cards(
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    set_id: str | None = None
):
    """ Retrieves cards, optionally filtered by set_id. """
    statement = select(Card)
    if set_id:
        statement = statement.where(Card.set_id == set_id)
    statement = statement.offset(skip).limit(limit)
    results = await session.exec(statement)
    cards = results.all()
    return cards

@router_cards.get("/{card_id}", response_model=Card)
async def read_card(card_id: str, session: AsyncSession = Depends(get_session)):
    """ Retrieves a specific Card by ID. """
    db_card = await session.get(Card, card_id)
    if not db_card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Card with id '{card_id}' not found")
    return db_card

# TODO: Add PUT/PATCH and DELETE endpoints for Cards later
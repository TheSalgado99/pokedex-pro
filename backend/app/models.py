# backend/app/models.py

from sqlmodel import Field, Relationship, SQLModel
from typing import List, Optional

class Set(SQLModel, table=True):
    id: str = Field(primary_key=True, index=True)
    name: str = Field(index=True)
    series: Optional[str] = Field(default=None, index=True)
    release_date: Optional[str] = Field(default=None)
    total_cards: Optional[int] = Field(default=None)
    logo_url: Optional[str] = Field(default=None)
    symbol_url: Optional[str] = Field(default=None)
    cards: List["Card"] = Relationship(back_populates="set")

class Card(SQLModel, table=True):
    id: str = Field(primary_key=True, index=True)
    name: str = Field(index=True)
    number: str = Field(index=True)
    rarity: Optional[str] = Field(default=None, index=True)
    type: Optional[str] = Field(default=None, index=True) # API 'supertype'
    subtype: Optional[str] = Field(default=None) # API 'subtypes' joined
    hp: Optional[int] = Field(default=None)
    image_url_small: Optional[str] = Field(default=None)
    image_url_large: Optional[str] = Field(default=None)
    set_id: str = Field(foreign_key="set.id", index=True)
    set: Set = Relationship(back_populates="cards")

# --- Future Models ---
# class User(SQLModel, table=True): ...
# class OwnedCard(SQLModel, table=True): ...
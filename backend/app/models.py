# Pydantic models for data validation and serialization
from pydantic import BaseModel
from typing import List, Optional

# Example: Define models based on frontend/src/types/index.ts
class AlbumCardBase(BaseModel):
    id: str
    name: str
    number: str
    rarity: str
    imageUrl: str
    estimatedValue: Optional[float] = None
    isHit: bool
    psaCertNumber: Optional[str] = None
    purchasePrice: Optional[float] = None

class AlbumCard(AlbumCardBase):
    isOwned: bool # This might depend on the user context

class AlbumCollection(BaseModel):
    id: str
    name: str
    logoUrl: str
    totalCards: int
    # ownedCards: int # Calculated dynamically
    # ownedValue: float # Calculated dynamically
    cards: List[AlbumCardBase] # Base info for all cards in the set

class UserAlbumCollection(AlbumCollection):
     cards: List[AlbumCard] # Cards with ownership status
     ownedCards: int
     ownedValue: float

# Add other models as needed (User, PriceData, etc.)

// frontend/src/types/index.ts

export interface ApiSet { // Ja hauries de tenir aquesta o una similar
    id: string;
    name: string;
    series?: string | null;
    release_date?: string | null;
    logo_url?: string | null;
    symbol_url?: string | null;
    total_cards?: number | null;
}

// AFEGEIX AQUESTA NOVA INTERFÍCIE:
export interface ApiCard {
    id: string;
    name: string;
    number?: string | null;
    rarity?: string | null;
    type?: string | null;
    subtype?: string | null;
    hp?: number | null;
    image_url_small?: string | null;
    image_url_large?: string | null;
    set_id: string; // Important per saber a quin set pertany
}
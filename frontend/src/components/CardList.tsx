// frontend/src/components/CardList.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ApiCard } from '../types'; // Importa la interfície que acabem de definir

interface CardListProps {
  selectedSetId: string | null; // Rep l'ID del set seleccionat com a prop
}

const CardList: React.FC<CardListProps> = ({ selectedSetId }) => {
  const [cards, setCards] = useState<ApiCard[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // useEffect s'executarà cada cop que 'selectedSetId' canviï
  useEffect(() => {
    // Només fem la crida si hi ha un set seleccionat
    if (!selectedSetId) {
      setCards([]); // Buidem la llista si no hi ha set seleccionat
      return; // Sortim de l'efecte
    }

    const fetchCards = async () => {
      setLoading(true);
      setError(null);
      console.log(`CardList: Fetching cards for set ID: ${selectedSetId}`);
      // Construïm la URL de l'API per obtenir cartes filtrant per set_id
      const apiUrl = `http://127.0.0.1:8000/cards/?set_id=${selectedSetId}`;

      try {
        const response = await axios.get<ApiCard[]>(apiUrl, { timeout: 15000 }); // Més timeout per si hi ha moltes cartes
        setCards(response.data);
        console.log(`CardList: Received ${response.data.length} cards.`);
      } catch (err: any) {
        console.error("CardList: Error fetching cards:", err);
        let errorMessage = "Error loading cards for the selected set.";
        if (axios.isAxiosError(err)) {
          errorMessage = `Error ${err.response?.status || ''}: ${err.message}`;
        } else if (err instanceof Error) {
          errorMessage = err.message;
        }
        setError(errorMessage);
        setCards([]); // Buidem les cartes en cas d'error
      } finally {
        setLoading(false);
      }
    };

    fetchCards();
  }, [selectedSetId]); // Array de dependències: l'efecte es re-executa si selectedSetId canvia

  // --- Renderització ---
  if (!selectedSetId) {
    return <div style={{ marginTop: '20px', fontStyle: 'italic', color: '#777'}}>Please select a set to see its cards.</div>;
  }

  if (loading) {
    return <div>⏳ Loading cards for set {selectedSetId}...</div>;
  }

  if (error) {
    return <div style={{ color: 'red', marginTop: '20px' }}>❌ Error loading cards: {error}</div>;
  }

  return (
    <div style={{ marginTop: '20px' }}>
      <h3>Cards in Set {selectedSetId}</h3>
      {cards.length === 0 ? (
        <p>No cards found for this set.</p>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {/* Mostrem les cartes com a imatges petites */}
          {cards.map(card => (
            <div key={card.id} style={{ border: '1px solid #ddd', padding: '5px', textAlign: 'center' }}>
              <img
                src={card.image_url_small}
                alt={card.name}
                title={`${card.name} (${card.number}) - ${card.rarity}`}
                style={{ width: '100px', height: 'auto' }}
                loading="lazy"
              />
              <p style={{ fontSize: '0.8em', margin: '5px 0 0 0' }}>{card.number}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CardList;
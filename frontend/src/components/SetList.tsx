// frontend/src/components/SetList.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ApiSet } from '../types'; // Assegura't que ApiSet està definida a types/index.ts

// Interfície per a les Props que rep aquest component
interface SetListProps {
  onSetSelect: (setId: string) => void; // Funció del pare per notificar la selecció
  selectedSetId: string | null;      // L'ID del set actualment seleccionat (per ressaltar)
}

const SetList: React.FC<SetListProps> = ({ onSetSelect, selectedSetId }) => {
  const [sets, setSets] = useState<ApiSet[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const apiUrl = 'http://127.0.0.1:8000/sets/'; // URL del backend

  useEffect(() => {
    const fetchSets = async () => {
      setLoading(true); setError(null);
      try {
        const response = await axios.get<ApiSet[]>(apiUrl, { timeout: 10000 });
        // Ordenem els sets per data de llançament (més nous primer) si volem
        response.data.sort((a, b) => (b.release_date || '').localeCompare(a.release_date || ''));
        setSets(response.data);
        // console.log("Dades rebudes dels Sets:", response.data); // Manté si vols debugar
      } catch (err: any) {
        console.error("SetList: Error fetching sets:", err);
        let errorMessage = "Error loading sets.";
        // ... (Gestió d'errors com abans) ...
        if (axios.isAxiosError(err)) { /* ... */ } else if (err instanceof Error) { /* ... */ }
        setError(errorMessage);
      } finally { setLoading(false); }
    };
    fetchSets();
  }, [apiUrl]); // Executa només un cop

  if (loading) return <div>⏳ Loading Pokémon Sets...</div>;
  if (error) return <div style={{ color: 'red' }}>❌ Error loading sets: {error}</div>;

  return (
    <div className="set-list-container"> {/* Afegim una classe per estil CSS */}
      <h2>Available Pokémon TCG Sets</h2>
      {sets.length === 0 ? (<p>No sets found.</p>) : (
        <ul style={{ listStyle: 'none', padding: 0, maxHeight: '80vh', overflowY: 'auto' }}> {/* Fem la llista scrollable */}
          {sets.map(set => {
            const isSelected = set.id === selectedSetId;
            // Estil per a cada element de la llista
            const itemStyle: React.CSSProperties = {
              marginBottom: '5px',
              borderBottom: '1px solid #eee',
              padding: '8px 10px', // Una mica més de padding
              display: 'flex',
              alignItems: 'center',
              minHeight: '30px',
              cursor: 'pointer', // Cursor de 'mà' per indicar clicable
              backgroundColor: isSelected ? '#e0f0ff' : 'transparent', // Blau clar si seleccionat
              borderRadius: '5px', // Cantonades arrodonides
              transition: 'background-color 0.2s ease' // Transició suau
            };
            // Estil per al hover (canvi de fons)
            const handleMouseEnter = (e: React.MouseEvent<HTMLLIElement>) => {
                if (!isSelected) e.currentTarget.style.backgroundColor = '#f9f9f9';
            };
            const handleMouseLeave = (e: React.MouseEvent<HTMLLIElement>) => {
                if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent';
            };

            return (
              <li
                key={set.id}
                style={itemStyle}
                onClick={() => onSetSelect(set.id)} // <-- Crida a la funció del pare al fer clic
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
                title={`Select set: ${set.name}`} // Tooltip
              >
                {/* Imatges i Text (com abans) */}
                {set.symbol_url ? (<img src={set.symbol_url} alt="" style={{ height: '20px', width: '20px', objectFit: 'contain', marginRight: '10px' }} />) : (<span style={{ width: '20px', marginRight: '10px' }}></span>)}
                {set.logo_url ? (<img src={set.logo_url} alt="" style={{ height: '20px', objectFit: 'contain', marginRight: '10px', maxWidth: '80px' }}/>) : (<span style={{ width: '50px', marginRight: '10px' }}></span>)}
                <span style={{ fontWeight: isSelected ? 'bold' : 'normal' }}>{set.name || 'N/A'}</span> {/* Negreta si seleccionat */}
                <span style={{ marginLeft: '8px', color: '#555', fontSize: '0.9em' }}>({set.id || 'N/A'})</span>
                <span style={{ marginLeft: 'auto', paddingLeft: '15px', color: '#666', fontSize: '0.9em' }}>
                  ({set.total_cards ?? '?'} cards) {/* Mostra el número de cartes */}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

export default SetList;
// frontend/src/App.tsx
import React from 'react';
import SetList from './components/SetList'; // Importa el nou component
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>PokéndeX Pro</h1>
      </header>
      <main>
        {/* Afegeix el component aquí per mostrar la llista */}
        <SetList />
      </main>
      <footer>
        {/* Peu de pàgina */}
      </footer>
    </div>
  );
}

export default App;

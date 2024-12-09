// src/App.jsx
import React, { useState } from 'react';
// Ensure proper path resolution for components
import ChessGamesViewer from './components/ChessGamesViewer';
import ChessAnalysis from './components/ChessAnalysis';

/**
 * Root application component providing navigation and view management.
 * Handles switching between game viewer and analysis interfaces.
 * 
 * @component
 * @returns {JSX.Element} The root application interface
 */
function App() {
  // Track active view state with clear intent
  const [activeView, setActiveView] = useState('games');

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      {/* Navigation Controls */}
      <nav className="max-w-6xl mx-auto mb-4">
        <div className="flex gap-4 bg-white p-2 rounded-lg shadow-sm">
          <button 
            onClick={() => setActiveView('games')}
            className={`px-4 py-2 rounded transition-colors duration-200 ${
              activeView === 'games' 
                ? 'bg-blue-500 text-white' 
                : 'hover:bg-gray-100'
            }`}
            aria-current={activeView === 'games' ? 'page' : undefined}
          >
            Games
          </button>
          <button 
            onClick={() => setActiveView('analysis')}
            className={`px-4 py-2 rounded transition-colors duration-200 ${
              activeView === 'analysis' 
                ? 'bg-blue-500 text-white' 
                : 'hover:bg-gray-100'
            }`}
            aria-current={activeView === 'analysis' ? 'page' : undefined}
          >
            Analysis
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="max-w-6xl mx-auto">
        {activeView === 'games' ? <ChessGamesViewer /> : <ChessAnalysis />}
      </main>
    </div>
  );
}

export default App;
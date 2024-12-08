import React from 'react';
import ItemManagement from './components/ItemManagement';
import ChessGamesViewer from './components/ChessGamesViewer';

function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="mb-8">
        <ChessGamesViewer />
      </div>
    </div>
  );
}

export default App;

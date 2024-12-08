import React, { useEffect, useState, useCallback } from 'react';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';
import { Search, Calendar, ChevronRight, ChevronLeft } from 'lucide-react';


const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

export default function ChessGamesViewer() {
  const [games, setGames] = useState([]);
  const [selectedGame, setSelectedGame] = useState(null);
  const [chess, setChess] = useState(new Chess());
  const [moveIndex, setMoveIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [playerName, setPlayerName] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 5000);
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  

  const handleKeyPress = useCallback((event) => {
    if (!selectedGame) return;
    
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      if (moveIndex > 0) {
        setMoveIndex(prev => prev - 1);
      }
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      const totalMoves = selectedGame.moves.split(' ').length;
      if (moveIndex < totalMoves) {
        setMoveIndex(prev => prev + 1);
      }
    }
  }, [selectedGame, moveIndex]);

  const fetchGames = useCallback(async () => {
    try {
        setIsLoading(true);
        const queryParams = new URLSearchParams();
        if (debouncedSearchTerm.trim()) {  // Only add if there's actual content
            queryParams.append('player_name', debouncedSearchTerm.trim());
        }
        if (startDate) {
            queryParams.append('start_date', startDate);
        }
        if (endDate) {
            queryParams.append('end_date', endDate);
        }

        const url = `${API_URL}/games${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch games');
        const data = await response.json();
        setGames(data);
        setError(null);
    } catch (error) {
        setError(error.message);
        console.error('Error fetching games:', error);
    } finally {
        setIsLoading(false);
    }
  }, [API_URL, debouncedSearchTerm, startDate, endDate]);
  
  useEffect(() => {
    fetchGames();
  }, [fetchGames]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [handleKeyPress]);

  const selectGame = useCallback((game) => {
    setSelectedGame(game);
    const newChess = new Chess();
    setChess(newChess);
    setMoveIndex(0);
  }, []);

  const loadPosition = useCallback(() => {
    if (!selectedGame) return;
    const newChess = new Chess();
    const moves = selectedGame.moves.split(' ');
    for (let i = 0; i < moveIndex && i < moves.length; i++) {
      try {
        newChess.move({
          from: moves[i].slice(0,2),
          to: moves[i].slice(2,4),
          promotion: moves[i].length > 4 ? moves[i][4] : undefined
        });
      } catch (e) {
        console.error('Invalid move:', moves[i], e);
      }
    }
    setChess(newChess);
  }, [selectedGame, moveIndex]);

  useEffect(() => {
    loadPosition();
  }, [loadPosition]);

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    fetchGames();
  };

  
  
  const nextMove = useCallback(() => {
    if (!selectedGame) return;
    const moves = selectedGame.moves.split(' ');
    if (moveIndex < moves.length) {
      setMoveIndex(moveIndex + 1);
    }
  }, [selectedGame, moveIndex]);

  const prevMove = useCallback(() => {
    if (moveIndex > 0) {
      setMoveIndex(moveIndex - 1);
    }
  }, [moveIndex]);

  
  

  const renderGameItem = useCallback((game) => (
    <div 
      key={game.id} 
      className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition-colors
        ${selectedGame?.id === game.id ? 'bg-blue-50' : ''}`}
      onClick={() => selectGame(game)}
    >
      <div className="font-medium">Game {game.id}</div>
      <div className="text-sm text-gray-600">
        {game.date && new Date(game.date).toLocaleDateString()}
      </div>
      <div className="text-sm mt-1 font-medium">
        <span className="text-blue-600">
          {game.white_player?.name || 'Unknown'}
        </span>
        <span className="mx-2 text-gray-500">vs</span>
        <span className="text-black">
          {game.black_player?.name || 'Unknown'}
        </span>
      </div>
      <div className="text-sm text-gray-500">
        Result: <span className="font-medium">{game.result}</span>
      </div>
    </div>
  ), [selectedGame, selectGame]);

  const renderContent = () => {
    if (isLoading) return <div className="p-6">Loading games...</div>;
    if (error) return <div className="p-6 text-red-500">Error: {error}</div>;

    return (
      <div className="p-6 max-w-6xl mx-auto bg-white rounded-lg shadow">
        <h1 className="text-2xl font-bold mb-6">Chess Games Viewer</h1>
        
        {/* Filter Section */}
        <form onSubmit={handleFilterSubmit} className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex flex-col">
              <label className="text-sm font-medium mb-1">Player Name</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search by player name"
                  className="pl-10 p-2 w-full border rounded"
                />
              </div>
            </div>
            
            <div className="flex flex-col">
              <label className="text-sm font-medium mb-1">Start Date</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="pl-10 p-2 w-full border rounded"
                />
              </div>
            </div>
            
            <div className="flex flex-col">
              <label className="text-sm font-medium mb-1">End Date</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="pl-10 p-2 w-full border rounded"
                />
              </div>
            </div>
          </div>
          
          <div className="mt-4 flex justify-end">
            <button
              type="submit"
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Apply Filters
            </button>
          </div>
        </form>

        {/* Main Content */}
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Game List */}
          <div className="lg:w-1/3">
            <h2 className="text-xl font-semibold mb-4">Game List</h2>
            {isLoading ? (
              <div className="text-center py-4">Loading games...</div>
            ) : error ? (
              <div className="text-red-500 py-4">{error}</div>
            ) : games.length === 0 ? (
              <div className="text-gray-500 py-4">No games found</div>
            ) : (
              <div className="max-h-[calc(100vh-400px)] overflow-auto border rounded">
                {games.map(renderGameItem)}
              </div>
            )}
          </div>

          {/* Chessboard */}
          <div className="lg:w-2/3">
            {selectedGame ? (
              <div className="flex flex-col items-center">
                <Chessboard 
                  position={chess.fen()} 
                  boardWidth={480}
                  arePiecesDraggable={false}
                  boardOrientation="white"
                />
                
                <div className="mt-6 flex items-center gap-4">
                  <button 
                    onClick={prevMove}
                    disabled={moveIndex === 0}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </button>
                  
                  <span className="text-sm text-gray-600">
                    Move {moveIndex} of {selectedGame.moves.split(' ').length}
                  </span>
                  
                  <button 
                    onClick={nextMove}
                    disabled={moveIndex >= selectedGame.moves.split(' ').length}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-[480px] text-gray-500">
                Select a game to view
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };
  return renderContent();
}
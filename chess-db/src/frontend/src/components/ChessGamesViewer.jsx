import React, { useState, useEffect, useCallback } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { Calendar, Search, ChevronLeft, ChevronRight, SkipBack, SkipForward } from 'lucide-react';

export default function ChessGamesViewer() {
  const [games, setGames] = useState([]);
  const [selectedGame, setSelectedGame] = useState(null);
  const [chess, setChess] = useState(new Chess());
  const [moveIndex, setMoveIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchQuery, setSearchQuery] = useState(''); // Actual search term to use in API call
  const [dateRange, setDateRange] = useState({ start: '', end: '' });


  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  // Add a date formatter with validation
  const formatGameDate = useCallback((dateStr) => {
    if (!dateStr) return 'Date unknown';
    
    try {
      const date = new Date(dateStr);
      
      // Check if date is invalid
      if (isNaN(date.getTime())) {
        return 'Date unknown';
      }

      // Check if date is in the future
      const today = new Date();
      if (date > today) {
        // For future dates, display as "Scheduled" or fall back to a reasonable date
        return 'Scheduled';
      }

      // Format valid past dates
      return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch (e) {
      console.warn('Error parsing date:', e);
      return 'Date unknown';
    }
  }, []);

  // Update the date filter handlers to validate dates
  const handleDateChange = useCallback((type, value) => {
    const date = new Date(value);
    if (isNaN(date.getTime())) {
      console.warn('Invalid date selected');
      return;
    }

    // Ensure start date isn't after end date and vice versa
    setDateRange(prev => {
      if (type === 'start' && prev.end && value > prev.end) {
        return { ...prev, start: prev.end };
      }
      if (type === 'end' && prev.start && value < prev.start) {
        return { ...prev, end: prev.start };
      }
      return { ...prev, [type]: value };
    });
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    setSearchQuery(searchTerm);
  };

  const fetchGames = useCallback(async () => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams();
      if (searchQuery) params.append('player_name', searchQuery);
      if (dateRange.start) params.append('start_date', dateRange.start);
      if (dateRange.end) params.append('end_date', dateRange.end);

      const response = await fetch(`${API_URL}/games?${params}`);
      if (!response.ok) throw new Error('Failed to fetch games');
      const data = await response.json();
      setGames(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL, searchQuery, dateRange]);

  useEffect(() => {
    fetchGames();
  }, [fetchGames]);

  const handleGameSelect = useCallback((game) => {
    setSelectedGame(game);
    setMoveIndex(0);
    setChess(new Chess());
  }, []);

  const updatePosition = useCallback(() => {
    if (!selectedGame) return;
    const moves = selectedGame.moves.split(' ');
    const newChess = new Chess();
    
    for (let i = 0; i < moveIndex && i < moves.length; i++) {
      try {
        newChess.move({
          from: moves[i].slice(0, 2),
          to: moves[i].slice(2, 4),
          promotion: moves[i][4]
        });
      } catch (e) {
        console.error('Invalid move:', moves[i], e);
      }
    }
    setChess(newChess);
  }, [selectedGame, moveIndex]);

  useEffect(() => {
    updatePosition();
  }, [updatePosition]);

  const handleKeyPress = useCallback((event) => {
    if (!selectedGame) return;
    
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      setMoveIndex(prev => Math.max(0, prev - 1));
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      const maxMoves = selectedGame.moves.split(' ').length;
      setMoveIndex(prev => Math.min(maxMoves, prev + 1));
    }
  }, [selectedGame]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [handleKeyPress]);

  const renderGameItem = useCallback((game) => (
    <div
      key={game.id}
      onClick={() => handleGameSelect(game)}
      className={`p-4 border-b cursor-pointer transition-colors hover:bg-gray-50 
        ${selectedGame?.id === game.id ? 'bg-blue-50' : ''}`}
    >
      <div className="flex justify-between items-start">
        <div>
          <div className="font-medium text-gray-900">
            {game.white_player?.name || 'Unknown'} vs {game.black_player?.name || 'Unknown'}
          </div>
          <div className="text-sm text-gray-600">
            {formatGameDate(game.date)}
          </div>
        </div>
        <div className="text-sm font-medium text-gray-900">{game.result}</div>
      </div>
      <div className="mt-1 text-sm text-gray-500">ECO: {game.eco}</div>
    </div>
  ), [selectedGame, formatGameDate]);


  const moveControls = (
    <div className="flex items-center justify-center gap-4 mt-4">
      <button
        onClick={() => setMoveIndex(0)}
        disabled={!selectedGame || moveIndex === 0}
        className="p-2 rounded hover:bg-gray-100 disabled:opacity-50"
      >
        <SkipBack className="h-5 w-5" />
      </button>
      <button
        onClick={() => setMoveIndex(prev => Math.max(0, prev - 1))}
        disabled={!selectedGame || moveIndex === 0}
        className="p-2 rounded hover:bg-gray-100 disabled:opacity-50"
      >
        <ChevronLeft className="h-5 w-5" />
      </button>
      <div className="text-sm text-gray-600 min-w-[100px] text-center">
        {selectedGame ? `Move ${moveIndex} of ${selectedGame.moves.split(' ').length}` : '-'}
      </div>
      <button
        onClick={() => setMoveIndex(prev => prev + 1)}
        disabled={!selectedGame || moveIndex >= selectedGame?.moves.split(' ').length}
        className="p-2 rounded hover:bg-gray-100 disabled:opacity-50"
      >
        <ChevronRight className="h-5 w-5" />
      </button>
      <button
        onClick={() => setMoveIndex(selectedGame?.moves.split(' ').length || 0)}
        disabled={!selectedGame || moveIndex >= selectedGame?.moves.split(' ').length}
        className="p-2 rounded hover:bg-gray-100 disabled:opacity-50"
      >
        <SkipForward className="h-5 w-5" />
      </button>
    </div>
  );

  // Update the game details section to use the formatted date
  const renderGameDetails = useCallback(() => {
    if (!selectedGame) return null;

    return (
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-medium mb-2">Game Details</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-gray-600">White</div>
            <div className="font-medium">{selectedGame.white_player?.name || 'Unknown'}</div>
          </div>
          <div>
            <div className="text-gray-600">Black</div>
            <div className="font-medium">{selectedGame.black_player?.name || 'Unknown'}</div>
          </div>
          <div>
            <div className="text-gray-600">Date</div>
            <div className="font-medium">
              {formatGameDate(selectedGame.date)}
            </div>
          </div>
          <div>
            <div className="text-gray-600">Result</div>
            <div className="font-medium">{selectedGame.result}</div>
          </div>
          {selectedGame.white_elo && selectedGame.black_elo && (
            <>
              <div>
                <div className="text-gray-600">White Elo</div>
                <div className="font-medium">{selectedGame.white_elo}</div>
              </div>
              <div>
                <div className="text-gray-600">Black Elo</div>
                <div className="font-medium">{selectedGame.black_elo}</div>
              </div>
            </>
          )}
        </div>
      </div>
    );
  }, [selectedGame, formatGameDate]);
  
  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto bg-white p-6 rounded-lg shadow-lg">
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-4">Chess Games Explorer</h1>
          
          {/* Filters */}
          <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Player Search</label>
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
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => handleDateChange('start', e.target.value)}
                  max={dateRange.end || undefined}
                  className="pl-10 p-2 w-full border rounded"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => handleDateChange('end', e.target.value)}
                  min={dateRange.start || undefined}
                  className="pl-10 p-2 w-full border rounded"
                />
              </div>
            </div>

            <div className="md:col-span-3 flex justify-end">
              <button
                type="submit"
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Apply Filters
              </button>
            </div>
          </form>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Game List */}
          <div className="lg:w-1/3">
            <h2 className="text-xl font-semibold mb-4">Game List</h2>
            <div className="border rounded-lg overflow-hidden">
              {isLoading ? (
                <div className="p-4 text-center text-gray-600">Loading games...</div>
              ) : error ? (
                <div className="p-4 text-center text-red-600">{error}</div>
              ) : games.length === 0 ? (
                <div className="p-4 text-center text-gray-600">No games found</div>
              ) : (
                <div className="max-h-[600px] overflow-y-auto">
                  {games.map(renderGameItem)}
                </div>
              )}
            </div>
          </div>

          {/* Chessboard */}
          <div className="lg:w-2/3">
            <h2 className="text-xl font-semibold mb-4">Game Viewer</h2>
            {selectedGame ? (
              <div>
                <Chessboard 
                  position={chess.fen()} 
                  boardWidth={480}
                  arePiecesDraggable={false}
                />
                {moveControls}
                {renderGameDetails()}
              </div>
            ) : (
              <div className="h-[480px] flex items-center justify-center text-gray-500 border rounded-lg">
                Select a game to view
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
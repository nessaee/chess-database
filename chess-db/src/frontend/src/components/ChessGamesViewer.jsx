import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { Calendar, Search, ChevronLeft, ChevronRight, SkipBack, SkipForward } from 'lucide-react';

// Utility functions
const formatDate = (dateStr) => {
  if (!dateStr) return 'Date unknown';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return 'Date unknown';
    if (date > new Date()) return 'Scheduled';
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch (e) {
    console.warn('Error parsing date:', e);
    return 'Date unknown';
  }
};

// Component for the game filters section
const GameFilters = ({ searchTerm, setSearchTerm, dateRange, onDateChange, onSearch }) => (
  <form onSubmit={onSearch} className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
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
          onChange={(e) => onDateChange('start', e.target.value)}
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
          onChange={(e) => onDateChange('end', e.target.value)}
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
);

// Component for the game list
const GameList = ({ games, selectedGame, onGameSelect, isLoading, error }) => {
  if (isLoading) return <div className="p-4 text-center text-gray-600">Loading games...</div>;
  if (error) return <div className="p-4 text-center text-red-600">{error}</div>;
  if (!games.length) return <div className="p-4 text-center text-gray-600">No games found</div>;

  return (
    <div className="max-h-[600px] overflow-y-auto">
      {games.map(game => (
        <div
          key={game.id}
          onClick={() => onGameSelect(game)}
          className={`p-4 border-b cursor-pointer transition-colors hover:bg-gray-50 
            ${selectedGame?.id === game.id ? 'bg-blue-50' : ''}`}
        >
          <div className="flex justify-between items-start">
            <div>
              <div className="font-medium text-gray-900">
                {game.white_player?.name || 'Unknown'} vs {game.black_player?.name || 'Unknown'}
              </div>
              <div className="text-sm text-gray-600">{formatDate(game.date)}</div>
            </div>
            <div className="text-sm font-medium text-gray-900">{game.result}</div>
          </div>
          <div className="mt-1 text-sm text-gray-500">ECO: {game.eco}</div>
        </div>
      ))}
    </div>
  );
};

// Component for the game controls
const GameControls = ({ moveIndex, totalMoves, onMoveChange, disabled }) => (
  <div className="flex items-center justify-between bg-white border rounded-lg p-2 mb-4">
    <button
      onClick={() => onMoveChange(0)}
      disabled={disabled || moveIndex === 0}
      className="p-2 rounded hover:bg-gray-100 disabled:opacity-50"
    >
      <SkipBack className="h-5 w-5" />
    </button>
    <button
      onClick={() => onMoveChange(Math.max(0, moveIndex - 1))}
      disabled={disabled || moveIndex === 0}
      className="p-2 rounded hover:bg-gray-100 disabled:opacity-50"
    >
      <ChevronLeft className="h-5 w-5" />
    </button>
    <div className="text-sm text-gray-600 font-medium">
      {disabled ? '-' : `Move ${moveIndex} of ${totalMoves}`}
    </div>
    <button
      onClick={() => onMoveChange(moveIndex + 1)}
      disabled={disabled || moveIndex >= totalMoves}
      className="p-2 rounded hover:bg-gray-100 disabled:opacity-50"
    >
      <ChevronRight className="h-5 w-5" />
    </button>
    <button
      onClick={() => onMoveChange(totalMoves)}
      disabled={disabled || moveIndex >= totalMoves}
      className="p-2 rounded hover:bg-gray-100 disabled:opacity-50"
    >
      <SkipForward className="h-5 w-5" />
    </button>
  </div>
);

// Component for the game details
const GameDetails = ({ game }) => (
  <div className="bg-white border rounded-lg p-4">
    <h3 className="font-medium mb-2">Game Details</h3>
    <div className="grid grid-cols-2 gap-4 text-sm">
      <div>
        <div className="text-gray-600">White</div>
        <div className="font-medium">{game.white_player?.name || 'Unknown'}</div>
      </div>
      <div>
        <div className="text-gray-600">Black</div>
        <div className="font-medium">{game.black_player?.name || 'Unknown'}</div>
      </div>
      <div>
        <div className="text-gray-600">Date</div>
        <div className="font-medium">{formatDate(game.date)}</div>
      </div>
      <div>
        <div className="text-gray-600">Result</div>
        <div className="font-medium">{game.result}</div>
      </div>
      <div>
        <div className="text-gray-600">ECO</div>
        <div className="font-medium">{game.eco}</div>
      </div>
    </div>
  </div>
);

// Component for the moves list
const MovesList = ({ moves, moveIndex, onMoveSelect, activeItemRef, moveListRef }) => {
  if (!moves.length) return null;

  const moveRows = [];
  for (let i = 0; i < moves.length; i += 2) {
    const whiteMove = moves[i];
    const blackMove = moves[i + 1];
    const isWhiteActive = i === moveIndex - 1;
    const isBlackActive = blackMove && (i + 1) === moveIndex - 1;

    moveRows.push(
      <div 
        key={i} 
        className="grid grid-cols-12 gap-1 hover:bg-gray-50 text-sm"
        ref={isWhiteActive || isBlackActive ? activeItemRef : null}
      >
        <div className="col-span-2 text-gray-500 pl-2">
          {whiteMove.moveNumber}.
        </div>
        <div 
          className={`col-span-5 px-2 py-1 cursor-pointer rounded transition-colors
            ${isWhiteActive ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
          onClick={() => onMoveSelect(i + 1)}
        >
          {whiteMove.san}
        </div>
        {blackMove && (
          <div 
            className={`col-span-5 px-2 py-1 cursor-pointer rounded transition-colors
              ${isBlackActive ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
            onClick={() => onMoveSelect(i + 2)}
          >
            {blackMove.san}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border h-[320px] flex flex-col">
      <div className="sticky top-0 z-10 bg-gray-50 border-b grid grid-cols-12 gap-1 text-sm font-medium p-2">
        <div className="col-span-2">#</div>
        <div className="col-span-5">White</div>
        <div className="col-span-5">Black</div>
      </div>
      <div ref={moveListRef} className="flex-1 overflow-y-auto p-2 scroll-smooth">
        {moveRows}
      </div>
    </div>
  );
};

// Main ChessGamesViewer component
export default function ChessGamesViewer() {
  // Base state
  const [games, setGames] = useState([]);
  const [selectedGame, setSelectedGame] = useState(null);
  const [chess, setChess] = useState(new Chess());
  const [moveIndex, setMoveIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Search and filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  // Game analysis state
  const [currentMoves, setCurrentMoves] = useState([]);

  // Refs for scroll management
  const moveListRef = useRef(null);
  const activeItemRef = useRef(null);

  // API configuration
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';


  // Utility functions for game management
  const generateSANMoves = useCallback((uciMoves) => {
    const tempChess = new Chess();
    return uciMoves.split(' ').map(uciMove => {
      try {
        const move = {
          from: uciMove.slice(0, 2),
          to: uciMove.slice(2, 4),
          promotion: uciMove[4]
        };
        const san = tempChess.move(move).san;
        const isWhite = tempChess.turn() === 'b';
        const fullMove = tempChess.moveNumber();
        return {
          uci: uciMove,
          san,
          color: isWhite ? 'white' : 'black',
          moveNumber: isWhite ? fullMove : null
        };
      } catch (e) {
        console.error('Invalid move:', uciMove, e);
        return null;
      }
    }).filter(Boolean);
  }, []);

  // Event handlers
  const handleGameSelect = useCallback((game) => {
    setSelectedGame(game);
    setMoveIndex(0);
    setChess(new Chess());
    setCurrentMoves(generateSANMoves(game.moves));
  }, [generateSANMoves]);

  const handleDateChange = useCallback((type, value) => {
    const date = new Date(value);
    if (isNaN(date.getTime())) {
      console.warn('Invalid date selected');
      return;
    }
    setDateRange(prev => ({
      ...prev,
      [type]: value
    }));
  }, []);

  // Effect for scrolling active move into view
  useEffect(() => {
    if (activeItemRef.current) {
      activeItemRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [moveIndex]);

  // Effect for keyboard navigation
  useEffect(() => {
    const handleKeyPress = (event) => {
      if (!selectedGame) return;
      
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        setMoveIndex(prev => Math.max(0, prev - 1));
      } else if (event.key === 'ArrowRight') {
        event.preventDefault();
        setMoveIndex(prev => Math.min(currentMoves.length, prev + 1));
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedGame, currentMoves.length]);

  // Games fetching logic
  const fetchGames = useCallback(async () => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams();
      
      if (searchQuery) params.append('player_name', searchQuery);
      if (dateRange.start) params.append('start_date', dateRange.start);
      if (dateRange.end) params.append('end_date', dateRange.end);

      const response = await fetch(`${API_URL}/games?${params}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch games');
      }
      
      const data = await response.json();
      setGames(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching games:', err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL, searchQuery, dateRange]);

  // Effect to fetch games when filters change
  useEffect(() => {
    fetchGames();
  }, [fetchGames]);


  // Game position management
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

  // Effect to update board position
  useEffect(() => {
    updatePosition();
  }, [updatePosition]);


  const handleSearch = useCallback((e) => {
    e.preventDefault();
    setSearchQuery(searchTerm);
  }, [searchTerm]);

  const handleMoveSelect = useCallback((index) => {
    setMoveIndex(index);
  }, []);

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto bg-white p-6 rounded-lg shadow-lg">
        <h1 className="text-2xl font-bold mb-6">Chess Games Explorer</h1>
        
        <GameFilters
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          dateRange={dateRange}
          onDateChange={handleDateChange}
          onSearch={handleSearch}
        />
        
        <div className="flex flex-col lg:flex-row gap-8">
          <div className="lg:w-1/4">
            <h2 className="text-xl font-semibold mb-4">Game List</h2>
            <div className="border rounded-lg overflow-hidden">
              <GameList
                games={games}
                selectedGame={selectedGame}
                onGameSelect={handleGameSelect}
                isLoading={isLoading}
                error={error}
              />
            </div>
          </div>

          <div className="lg:w-3/4">
            <h2 className="text-xl font-semibold mb-4">Game Viewer</h2>
            {selectedGame ? (
              <div className="flex flex-col xl:flex-row gap-6">
                <div className="xl:w-[480px]">
                  <Chessboard 
                    position={chess.fen()} 
                    boardWidth={480}
                    arePiecesDraggable={false}
                  />
                  <GameControls
                    moveIndex={moveIndex}
                    totalMoves={currentMoves.length}
                    onMoveChange={setMoveIndex}
                    disabled={!selectedGame}
                  />
                  <GameDetails game={selectedGame} />
                </div>

                <div className="xl:flex-1">
                  <div className="sticky top-0">
                    <h3 className="font-medium mb-2">Moves</h3>
                    <MovesList
                      moves={currentMoves}
                      moveIndex={moveIndex}
                      onMoveSelect={setMoveIndex}
                      activeItemRef={activeItemRef}
                      moveListRef={moveListRef}
                    />
                  </div>
                </div>
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
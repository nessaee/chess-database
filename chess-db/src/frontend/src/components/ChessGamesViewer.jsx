import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { Calendar, ChevronLeft, ChevronRight, SkipBack, SkipForward } from 'lucide-react';
import PlayerSearch from './PlayerSearch';
import { GameService } from '../services/GameService';

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
const GameFilters = ({ onPlayerSelect, dateRange, onDateChange, onSearch, onlyDated, setOnlyDated }) => (
  <form onSubmit={onSearch} className="container mx-auto p-4 mb-6">
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Player Search</label>
        <PlayerSearch onPlayerSelect={onPlayerSelect} />
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

      <div className="md:col-span-3">
        <label className="inline-flex items-center">
          <input
            type="checkbox"
            checked={onlyDated}
            onChange={(e) => setOnlyDated(e.target.checked)}
            className="form-checkbox h-4 w-4 text-blue-600"
          />
          <span className="ml-2 text-sm text-gray-700">Only show games with dates</span>
        </label>
      </div>

      <div className="md:col-span-3 flex justify-end">
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Apply Filters
        </button>
      </div>
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
        <div className="font-medium">
          {game.white_player?.name || 'Unknown'}
          {game.white_player?.rating && ` (${game.white_player.rating})`}
        </div>
      </div>
      <div>
        <div className="text-gray-600">Black</div>
        <div className="font-medium">
          {game.black_player?.name || 'Unknown'}
          {game.black_player?.rating && ` (${game.black_player.rating})`}
        </div>
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
  if (!moves.length) return <div className="text-gray-600">No moves available</div>;

  // Create pairs of moves for display
  const movePairs = [];
  for (let i = 0; i < moves.length; i += 2) {
    movePairs.push({
      number: Math.floor(i / 2) + 1,
      white: moves[i],
      black: moves[i + 1]
    });
  }

  return (
    <div 
      ref={moveListRef}
      className="border rounded p-4 max-h-[400px] overflow-y-auto"
    >
      <div className="grid grid-cols-[auto_1fr_1fr] gap-2">
        {movePairs.map(({ number, white, black }, index) => (
          <React.Fragment key={number}>
            <div className="text-gray-500 text-right">{number}.</div>
            <div
              ref={moveIndex === index * 2 ? activeItemRef : null}
              onClick={() => onMoveSelect(index * 2)}
              className={`cursor-pointer px-2 rounded ${
                moveIndex === index * 2 ? 'bg-blue-500 text-white' : 'hover:bg-gray-100'
              }`}
            >
              {white}
            </div>
            {black && (
              <div
                ref={moveIndex === index * 2 + 1 ? activeItemRef : null}
                onClick={() => onMoveSelect(index * 2 + 1)}
                className={`cursor-pointer px-2 rounded ${
                  moveIndex === index * 2 + 1 ? 'bg-blue-500 text-white' : 'hover:bg-gray-100'
                }`}
              >
                {black}
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

// Main ChessGamesViewer component
const ChessGamesViewer = () => {
  const [games, setGames] = useState([]);
  const [selectedGame, setSelectedGame] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [onlyDated, setOnlyDated] = useState(false);
  const [moveIndex, setMoveIndex] = useState(0);
  const [game, setGame] = useState(new Chess());
  const [moves, setMoves] = useState([]);
  const moveListRef = useRef(null);
  const activeItemRef = useRef(null);

  // Initialize game service
  const gameService = new GameService();

  // Fetch games with filters
  const fetchGames = useCallback(async () => {
    if (!selectedPlayer) {
      setGames([]);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const data = await gameService.getPlayerGames(selectedPlayer, {
        startDate: dateRange.start,
        endDate: dateRange.end,
        onlyDated,
      });

      setGames(data);
    } catch (error) {
      console.error('Error fetching games:', error);
      setError(error.message || 'Failed to fetch games. Please try again.');
      setGames([]);
    } finally {
      setIsLoading(false);
    }
  }, [selectedPlayer, dateRange, onlyDated]);

  // Fetch games when filters change
  useEffect(() => {
    fetchGames();
  }, [fetchGames]);

  // Utility functions for game management
  const generateSANMoves = useCallback((uciMoves) => {
    if (!uciMoves) return [];
    
    try {
      const tempGame = new Chess();
      const movesList = uciMoves.split(' ');
      const sanMoves = [];
      
      for (const uciMove of movesList) {
        // Parse UCI move format (e.g., "e2e4" to {from: "e2", to: "e4"})
        const from = uciMove.slice(0, 2);
        const to = uciMove.slice(2, 4);
        const promotion = uciMove[4];
        
        // Make move using chess.js move function with explicit from/to
        const move = tempGame.move({
          from: from,
          to: to,
          promotion: promotion
        });
        
        if (move) {
          sanMoves.push(move.san);
        } else {
          console.error('Invalid move:', uciMove);
          return [];  // Return empty array on invalid move
        }
      }
      
      return sanMoves;
    } catch (err) {
      console.error('Error generating SAN moves:', err);
      return [];
    }
  }, []);

  // Handle game selection
  const handleGameSelect = useCallback((selectedGame) => {
    try {
      setSelectedGame(selectedGame);
      setMoveIndex(0);
      
      // Create new game instance
      const newGame = new Chess();
      setGame(newGame);
      
      // Split moves and set them
      const moves = selectedGame.moves.split(' ');
      setMoves(moves);
      
      // Reset the board position
      newGame.reset();
    } catch (err) {
      console.error('Error selecting game:', err);
      setError('Failed to load game moves. Please try another game.');
    }
  }, []);

  // Event handlers
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
        setMoveIndex(prev => Math.min(moves.length, prev + 1));
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedGame, moves.length]);

  const handleSearch = useCallback((e) => {
    e.preventDefault();
    fetchGames();
  }, [fetchGames]);

  const handlePlayerSelect = useCallback((player) => {
    if (!player) {
      setSelectedPlayer('');
      setGames([]);
      return;
    }
    setSelectedPlayer(player.name || player);
  }, []);

  const handleMoveSelect = useCallback((index) => {
    setMoveIndex(index);
  }, []);

  const handleOnlyDatedChange = useCallback((checked) => {
    setOnlyDated(checked);
  }, []);

  // Effect for move playback
  useEffect(() => {
    if (!selectedGame || !moves.length) return;
    
    try {
      // Reset the game and replay moves up to current index
      const newGame = new Chess();
      
      // Get moves up to current index and replay them
      const currentMoves = moves.slice(0, moveIndex);
      
      // Apply each move
      for (const move of currentMoves) {
        newGame.move(move);
      }
      
      setGame(newGame);
    } catch (err) {
      console.error('Error updating game position:', err);
    }
  }, [selectedGame, moveIndex, moves]);

  return (
    <div className="container mx-auto p-6">
      <div className="max-w-7xl mx-auto bg-white p-6 rounded-lg shadow-lg">
        <h1 className="text-2xl font-bold mb-6">Chess Games Explorer</h1>
        
        <GameFilters
          onPlayerSelect={handlePlayerSelect}
          dateRange={dateRange}
          onDateChange={handleDateChange}
          onSearch={handleSearch}
          onlyDated={onlyDated}
          setOnlyDated={handleOnlyDatedChange}
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
                    position={game.fen()} 
                    boardWidth={480}
                    arePiecesDraggable={false}
                  />
                  <GameControls
                    moveIndex={moveIndex}
                    totalMoves={moves.length}
                    onMoveChange={setMoveIndex}
                    disabled={!selectedGame}
                  />
                  <GameDetails game={selectedGame} />
                </div>

                <div className="xl:flex-1">
                  <div className="sticky top-0">
                    <h3 className="font-medium mb-2">Moves</h3>
                    <MovesList
                      moves={moves}
                      moveIndex={moveIndex}
                      onMoveSelect={handleMoveSelect}
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
};

export default ChessGamesViewer;
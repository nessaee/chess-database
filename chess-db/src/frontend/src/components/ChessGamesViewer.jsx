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
  const [searchQuery, setSearchQuery] = useState('');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [currentMoves, setCurrentMoves] = useState([]);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  const formatGameDate = useCallback((dateStr) => {
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
  }, []);

  const handleDateChange = useCallback((type, value) => {
    const date = new Date(value);
    if (isNaN(date.getTime())) {
      console.warn('Invalid date selected');
      return;
    }
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
        const isWhite = tempChess.turn() === 'b'; // After move, turn has changed
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

  const handleGameSelect = useCallback((game) => {
    setSelectedGame(game);
    setMoveIndex(0);
    setChess(new Chess());
    setCurrentMoves(generateSANMoves(game.moves));
  }, [generateSANMoves]);

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

  const renderMoveList = () => {
    if (!currentMoves.length) return null;

    const moveRows = [];
    for (let i = 0; i < currentMoves.length; i += 2) {
      const whiteMove = currentMoves[i];
      const blackMove = currentMoves[i + 1];
      moveRows.push(
        <div 
          key={i} 
          className="grid grid-cols-12 gap-1 hover:bg-gray-50 text-sm"
        >
          <div className="col-span-2 text-gray-500 pl-2">
            {whiteMove.moveNumber}.
          </div>
          <div 
            className={`col-span-5 px-2 py-1 cursor-pointer rounded ${
              i === moveIndex - 1 ? 'bg-blue-100' : ''
            }`}
            onClick={() => setMoveIndex(i + 1)}
          >
            {whiteMove.san}
          </div>
          {blackMove && (
            <div 
              className={`col-span-5 px-2 py-1 cursor-pointer rounded ${
                i + 1 === moveIndex - 1 ? 'bg-blue-100' : ''
              }`}
              onClick={() => setMoveIndex(i + 2)}
            >
              {blackMove.san}
            </div>
          )}
        </div>
      );
    }

    return (
      <div className="bg-white rounded-lg border h-[320px] overflow-y-auto">
        <div className="sticky top-0 bg-gray-50 border-b grid grid-cols-12 gap-1 text-sm font-medium p-2">
          <div className="col-span-2">#</div>
          <div className="col-span-5">White</div>
          <div className="col-span-5">Black</div>
        </div>
        <div className="p-2">
          {moveRows}
        </div>
      </div>
    );
  };

  const renderGameControls = () => (
    <div className="flex items-center justify-between bg-white border rounded-lg p-2 mb-4">
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
      <div className="text-sm text-gray-600 font-medium">
        {selectedGame ? `Move ${moveIndex} of ${currentMoves.length}` : '-'}
      </div>
      <button
        onClick={() => setMoveIndex(prev => prev + 1)}
        disabled={!selectedGame || moveIndex >= currentMoves.length}
        className="p-2 rounded hover:bg-gray-100 disabled:opacity-50"
      >
        <ChevronRight className="h-5 w-5" />
      </button>
      <button
        onClick={() => setMoveIndex(currentMoves.length)}
        disabled={!selectedGame || moveIndex >= currentMoves.length}
        className="p-2 rounded hover:bg-gray-100 disabled:opacity-50"
      >
        <SkipForward className="h-5 w-5" />
      </button>
    </div>
  );

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
        {/* ... [Previous JSX for filters remains the same] */}
        
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
                  {games.map(game => (
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
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Board and Analysis Section */}
          <div className="lg:w-3/4">
            <h2 className="text-xl font-semibold mb-4">Game Viewer</h2>
            {selectedGame ? (
              <div className="flex flex-col xl:flex-row gap-6">
                {/* Board and Controls */}
                <div className="xl:w-[480px]">
                  <Chessboard 
                    position={chess.fen()} 
                    boardWidth={480}
                    arePiecesDraggable={false}
                  />
                  {renderGameControls()}
                  <div className="bg-white border rounded-lg p-4">
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
                        <div className="font-medium">{formatGameDate(selectedGame.date)}</div>
                      </div>
                      <div>
                        <div className="text-gray-600">Result</div>
                        <div className="font-medium">{selectedGame.result}</div>
                      </div>
                      <div>
                        <div className="text-gray-600">ECO</div>
                        <div className="font-medium">{selectedGame.eco}</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Moves List */}
                <div className="xl:flex-1">
                  <div className="sticky top-0">
                    <h3 className="font-medium mb-2">Moves</h3>
                    {renderMoveList()}
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
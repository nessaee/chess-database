import React, { useState, useRef, useEffect } from 'react';
import { Search } from 'lucide-react';
import { AnalysisService } from '../../services/AnalysisService';

const analysisService = new AnalysisService();

/**
 * Analysis Interface Component
 * Provides controls for filtering and analyzing chess data
 */
export function AnalysisInterface({
  timeRange,
  dateRange,
  minGames,
  onTimeRangeChange,
  onDateRangeChange,
  onPlayerSearch,
  onMinGamesChange,
  playerName
}) {
  const [searchTerm, setSearchTerm] = useState(playerName || '');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const suggestionsRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const searchPlayers = async () => {
      if (!searchTerm.trim()) {
        setSuggestions([]);
        return;
      }

      try {
        setIsLoading(true);
        const results = await analysisService.searchPlayers(searchTerm);
        setSuggestions(results);
      } catch (error) {
        console.error('Error searching players:', error);
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    };

    const timeoutId = setTimeout(searchPlayers, 300);
    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (selectedPlayer) {
      onPlayerSearch(selectedPlayer);
    } else if (searchTerm.trim()) {
      // If no player is selected but there's a search term,
      // use the first suggestion if available
      const firstMatch = suggestions[0];
      if (firstMatch) {
        setSelectedPlayer(firstMatch);
        onPlayerSearch(firstMatch);
      }
    }
    setShowSuggestions(false);
  };

  const handleSuggestionClick = (player) => {
    setSearchTerm(player.name);
    setSelectedPlayer(player);
    onPlayerSearch(player);
    setShowSuggestions(false);
  };

  // Update search term when playerName prop changes
  useEffect(() => {
    if (playerName && playerName !== searchTerm) {
      setSearchTerm(playerName);
    }
  }, [playerName]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Player Search */}
        <div className="md:col-span-2">
          <div className="relative" ref={suggestionsRef}>
            <form onSubmit={handleSearchSubmit} className="flex gap-2">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setSelectedPlayer(null);
                    setShowSuggestions(true);
                  }}
                  onFocus={() => setShowSuggestions(true)}
                  placeholder="Search player (e.g., Nakamura,Hi)"
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
                {isLoading && (
                  <div className="absolute right-3 top-2.5">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
                  </div>
                )}
              </div>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Search
              </button>
            </form>

            {/* Suggestions Dropdown */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto">
                {suggestions.map((player) => (
                  <button
                    key={player.id}
                    onClick={() => handleSuggestionClick(player)}
                    className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:outline-none focus:bg-gray-100"
                  >
                    <span className="font-medium">{player.name}</span>
                    {player.elo && (
                      <span className="text-sm text-gray-500 ml-2">
                        (ELO: {player.elo})
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Time Range */}
        <div>
          <select
            value={timeRange}
            onChange={(e) => onTimeRangeChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
            <option value="all">All Time</option>
          </select>
        </div>

        {/* Minimum Games */}
        <div>
          <div className="flex items-center gap-2">
            <input
              type="number"
              value={minGames}
              onChange={(e) => onMinGamesChange(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              min="1"
              placeholder="Min games"
            />
            <span className="text-sm text-gray-500 whitespace-nowrap">min games</span>
          </div>
        </div>
      </div>

      {/* Date Range */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <input
            type="date"
            value={dateRange?.start || ''}
            onChange={(e) => onDateRangeChange('start', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <input
            type="date"
            value={dateRange?.end || ''}
            onChange={(e) => onDateRangeChange('end', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    </div>
  );
}

export default AnalysisInterface;
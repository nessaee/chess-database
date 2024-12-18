import React, { useState, useEffect, useRef } from 'react';
import { debounce } from 'lodash';
import { Search } from 'lucide-react';
import { PlayerService } from '../services/PlayerService';

const playerService = new PlayerService();

const PlayerSearch = ({ onPlayerSelect, initialValue = '' }) => {
  const [inputValue, setInputValue] = useState(initialValue);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState(null);
  const wrapperRef = useRef(null);

  // Handle clicks outside of the component
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounce the API call
  const fetchSuggestions = useRef(
    debounce(async (searchTerm) => {
      if (!searchTerm || searchTerm.length < 2) {
        setSuggestions([]);
        setLoading(false);
        setError(null);
        return;
      }

      try {
        setLoading(true);
        const results = await playerService.searchPlayers(searchTerm);
        setSuggestions(results);
        setOpen(true);
        setError(null);
      } catch (error) {
        console.error('Error fetching player suggestions:', error);
        setError('Failed to fetch suggestions');
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300)
  ).current;

  const handleInputChange = (e) => {
    const value = e.target.value;
    setInputValue(value);
    fetchSuggestions(value);
  };

  const handleSuggestionClick = (player) => {
    setInputValue(player.name);
    onPlayerSelect(player);
    setOpen(false);
  };

  return (
    <div className="relative" ref={wrapperRef}>
      <div className="relative">
        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => setOpen(true)}
          placeholder="Enter player name (e.g., Nakamura,Hi)"
          className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
        {loading && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
          </div>
        )}
      </div>

      {error && (
        <div className="absolute w-full mt-1 p-2 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {open && suggestions.length > 0 && (
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
                  ({player.elo})
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default PlayerSearch;

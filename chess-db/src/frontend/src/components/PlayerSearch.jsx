import React, { useState, useEffect, useRef } from 'react';
import { debounce } from 'lodash';
import { Search } from 'lucide-react';

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
        const response = await fetch(
          `/players/search?q=${encodeURIComponent(searchTerm)}&limit=10`
        );
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Unknown error occurred' }));
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        setSuggestions(data.map(player => player.name));
        setOpen(true);
      } catch (error) {
        console.error('Error fetching player suggestions:', error);
        setError(error.message || 'Failed to fetch suggestions');
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300)
  ).current;

  useEffect(() => {
    return () => {
      fetchSuggestions.cancel();
    };
  }, [fetchSuggestions]);

  const handleInputChange = (event) => {
    const value = event.target.value;
    setInputValue(value);
    if (value) {
      fetchSuggestions(value);
    } else {
      setSuggestions([]);
      setOpen(false);
      setError(null);
    }
  };

  const handleSelect = (value) => {
    setInputValue(value);
    onPlayerSelect(value);
    setOpen(false);
  };

  return (
    <div ref={wrapperRef} className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => inputValue.length >= 2 && setOpen(true)}
          placeholder="Search by player name"
          className="pl-10 p-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        {loading && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-500 border-t-transparent"></div>
          </div>
        )}
      </div>

      {open && suggestions.length > 0 && (
        <ul className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-60 overflow-auto">
          {suggestions.map((suggestion, index) => (
            <li
              key={index}
              onClick={() => handleSelect(suggestion)}
              className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
            >
              {suggestion}
            </li>
          ))}
        </ul>
      )}

      {open && suggestions.length === 0 && !loading && inputValue.length >= 2 && (
        <div className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg p-4 text-center text-gray-500">
          {error ? error : 'No players found'}
        </div>
      )}

      {inputValue.length < 2 && (
        <p className="mt-1 text-sm text-gray-500">
          Enter at least 2 characters
        </p>
      )}
    </div>
  );
};

export default PlayerSearch;

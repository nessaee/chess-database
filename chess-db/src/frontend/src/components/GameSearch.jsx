import React, { useState } from 'react';
import PlayerSearch from './PlayerSearch';
import { format } from 'date-fns';

const GameSearch = ({ onSearch }) => {
  const [playerName, setPlayerName] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [onlyDated, setOnlyDated] = useState(false);

  const handleSearch = () => {
    onSearch({
      playerName,
      startDate,
      endDate,
      onlyDated,
    });
  };

  const handleDateChange = (setter) => (e) => {
    const value = e.target.value;
    setter(value);
  };

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-white shadow-sm">
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Player Name
        </label>
        <PlayerSearch
          onPlayerSelect={setPlayerName}
          initialValue={playerName}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Start Date
          </label>
          <input
            type="date"
            value={startDate}
            onChange={handleDateChange(setStartDate)}
            className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            End Date
          </label>
          <input
            type="date"
            value={endDate}
            onChange={handleDateChange(setEndDate)}
            className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="onlyDated"
          checked={onlyDated}
          onChange={(e) => setOnlyDated(e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <label
          htmlFor="onlyDated"
          className="text-sm font-medium text-gray-700"
        >
          Show only games with dates
        </label>
      </div>

      <button
        onClick={handleSearch}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        Search Games
      </button>
    </div>
  );
};

export default GameSearch;

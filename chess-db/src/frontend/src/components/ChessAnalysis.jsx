/**
 * ChessAnalysis.jsx
 * Provides visualization and analysis of chess game statistics, particularly move counts.
 * 
 * @module ChessAnalysis
 * @author [Your Name]
 * @requires react
 * @requires recharts
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Label
} from 'recharts';

/**
 * Validates and processes raw move count data
 * @param {Array} data - Raw data from API
 * @returns {Array} - Processed and validated data array
 * @throws {Error} - If data validation fails
 */
const processRawData = (data) => {
  if (!Array.isArray(data)) {
    throw new Error('Invalid data format: Expected array');
  }

  return data
    .filter(item => (
      typeof item.actual_full_moves === 'number' &&
      item.actual_full_moves >= 0
    ))
    .map(item => ({
      actual_full_moves: Number(item.actual_full_moves),
      number_of_games: Number(item.number_of_games),
      avg_bytes: Number(item.avg_bytes),
      results: String(item.results || ''),
      min_stored_count: item.min_stored_count ? Number(item.min_stored_count) : null,
      max_stored_count: item.max_stored_count ? Number(item.max_stored_count) : null,
      avg_stored_count: Number(item.avg_stored_count || 0)
    }))
    .sort((a, b) => a.actual_full_moves - b.actual_full_moves);
};

/**
 * CustomTooltip component for displaying detailed move statistics
 * @component
 */
const CustomTooltip = ({ active, payload }) => {
  // Early return if tooltip shouldn't be displayed
  if (!active || !payload?.length) return null;

  const data = payload[0].payload;
  
  return (
    <div className="bg-white p-4 border rounded shadow-lg">
      <h4 className="font-semibold mb-2">Game Statistics</h4>
      <div className="space-y-1 text-sm">
        <p>Move Count: {data.actual_full_moves}</p>
        <p>Games: {data.number_of_games.toLocaleString()}</p>
        <p>Average Size: {data.avg_bytes.toFixed(2)} bytes</p>
        <p>Results: {data.results}</p>
        {data.min_stored_count !== null && (
          <p>
            Move Range: {data.min_stored_count.toLocaleString()} - 
            {data.max_stored_count.toLocaleString()}
          </p>
        )}
      </div>
    </div>
  );
};

/**
 * LoadingState component for displaying loading animation
 * @component
 */
const LoadingState = () => (
  <div className="p-4 bg-white rounded-lg shadow animate-pulse">
    <div className="h-8 w-48 bg-gray-200 rounded mb-4"/>
    <div className="h-[400px] bg-gray-100 rounded flex items-center justify-center">
      <span className="text-gray-500">Loading analysis data...</span>
    </div>
  </div>
);

/**
 * ErrorState component for displaying error messages
 * @component
 */
const ErrorState = ({ error, onRetry }) => (
  <div className="p-4 bg-white rounded-lg shadow">
    <h2 className="text-xl font-bold mb-4 text-red-500">Analysis Error</h2>
    <p className="mb-4 text-gray-700">
      {error?.message || 'An unexpected error occurred'}
    </p>
    <button
      onClick={onRetry}
      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 
                 transition-colors focus:outline-none focus:ring-2 
                 focus:ring-blue-500 focus:ring-offset-2"
      type="button"
    >
      Retry Analysis
    </button>
  </div>
);

/**
 * ChessAnalysis component for visualizing chess game statistics
 * @component
 * @returns {JSX.Element} Rendered analysis component
 */
function ChessAnalysis() {
  // State management for data, loading, and error conditions
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // API configuration with fallback
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  /**
   * Fetches and processes move count data from the API
   * @async
   * @function
   * @throws {Error} When API request fails
   */
  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/analysis/move-counts`);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      const rawData = await response.json();
      const processedData = processRawData(rawData);
      setData(processedData);
    } catch (err) {
      console.error('Analysis data fetch error:', err);
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Conditional rendering based on state
  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} onRetry={fetchData} />;
  if (!data.length) return (
    <div className="p-4 bg-white rounded-lg shadow">
      <p className="text-gray-500">No analysis data available</p>
    </div>
  );

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h2 className="text-xl font-bold mb-4">Move Count Distribution</h2>
      <div className="h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 20, right: 30, left: 40, bottom: 20 }}
          >
            <CartesianGrid 
              strokeDasharray="3 3" 
              strokeOpacity={0.1}
              vertical={false}
            />
            <XAxis
              dataKey="actual_full_moves"
              tick={{ fontSize: 12 }}
            >
              <Label
                value="Number of Moves"
                position="bottom"
                offset={-10}
              />
            </XAxis>
            <YAxis tick={{ fontSize: 12 }}>
              <Label
                value="Number of Games"
                angle={-90}
                position="insideLeft"
                offset={-10}
              />
            </YAxis>
            <Tooltip 
              content={<CustomTooltip />}
              cursor={{ fillOpacity: 0.1 }}
            />
            <Bar
              dataKey="number_of_games"
              fill="#8884d8"
              radius={[4, 4, 0, 0]}
              className="hover:opacity-80 transition-opacity"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default ChessAnalysis;
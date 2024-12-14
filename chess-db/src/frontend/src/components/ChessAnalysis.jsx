import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts';
import { AlertCircle, Calendar, Search } from 'lucide-react';

// Custom tooltip for move count visualization
const MoveCountTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;

  const data = payload[0].payload;
  return (
    <div className="bg-white p-4 border rounded shadow-lg">
      <h4 className="font-semibold mb-2">Move Count Analysis</h4>
      <div className="space-y-1 text-sm">
        <p>Moves: {data.actual_full_moves}</p>
        <p>Games: {data.number_of_games.toLocaleString()}</p>
        <p>Average Size: {data.avg_bytes.toFixed(1)} bytes</p>
        {data.avg_stored_count && (
          <p>Average Stored Count: {data.avg_stored_count.toFixed(1)}</p>
        )}
        <div className="mt-2 text-xs text-gray-500">
          <p>Results: {data.results}</p>
        </div>
      </div>
    </div>
  );
};

// Custom tooltip for performance visualization
const PerformanceTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;

  const data = payload[0].payload;
  return (
    <div className="bg-white p-4 border rounded shadow-lg">
      <h4 className="font-semibold mb-2">{data.time_period}</h4>
      <div className="space-y-1 text-sm">
        <p>Games Played: {data.games_played.toLocaleString()}</p>
        <p>Win Rate: {data.win_rate.toFixed(1)}%</p>
        <p>Average Moves: {data.avg_moves.toFixed(1)}</p>
        <div className="mt-2 border-t pt-2">
          <p>White Games: {data.white_games}</p>
          <p>Black Games: {data.black_games}</p>
          {data.elo_rating && <p>ELO Rating: {data.elo_rating}</p>}
        </div>
      </div>
    </div>
  );
};

// Loading state component
const LoadingState = () => (
  <div className="p-4 bg-white rounded-lg shadow animate-pulse">
    <div className="h-8 w-48 bg-gray-200 rounded mb-4"/>
    <div className="h-[400px] bg-gray-100 rounded flex items-center justify-center">
      <span className="text-gray-500">Loading analysis data...</span>
    </div>
  </div>
);

// Error state component
/**
 * ErrorState component for displaying error messages with optional retry functionality
 * @param {Object} props - Component props
 * @param {Error} props.error - Error object containing message and details
 * @param {Function} props.onRetry - Optional callback function to retry the operation
 */
const ErrorState = ({ error, onRetry }) => (
  <div className="p-6 bg-white rounded-lg shadow-lg border border-red-100">
    <div className="flex items-start space-x-4">
      <div className="flex-shrink-0">
        <AlertCircle className="h-6 w-6 text-red-500" />
      </div>
      <div className="flex-1 min-w-0">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Analysis Error
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          {error?.message || 'An unexpected error occurred while analyzing data'}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center px-4 py-2 bg-red-100 text-red-700 
                     rounded-md hover:bg-red-200 focus:outline-none focus:ring-2 
                     focus:ring-red-500 focus:ring-offset-2 transition-colors
                     text-sm font-medium"
          >
            Retry Analysis
          </button>
        )}
      </div>
    </div>
  </div>
);

// Move distribution visualization
const MoveDistributionChart = ({ data }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <h2 className="text-xl font-bold mb-4">Move Count Distribution</h2>
    <div className="h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 40, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" opacity={0.1} vertical={false} />
          <XAxis 
            dataKey="actual_full_moves"
            label={{ value: 'Number of Moves', position: 'bottom', offset: -10 }}
          />
          <YAxis 
            label={{ 
              value: 'Number of Games', 
              angle: -90, 
              position: 'insideLeft',
              offset: -10 
            }}
          />
          <Tooltip content={<MoveCountTooltip />} />
          <Bar
            dataKey="number_of_games"
            fill="#8884d8"
            name="Games"
            radius={[4, 4, 0, 0]}
            className="hover:opacity-80 transition-opacity"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  </div>
);

// Player performance timeline
const PerformanceTimeline = ({ data, title }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <h2 className="text-xl font-bold mb-4">{title || 'Performance Timeline'}</h2>
    <div className="h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 20, right: 30, left: 40, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
          <XAxis 
            dataKey="time_period"
            label={{ value: 'Time Period', position: 'bottom', offset: -10 }}
          />
          <YAxis 
            yAxisId="rate"
            label={{ value: 'Win Rate (%)', angle: -90, position: 'insideLeft', offset: 10 }}
          />
          <YAxis 
            yAxisId="games"
            orientation="right"
            label={{ value: 'Games Played', angle: 90, position: 'insideRight', offset: 10 }}
          />
          <Tooltip content={<PerformanceTooltip />} />
          <Legend />
          <Line
            type="monotone"
            dataKey="win_rate"
            stroke="#10B981"
            yAxisId="rate"
            name="Win Rate"
          />
          <Line
            type="monotone"
            dataKey="games_played"
            stroke="#6366F1"
            yAxisId="games"
            name="Games Played"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>
);

// Main analysis component
export default function ChessAnalysis() {
  // State management
  const [moveData, setMoveData] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [playerId, setPlayerId] = useState(null);
  const [timeRange, setTimeRange] = useState('monthly');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  // Fetch move count distribution data
  const fetchMoveData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/analysis/move-counts`);
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      
      // Process and validate the data
      const processedData = data
        .map(item => ({
          ...item,
          actual_full_moves: Number(item.actual_full_moves),
          number_of_games: Number(item.number_of_games),
          avg_bytes: Number(item.avg_bytes),
          avg_stored_count: Number(item.avg_stored_count)
        }))
        .filter(item => (
          !isNaN(item.actual_full_moves) &&
          !isNaN(item.number_of_games) &&
          item.actual_full_moves >= 0 &&
          item.number_of_games > 0
        ))
        .sort((a, b) => a.actual_full_moves - b.actual_full_moves);

      setMoveData(processedData);
    } catch (err) {
      setError(err);
      console.error('Analysis data fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  // Fetch player performance data if player ID is available
  const fetchPerformanceData = useCallback(async () => {
    if (!playerId) return;

    try {
      setIsLoading(true);
      setError(null);

      // Build query parameters
      const params = new URLSearchParams({
        time_range: timeRange,
        ...(dateRange.start && { start_date: dateRange.start }),
        ...(dateRange.end && { end_date: dateRange.end })
      });

      const response = await fetch(
        `${API_URL}/players/${playerId}/performance?${params}`
      );

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      setPerformanceData(data);
    } catch (err) {
      setError(err);
      console.error('Performance data fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL, playerId, timeRange, dateRange]);

  // Initial data fetch
  useEffect(() => {
    fetchMoveData();
  }, [fetchMoveData]);

  useEffect(() => {
    if (playerId) {
      fetchPerformanceData();
    }
  }, [fetchPerformanceData, playerId]);

  // Handle date range changes
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

  // Render loading state
  if (isLoading) {
    return <LoadingState />;
  }

  // Render error state
  if (error) {
    return <ErrorState error={error} onRetry={fetchMoveData} />;
  }

  // Render main analysis view
  return (
    <div className="space-y-6">
      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Games Analyzed</h3>
          <p className="mt-1 text-2xl font-semibold text-gray-900">
            {moveData.reduce((sum, d) => sum + d.number_of_games, 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Average Move Count</h3>
          <p className="mt-1 text-2xl font-semibold text-gray-900">
            {(moveData.reduce((sum, d) => sum + d.actual_full_moves * d.number_of_games, 0) / 
              moveData.reduce((sum, d) => sum + d.number_of_games, 0)).toFixed(1)}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Most Common Length</h3>
          <p className="mt-1 text-2xl font-semibold text-gray-900">
            {moveData.reduce((max, d) => d.number_of_games > max.number_of_games ? d : max).actual_full_moves} moves
          </p>
        </div>
      </div>

      {/* Move Distribution Chart */}
      <MoveDistributionChart data={moveData} />

      {/* Player Performance Timeline (if player data is available) */}
      {performanceData.length > 0 && (
        <PerformanceTimeline 
          data={performanceData}
          title="Player Performance Timeline"
        />
      )}
    </div>
  );
}
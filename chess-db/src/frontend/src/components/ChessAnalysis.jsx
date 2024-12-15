import React, { useState, useEffect, useCallback } from 'react';
import { Calendar, Search } from 'lucide-react';
import { MoveDistributionChart, PerformanceTimeline } from './charts/ChessCharts';
import { LoadingState, ErrorState } from './states/LoadingStates';

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
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${response.status}`);
      }

      const data = await response.json();
      
      // Process and validate the data according to MoveCountStats model
      const processedData = data
        .filter(item => item && typeof item === 'object')
        .map(item => ({
          actual_full_moves: Number(item.actual_full_moves),
          number_of_games: Number(item.number_of_games),
          avg_bytes: Number(item.avg_bytes),
          results: String(item.results),
          min_stored_count: item.min_stored_count ? Number(item.min_stored_count) : null,
          max_stored_count: item.max_stored_count ? Number(item.max_stored_count) : null,
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

      // Build query parameters according to PlayerPerformanceResponse model
      const params = new URLSearchParams({
        time_range: timeRange,
        ...(dateRange.start && { start_date: dateRange.start }),
        ...(dateRange.end && { end_date: dateRange.end })
      });

      const response = await fetch(
        `${API_URL}/players/${playerId}/performance?${params}`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${response.status}`);
      }

      const data = await response.json();
      
      // Process and validate performance data
      const processedData = data
        .filter(item => item && typeof item === 'object')
        .map(item => ({
          time_period: String(item.time_period),
          games_played: Number(item.games_played),
          wins: Number(item.wins),
          losses: Number(item.losses),
          draws: Number(item.draws),
          win_rate: Number(item.win_rate),
          avg_moves: Number(item.avg_moves),
          white_games: Number(item.white_games),
          black_games: Number(item.black_games),
          elo_rating: item.elo_rating ? Number(item.elo_rating) : null
        }))
        .filter(item => (
          !isNaN(item.games_played) &&
          !isNaN(item.win_rate) &&
          item.games_played > 0 &&
          item.win_rate >= 0 &&
          item.win_rate <= 100
        ))
        .sort((a, b) => new Date(a.time_period) - new Date(b.time_period));

      setPerformanceData(processedData);
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

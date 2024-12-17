import React, { useState, useEffect } from 'react';
import { MoveDistributionChart } from './charts/ChessCharts';
import { LoadingState, ErrorState } from './states/LoadingStates';
import AnalysisInterface from './analysis/AnalysisInterface';
import DatabaseMetricsView from './analysis/DatabaseMetricsView';
import PlayerAnalysisView from './analysis/PlayerAnalysisView';
import PlayerSearch from './PlayerSearch';
import { AnalysisService } from '../services/AnalysisService';
import { PlayerService } from '../services/PlayerService';

/**
 * Enhanced Chess Analysis Component providing comprehensive chess game analysis
 * including general statistics, openings, player performance, and database metrics.
 * 
 * @component
 * @returns {JSX.Element} Rendered analysis interface
 */

export default function ChessAnalysis() {
  // View state management
  const [activeView, setActiveView] = useState('general');
  
  // Data state management
  const [moveData, setMoveData] = useState([]);
  const [performanceData, setPerformanceData] = useState(null);
  const [openingAnalysis, setOpeningAnalysis] = useState(null);
  const [dbMetrics, setDbMetrics] = useState(null);
  const [playerName, setPlayerName] = useState('');
  const [playerId, setPlayerId] = useState(null);
  
  // UI state management
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('monthly');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [minGames, setMinGames] = useState(20);

  // Initialize services
  const analysisService = new AnalysisService();
  const playerService = new PlayerService();

  // Data fetching effects
  useEffect(() => {
    const fetchAnalysisData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const [moveDistribution, metrics] = await Promise.all([
          analysisService.getMoveCountDistribution(),
          analysisService.getDatabaseMetrics()
        ]);
        setMoveData(moveDistribution);
        setDbMetrics(metrics);
      } catch (error) {
        console.error('Error fetching analysis data:', error);
        setError(error.message || 'Failed to fetch analysis data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalysisData();
  }, []);

  useEffect(() => {
    const fetchPlayerData = async () => {
      if (!playerId) return;

      try {
        setIsLoading(true);
        setError(null);

        const [performance, openings] = await Promise.all([
          playerService.getPlayerPerformance(playerId, {
            timeRange,
            startDate: dateRange?.start,
            endDate: dateRange?.end
          }),
          analysisService.getPlayerOpeningAnalysis(playerId, {
            minGames,
            startDate: dateRange?.start,
            endDate: dateRange?.end
          })
        ]);
        
        setPerformanceData(performance);
        setOpeningAnalysis(openings);
      } catch (error) {
        console.error('Error fetching player data:', error);
        setError(error.message || 'Failed to fetch player data');
        setPerformanceData(null);
        setOpeningAnalysis(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPlayerData();
  }, [playerId, timeRange, dateRange, minGames]);

  const handlePlayerSearch = (player) => {
    if (!player || !player.id) {
      setError('Invalid player selection');
      return;
    }

    setPlayerId(player.id);
    setPlayerName(player.name);
    setError(null);
  };

  const handleDateChange = (type, value) => {
    setDateRange(prev => ({
      ...prev,
      [type]: value
    }));
  };

  // Loading state handler
  if (isLoading) {
    return <LoadingState message={`Loading ${activeView} analysis data...`} />;
  }

  // Error state handler
  if (error) {
    return (
      <ErrorState
        error={error}
        onRetry={() => {
          setError(null);
          if (playerId) {
            handlePlayerSearch({ id: playerId, name: playerName });
          }
        }}
      />
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-4">Chess Analysis Dashboard</h1>
      <p className="text-gray-600 mb-8">
        Comprehensive analysis of chess games, openings, player performance, and database metrics
      </p>

      {/* Navigation Tabs */}
      <div className="flex space-x-4 mb-8">
        <button
          onClick={() => setActiveView('general')}
          className={`px-4 py-2 rounded ${
            activeView === 'general'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          General Statistics
        </button>
        <button
          onClick={() => setActiveView('player')}
          className={`px-4 py-2 rounded ${
            activeView === 'player'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Player Analysis
        </button>
        <button
          onClick={() => setActiveView('database')}
          className={`px-4 py-2 rounded ${
            activeView === 'database'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Database Metrics
        </button>
      </div>

      {/* Analysis Interface */}
      <AnalysisInterface
        timeRange={timeRange}
        dateRange={dateRange}
        minGames={minGames}
        onTimeRangeChange={setTimeRange}
        onDateRangeChange={handleDateChange}
        onMinGamesChange={setMinGames}
        onPlayerSearch={handlePlayerSearch}
        playerName={playerName}
      />

      {/* View Content */}
      <div className="mt-8">
        {activeView === 'general' && (
          <div className="space-y-8">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4">Move Distribution</h2>
              <MoveDistributionChart data={moveData} />
            </div>
          </div>
        )}

        {activeView === 'player' && playerId && playerName && (
          <PlayerAnalysisView
            performanceData={performanceData}
            openingAnalysis={openingAnalysis}
            databaseMetrics={dbMetrics}
          />
        )}

        {activeView === 'database' && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4">Database Metrics</h2>
            <DatabaseMetricsView data={dbMetrics} />
          </div>
        )}
      </div>
    </div>
  );
}
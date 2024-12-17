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
            endDate: dateRange?.end,
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

  const handleDateChange = (type, value) => {
    setDateRange(prev => ({
      ...prev,
      [type]: value
    }));
  };

  return (
    <div className="space-y-6">
      <AnalysisInterface
        timeRange={timeRange}
        dateRange={dateRange}
        minGames={minGames}
        onTimeRangeChange={setTimeRange}
        onDateRangeChange={setDateRange}
        onMinGamesChange={setMinGames}
        onPlayerSearch={(player) => {
          setPlayerName(player.name);
          setPlayerId(player.id);
        }}
        playerName={playerName}
      />

      {isLoading && <LoadingState />}
      {error && <ErrorState message={error} />}
      
      {!isLoading && !error && (
        <div className="space-y-8">
          {activeView === 'general' && (
            <div className="space-y-8">
              <MoveDistributionChart data={moveData} />
              <DatabaseMetricsView data={dbMetrics} />
            </div>
          )}
          
          {activeView === 'player' && playerId && (
            <PlayerAnalysisView
              performanceData={performanceData}
              openingAnalysis={openingAnalysis}
              databaseMetrics={dbMetrics}
            />
          )}
        </div>
      )}
    </div>
  );
}
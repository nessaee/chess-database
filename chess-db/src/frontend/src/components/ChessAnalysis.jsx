import React, { useState, useEffect } from 'react';
import { Tab } from '@headlessui/react';
import { MoveDistributionChart } from './charts/ChessCharts';
import { LoadingState, ErrorState } from './states/LoadingStates';
import AnalysisInterface from './analysis/AnalysisInterface';
import DatabaseMetricsView from './analysis/DatabaseMetricsView';
import PlayerAnalysisView from './analysis/PlayerAnalysisView';
import PlayerSearch from './PlayerSearch';
import { AnalysisService } from '../services/AnalysisService';
import { PlayerService } from '../services/PlayerService';
import { databaseMetricsService } from '../services/DatabaseMetricsService';
import { classNames } from '../utils/classNames';

// Initialize services
const analysisService = new AnalysisService();
const playerService = new PlayerService();

/**
 * Enhanced Chess Analysis Component providing comprehensive chess game analysis
 * including general statistics, opening analysis, and player performance metrics.
 */
const ChessAnalysis = () => {
  // State management
  const [selectedTab, setSelectedTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [analysisData, setAnalysisData] = useState({
    moveDistribution: [],
    playerStats: null,
    openingStats: null,
    databaseMetrics: null
  });
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [timeRange, setTimeRange] = useState('all');
  const [dateRange, setDateRange] = useState({ startDate: null, endDate: null });
  const [minGames, setMinGames] = useState(5);

  // Fetch initial data
  useEffect(() => {
    fetchDatabaseMetrics();
  }, []);

  // Fetch database metrics
  const fetchDatabaseMetrics = async () => {
    try {
      setLoading(true);
      const metrics = await databaseMetricsService.getDatabaseMetrics();
      setAnalysisData(prev => ({ ...prev, databaseMetrics: metrics }));
    } catch (err) {
      console.error('Error fetching database metrics:', err);
      setError('Failed to load database metrics');
    } finally {
      setLoading(false);
    }
  };

  // Handle player selection
  const handlePlayerSelect = async (player) => {
    setSelectedPlayer(player);
    setLoading(true);
    setError(null);

    try {
      // Fetch player statistics
      const [performanceData, openingStats] = await Promise.all([
        playerService.getPlayerPerformance(player.id, { timePeriod: timeRange }),
        playerService.getPlayerOpenings(player.id, {
          minGames,
          startDate: dateRange.startDate,
          endDate: dateRange.endDate
        })
      ]);

      setAnalysisData(prev => ({
        ...prev,
        playerStats: performanceData,
        openingStats
      }));
    } catch (err) {
      setError(err.message || 'Error fetching player analysis');
    } finally {
      setLoading(false);
    }
  };

  // Handle time range change
  const handleTimeRangeChange = async (range) => {
    setTimeRange(range);
    if (selectedPlayer) {
      setLoading(true);
      try {
        const performanceData = await playerService.getPlayerPerformance(selectedPlayer.id, { timePeriod: range });
        setAnalysisData(prev => ({ ...prev, playerStats: performanceData }));
      } catch (err) {
        setError(err.message || 'Error updating time range');
      } finally {
        setLoading(false);
      }
    }
  };

  // Handle date range change
  const handleDateRangeChange = async (range) => {
    setDateRange(range);
    if (selectedPlayer) {
      setLoading(true);
      try {
        const openingStats = await playerService.getPlayerOpenings(selectedPlayer.id, {
          minGames,
          startDate: range.startDate,
          endDate: range.endDate
        });
        setAnalysisData(prev => ({ ...prev, openingStats }));
      } catch (err) {
        setError(err.message || 'Error updating date range');
      } finally {
        setLoading(false);
      }
    }
  };

  // Handle minimum games change
  const handleMinGamesChange = async (games) => {
    setMinGames(games);
    if (selectedPlayer) {
      setLoading(true);
      try {
        const openingStats = await playerService.getPlayerOpenings(selectedPlayer.id, {
          minGames: games,
          startDate: dateRange.startDate,
          endDate: dateRange.endDate
        });
        setAnalysisData(prev => ({ ...prev, openingStats }));
      } catch (err) {
        setError(err.message || 'Error updating minimum games');
      } finally {
        setLoading(false);
      }
    }
  };

  // Handle metrics refresh from child component
  const handleMetricsRefresh = async () => {
    await fetchDatabaseMetrics();
  };

  const tabs = [
    { 
      name: 'Database Overview', 
      content: (
        <DatabaseMetricsView 
          metrics={analysisData.databaseMetrics} 
          onRefresh={handleMetricsRefresh}
        />
      ) 
    },
    {
      name: 'Player Analysis',
      content: (
        <div className="space-y-4">
          <PlayerSearch onPlayerSelect={handlePlayerSelect} />
          {error && <ErrorState message={error} />}
          {loading ? (
            <LoadingState />
          ) : (
            selectedPlayer && (
              <PlayerAnalysisView
                performanceData={analysisData.playerStats}
                openingAnalysis={analysisData.openingStats}
                databaseMetrics={analysisData.databaseMetrics}
              />
            )
          )}
        </div>
      )
    },
    {
      name: 'Analysis Interface',
      content: (
        <AnalysisInterface
          timeRange={timeRange}
          dateRange={dateRange}
          minGames={minGames}
          onTimeRangeChange={handleTimeRangeChange}
          onDateRangeChange={handleDateRangeChange}
          onMinGamesChange={handleMinGamesChange}
        />
      )
    }
  ];

  return (
    <div className="w-full px-2 py-16 sm:px-0">
      <Tab.Group selectedIndex={selectedTab} onChange={setSelectedTab}>
        <Tab.List className="flex space-x-1 rounded-xl bg-blue-900/20 p-1">
          {tabs.map((tab) => (
            <Tab
              key={tab.name}
              className={({ selected }) =>
                classNames(
                  'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                  'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                  selected
                    ? 'bg-white shadow text-blue-700'
                    : 'text-blue-100 hover:bg-white/[0.12] hover:text-white'
                )
              }
            >
              {tab.name}
            </Tab>
          ))}
        </Tab.List>
        <Tab.Panels className="mt-2">
          {tabs.map((tab, idx) => (
            <Tab.Panel
              key={idx}
              className={classNames(
                'rounded-xl bg-white p-3',
                'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2'
              )}
            >
              {tab.content}
            </Tab.Panel>
          ))}
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
};

export default ChessAnalysis;
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
import { classNames } from '../utils/classNames';

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

  // Tab categories
  const categories = [
    { name: 'Player Analysis', key: 'player' },
    { name: 'Opening Explorer', key: 'openings' },
    { name: 'Database Stats', key: 'database' }
  ];

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

  const renderTabContent = (category) => {
    switch (category) {
      case 'player':
        return playerId ? (
          <PlayerAnalysisView
            performanceData={performanceData}
            openingAnalysis={openingAnalysis}
            databaseMetrics={dbMetrics}
          />
        ) : (
          <div className="text-center py-8 text-gray-500">
            Please select a player to view analysis
          </div>
        );
      case 'openings':
        return (
          <div className="text-center py-8 text-gray-500">
            Opening explorer coming soon
          </div>
        );
      case 'database':
        return (
          <div className="space-y-8">
            <MoveDistributionChart data={moveData} />
            <DatabaseMetricsView data={dbMetrics} showDetails={true} />
          </div>   
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <Tab.Group onChange={(index) => setActiveView(categories[index].key)}>
        <Tab.List className="flex space-x-1 rounded-xl bg-gray-100 p-1">
          {categories.map((category) => (
            <Tab
              key={category.key}
              className={({ selected }) =>
                classNames(
                  'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                  'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                  selected
                    ? 'bg-white shadow text-blue-700'
                    : 'text-gray-600 hover:bg-white/[0.12] hover:text-blue-600'
                )
              }
            >
              {category.name}
            </Tab>
          ))}
        </Tab.List>
        <Tab.Panels className="mt-2">
          {categories.map((category) => (
            <Tab.Panel
              key={category.key}
              className={classNames(
                'rounded-xl bg-white p-3',
                'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2'
              )}
            >
              {category.key === 'player' && (
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
              )}
              {isLoading && <LoadingState />}
              {error && <ErrorState message={error} />}
              {!isLoading && !error && renderTabContent(category.key)}
            </Tab.Panel>
          ))}
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
}
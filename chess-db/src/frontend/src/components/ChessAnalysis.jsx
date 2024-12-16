import React, { useState, useEffect } from 'react';
import { MoveDistributionChart } from './charts/ChessCharts';
import { LoadingState, ErrorState } from './states/LoadingStates';
import { AnalysisInterface } from './analysis/AnalysisInterface';
import OpeningAnalysisView from './analysis/OpeningAnalysisView';
import { PlayerMetricsView, DatabaseMetricsView } from './analysis/PlayerDatabaseMetrics';
import { AnalysisService } from '../services/AnalysisService';


/**
 * @typedef {Object} PlayerMetrics
 * @property {number} overallWinRate - Overall win percentage
 * @property {number} totalGames - Total games played
 * @property {number} peakRating - Highest achieved rating
 * @property {Array<Object>} trend - Performance trend data
 * @property {Array<Object>} colorStats - Statistics by piece color
 * @property {Array<Object>} gameLengths - Game length distribution
 */

/**
 * @typedef {Object} DatabaseMetrics
 * @property {number} totalGames - Total games in database
 * @property {number} totalPlayers - Total unique players
 * @property {number} avgResponseTime - Average query response time
 * @property {Array<Object>} growth - Growth metrics over time
 * @property {Array<Object>} performance - Query performance metrics
 */

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
  const [performanceData, setPerformanceData] = useState([]);
  const [openingAnalysis, setOpeningAnalysis] = useState(null);
  const [playerMetrics, setPlayerMetrics] = useState(null);
  const [dbMetrics, setDbMetrics] = useState(null);
  
  // UI state management
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [playerId, setPlayerId] = useState(null);
  const [timeRange, setTimeRange] = useState('monthly');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  // Initialize analysis service
  const analysisService = new AnalysisService();


  const getErrorMessage = (view) => {
      switch (view) {
          case 'player':
              return 'Error loading player performance data';
          case 'database':
              return 'Error loading database metrics';
          case 'openings':
              return 'Error loading opening analysis';
          default:
              return 'Error loading analysis data';
      }
  };

  // Data fetching effects
  useEffect(() => {
    const fetchAnalysisData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const [moveDistribution, metrics] = await Promise.all([
          analysisService.getMoveCountDistribution(),
          analysisService.getDatabaseMetrics(timeRange)
        ]);
        setMoveData(moveDistribution);
        setDbMetrics(metrics);
      } catch (error) {
        console.error('Error fetching analysis data:', error);
        setError(error.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalysisData();
  }, [timeRange]);

  useEffect(() => {
    const fetchPlayerData = async () => {
      if (!playerId) return;

      try {
        setIsLoading(true);
        setError(null);
        const [performance, openings] = await Promise.all([
          analysisService.getPlayerPerformance(playerId, {
            timeRange,
            startDate: dateRange?.start,
            endDate: dateRange?.end
          }),
          analysisService.getPlayerOpeningAnalysis(playerId, {
            minGames: 5,
            startDate: dateRange?.start,
            endDate: dateRange?.end
          })
        ]);
        
        setPerformanceData(performance);
        setOpeningAnalysis(openings);
      } catch (error) {
        console.error('Error fetching player data:', error);
        setError(error.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPlayerData();
  }, [playerId, timeRange, dateRange]);

  /**
   * Handles date range changes
   * @param {string} type - Range type ('start' or 'end')
   * @param {string} value - Selected date value
   */
  const handleDateChange = (type, value) => {
    const date = new Date(value);
    if (isNaN(date.getTime())) {
      console.warn('Invalid date selected');
      return;
    }

    setDateRange(prev => ({
      ...prev,
      [type]: value
    }));
  };

  const handlePlayerSearch = async (query) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // First get the player ID from search
      const searchResults = await analysisService.searchPlayers(query);
      if (!searchResults || searchResults.length === 0) {
        setError('Player not found');
        return;
      }
      
      // Use the first matching player's ID
      const selectedPlayerId = searchResults[0].id;
      setPlayerId(selectedPlayerId);
      
    } catch (error) {
      console.error('Error searching player:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const searchInput = e.target.elements.playerSearch;
    if (searchInput && searchInput.value) {
      handlePlayerSearch(searchInput.value);
    }
  };

  // Loading state handler
  if (isLoading) {
    return (
      <LoadingState
        message={`Loading ${activeView} analysis data...`}
      />
    );
  }

  // Error state handler
  if (error) {
    return (
      <ErrorState
        error={error}
        onRetry={() => {
          if (activeView === 'general' || activeView === 'database') {
            const fetchAnalysisData = async () => {
              try {
                setIsLoading(true);
                setError(null);
                const [moveDistribution, metrics] = await Promise.all([
                  analysisService.getMoveCountDistribution(),
                  analysisService.getDatabaseMetrics(timeRange)
                ]);
                setMoveData(moveDistribution);
                setDbMetrics(metrics);
              } catch (error) {
                console.error('Error fetching analysis data:', error);
                setError(error.message);
              } finally {
                setIsLoading(false);
              }
            };

            fetchAnalysisData();
          } else if (activeView === 'player' || activeView === 'openings') {
            const fetchPlayerData = async () => {
              if (!playerId) return;

              try {
                setIsLoading(true);
                setError(null);
                const [performance, openings] = await Promise.all([
                  analysisService.getPlayerPerformance(playerId, {
                    timeRange,
                    startDate: dateRange?.start,
                    endDate: dateRange?.end
                  }),
                  analysisService.getPlayerOpeningAnalysis(playerId, {
                    minGames: 5,
                    startDate: dateRange?.start,
                    endDate: dateRange?.end
                  })
                ]);
                
                setPerformanceData(performance);
                setOpeningAnalysis(openings);
              } catch (error) {
                console.error('Error fetching player data:', error);
                setError(error.message);
              } finally {
                setIsLoading(false);
              }
            };

            fetchPlayerData();
          }
        }}
      />
    );
  }

  return (
    <div className="space-y-6 p-4">
      {/* Analysis Control Interface */}
      <div className="bg-white rounded-lg shadow-lg p-4">
        <div className="mb-4">
          <h2 className="text-xl font-bold text-gray-900">Chess Analysis Dashboard</h2>
          <p className="text-sm text-gray-500">
            Comprehensive analysis of chess games, openings, player performance, and database metrics
          </p>
        </div>

        {/* View Selection Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8" aria-label="Analysis Views">
            {[
              { id: 'general', label: 'General Statistics' },
              { id: 'openings', label: 'Opening Analysis' },
              { id: 'player', label: 'Player Performance' },
              { id: 'database', label: 'Database Metrics' }
            ].map(view => (
              <button
                key={view.id}
                onClick={() => setActiveView(view.id)}
                className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${activeView === view.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                aria-current={activeView === view.id ? 'page' : undefined}
              >
                {view.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Analysis Interface Controls - Only show for relevant views */}
        {activeView !== 'general' && activeView !== 'database' && (
          <div className="mt-4">
            <AnalysisInterface
              timeRange={timeRange}
              dateRange={dateRange}
              onTimeRangeChange={setTimeRange}
              onDateRangeChange={handleDateChange}
              onPlayerSelect={setPlayerId}
            />
            <form onSubmit={handleSearchSubmit} className="mb-4">
              <input
                type="text"
                name="playerSearch"
                placeholder="Search player (e.g., Nakamura,Hi)"
                className="w-full p-2 border rounded"
              />
            </form>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* Render appropriate view based on active tab */}
        {activeView === 'general' && (
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
                    Math.max(moveData.reduce((sum, d) => sum + d.number_of_games, 0), 1)).toFixed(1)}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <h3 className="text-sm font-medium text-gray-500">Most Common Length</h3>
                <p className="mt-1 text-2xl font-semibold text-gray-900">
                  {moveData.length > 0
                    ? `${moveData.reduce((max, d) => d.number_of_games > max.number_of_games ? d : max).actual_full_moves} moves`
                    : 'N/A'}
                </p>
              </div>
            </div>

            {/* Move Distribution Chart */}
            {moveData.length > 0 && (
              <MoveDistributionChart data={moveData} />
            )}
          </div>
        )}

        {activeView === 'openings' && (
          <>
            {playerId ? (
              <OpeningAnalysisView data={openingAnalysis} />
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-500">
                  Select a player to view opening analysis
                </p>
              </div>
            )}
          </>
        )}

        {activeView === 'player' && (
          <>
            {playerId ? (
              <PlayerMetricsView data={playerMetrics} />
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-500">
                  Select a player to view performance metrics
                </p>
              </div>
            )}
          </>
        )}

        {activeView === 'database' && (
          <DatabaseMetricsView data={dbMetrics} />
        )}
      </div>

      {/* Error Boundary - Catch and display any rendering errors */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 rounded-lg">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Error loading analysis data
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  type="button"
                  onClick={() => {
                    if (activeView === 'general' || activeView === 'database') {
                      const fetchAnalysisData = async () => {
                        try {
                          setIsLoading(true);
                          setError(null);
                          const [moveDistribution, metrics] = await Promise.all([
                            analysisService.getMoveCountDistribution(),
                            analysisService.getDatabaseMetrics(timeRange)
                          ]);
                          setMoveData(moveDistribution);
                          setDbMetrics(metrics);
                        } catch (error) {
                          console.error('Error fetching analysis data:', error);
                          setError(error.message);
                        } finally {
                          setIsLoading(false);
                        }
                      };

                      fetchAnalysisData();
                    } else if (activeView === 'player' || activeView === 'openings') {
                      const fetchPlayerData = async () => {
                        if (!playerId) return;

                        try {
                          setIsLoading(true);
                          setError(null);
                          const [performance, openings] = await Promise.all([
                            analysisService.getPlayerPerformance(playerId, {
                              timeRange,
                              startDate: dateRange?.start,
                              endDate: dateRange?.end
                            }),
                            analysisService.getPlayerOpeningAnalysis(playerId, {
                              minGames: 5,
                              startDate: dateRange?.start,
                              endDate: dateRange?.end
                            })
                          ]);
                          
                          setPerformanceData(performance);
                          setOpeningAnalysis(openings);
                        } catch (error) {
                          console.error('Error fetching player data:', error);
                          setError(error.message);
                        } finally {
                          setIsLoading(false);
                        }
                      };

                      fetchPlayerData();
                    }
                  }}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
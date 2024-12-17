import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { AnalysisService } from '../../services/AnalysisService';

const analysisService = new AnalysisService();

// Helper functions
const getWinRateColor = (rate) => {
  if (rate >= 60) return 'text-emerald-600';
  if (rate >= 50) return 'text-blue-600';
  if (rate >= 40) return 'text-amber-600';
  return 'text-red-600';
};

const formatWinRate = (rate) => `${rate.toFixed(1)}%`;
const formatDrawRate = (rate) => `${rate.toFixed(1)}%`;

/**
 * Analysis Insight component for displaying individual analysis insights
 * @param {Object} props - Component properties
 * @param {Object} props.insight - Analysis insight data
 */
const AnalysisInsight = ({ insight }) => {
  const winRateColor = getWinRateColor(insight.win_rate);
  const drawRate = (insight.draw_count / insight.total_games) * 100;
  const drawRateColor = drawRate >= 30 ? 'text-blue-600' : 'text-gray-600';
  
  return (
    <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="font-medium text-gray-900">{insight.opening_name}</h3>
          <p className="text-gray-600 text-sm mt-1">
            {insight.message}
          </p>
        </div>
        <div className="text-right">
          <span className={`font-semibold ${winRateColor} block`}>
            {formatWinRate(insight.win_rate)} wins
          </span>
          <span className={`text-sm ${drawRateColor} block`}>
            {formatDrawRate(drawRate)} draws
          </span>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Games as White:</span>{' '}
          <span className="font-medium">{insight.games_as_white}</span>
          <span className="text-xs text-gray-500 ml-1">
            ({((insight.games_as_white / insight.total_games) * 100).toFixed(1)}%)
          </span>
        </div>
        <div>
          <span className="text-gray-500">Games as Black:</span>{' '}
          <span className="font-medium">{insight.games_as_black}</span>
          <span className="text-xs text-gray-500 ml-1">
            ({((insight.games_as_black / insight.total_games) * 100).toFixed(1)}%)
          </span>
        </div>
        <div>
          <span className="text-gray-500">Total Games:</span>{' '}
          <span className="font-medium">{insight.total_games}</span>
        </div>
        <div>
          <span className="text-gray-500">Avg Length:</span>{' '}
          <span className="font-medium">{insight.avg_game_length.toFixed(1)} moves</span>
        </div>
      </div>
    </div>
  );
};

/**
 * Opening row component for displaying individual opening statistics
 * @param {Object} props - Component properties
 * @param {Object} props.opening - Opening data
 */
const OpeningRow = ({ opening }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const winRateColor = getWinRateColor(opening.win_rate);
  const drawRate = (opening.draw_count / opening.total_games) * 100;
  const drawRateColor = drawRate >= 30 ? 'text-blue-600' : 'text-gray-600';

  return (
    <>
      <tr className="border-b bg-white hover:bg-gray-50">
        <td className="p-4">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-gray-100 rounded-full"
            aria-label="toggle opening details"
          >
            {isExpanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
        </td>
        <td className="p-4">
          <div className="font-medium text-gray-900">
            {opening.opening_name}
          </div>
          {/* {opening.message && (
            <div className="text-sm text-gray-500 mt-1">
              {opening.message}
            </div>
          )} */}
        </td>
        <td className="p-4 text-right">
          <span className="font-medium">{opening.total_games}</span>
        </td>
        <td className="p-4 text-right">
          <span className="font-medium">{opening.games_as_white}</span>
          <span className="text-xs text-gray-500 ml-1">
            ({((opening.games_as_white / opening.total_games) * 100).toFixed(1)}%)
          </span>
        </td>
        <td className="p-4 text-right">
          <span className="font-medium">{opening.games_as_black}</span>
          <span className="text-xs text-gray-500 ml-1">
            ({((opening.games_as_black / opening.total_games) * 100).toFixed(1)}%)
          </span>
        </td>
        <td className="p-4 text-right">
          <span className={`font-medium ${winRateColor}`}>
            {formatWinRate(opening.win_rate)}
          </span>
        </td>
      </tr>
      {isExpanded && (
        <tr className="border-b">
          <td colSpan="6" className="p-4 bg-gray-50">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <span className="text-gray-500">Wins:</span>{' '}
                <span className="font-medium text-emerald-600">{opening.win_count}</span>
              </div>
              <div>
                <span className="text-gray-500">Draws:</span>{' '}
                <span className={`font-medium ${drawRateColor}`}>{opening.draw_count}</span>
              </div>
              <div>
                <span className="text-gray-500">Losses:</span>{' '}
                <span className="font-medium text-red-600">{opening.loss_count}</span>
              </div>
              <div>
                <span className="text-gray-500">Avg Length:</span>{' '}
                <span className="font-medium">{opening.avg_game_length.toFixed(1)} moves</span>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

/**
 * Opening Analysis Component - Displays comprehensive opening statistics and analysis
 * @param {Object} props - Component properties
 * @param {Object} props.data - Opening analysis data
 */
export default function OpeningAnalysisView({ data = {} }) {
  const [openingData, setOpeningData] = useState({
    analysis: [],
    total_openings: 0,
    avg_game_length: 0,
    total_games: 0,
    total_wins: 0,
    total_draws: 0,
    total_losses: 0,
    most_successful: '',
    most_played: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({
    key: 'total_games',
    direction: 'desc'
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [filterConfig, setFilterConfig] = useState({
    minGames: 0,
    minWinRate: 0,
    colorFilter: 'all' // 'all', 'white', 'black'
  });

  const validateNumericField = (value, min = 0, max = Infinity) => {
    const num = parseInt(value);
    if (isNaN(num)) return min;
    return Math.min(Math.max(num, min), max);
  };

  const handleFilterChange = (field, value) => {
    setFilterConfig(prev => ({
      ...prev,
      [field]: field === 'colorFilter' ? value : validateNumericField(value, 0, field === 'minWinRate' ? 100 : Infinity)
    }));
  };

  useEffect(() => {
    const fetchOpenings = async () => {
      if (!data?.playerId) return;

      try {
        setLoading(true);
        const response = await analysisService.getPlayerOpeningAnalysis(data.playerId);
        setOpeningData(response || {
          analysis: [],
          total_openings: 0,
          avg_game_length: 0,
          total_games: 0,
          total_wins: 0,
          total_draws: 0,
          total_losses: 0,
          most_successful: '',
          most_played: ''
        });
        setError(null);
      } catch (err) {
        console.error('Error fetching opening analysis:', err);
        setError(err.message || 'Failed to fetch opening analysis');
        setOpeningData({
          analysis: [],
          total_openings: 0,
          avg_game_length: 0,
          total_games: 0,
          total_wins: 0,
          total_draws: 0,
          total_losses: 0,
          most_successful: '',
          most_played: ''
        });
      } finally {
        setLoading(false);
      }
    };

    fetchOpenings();
  }, [data?.playerId]);

  const handleSort = (key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  const getSortedOpenings = (openings) => {
    if (!sortConfig.key || !openings) return openings;
    
    return [...openings].sort((a, b) => {
      let aValue = a[sortConfig.key];
      let bValue = b[sortConfig.key];
      
      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }
      
      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  };

  const getFilteredOpenings = (analysis) => {
    if (!analysis) return [];
    
    return analysis.filter(opening => {
      const matchesSearch = opening.opening_name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesMinGames = opening.total_games >= filterConfig.minGames;
      const matchesWinRate = opening.win_rate >= filterConfig.minWinRate;
      const matchesColor = filterConfig.colorFilter === 'all' ||
        (filterConfig.colorFilter === 'white' && opening.games_as_white > 0) ||
        (filterConfig.colorFilter === 'black' && opening.games_as_black > 0);
      
      return matchesSearch && matchesMinGames && matchesWinRate && matchesColor;
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-4 text-red-600">
        Error loading opening analysis: {error}
      </div>
    );
  }

  if (!openingData || !openingData.analysis || openingData.analysis.length === 0) {
    return (
      <div className="text-center p-4 text-gray-600">
        No opening data available
      </div>
    );
  }

  const { total_games, total_wins, total_draws, total_losses, avg_game_length, most_successful, most_played } = openingData;
  const filteredOpenings = getFilteredOpenings(openingData.analysis);
  const sortedOpenings = getSortedOpenings(filteredOpenings);

  return (
    <div className="space-y-6">
      {/* Overall Stats */}
      <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Overall Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <span className="text-gray-500">Total Games:</span>{' '}
            <span className="font-medium">{total_games}</span>
            <div className="space-y-1 mt-2">
              <div className={`text-sm ${getWinRateColor((total_wins / total_games) * 100)}`}>
                W: {total_wins} ({formatWinRate((total_wins / total_games) * 100)})
              </div>
              <div className="text-sm text-blue-600">
                D: {total_draws} ({formatWinRate((total_draws / total_games) * 100)})
              </div>
              <div className="text-sm text-red-600">
                L: {total_losses} ({formatWinRate((total_losses / total_games) * 100)})
              </div>
            </div>
          </div>
          <div>
            <span className="text-gray-500">Total Openings:</span>{' '}
            <span className="font-medium">{openingData.total_openings}</span>
            <div className="text-sm text-gray-500 mt-2">
              Avg. Length: {avg_game_length.toFixed(1)} moves
            </div>
          </div>
          {most_successful && (
            <div>
              <span className="text-gray-500">Most Successful:</span>{' '}
              <div className="font-medium text-sm mt-2 text-emerald-600">{most_successful}</div>
            </div>
          )}
          {most_played && (
            <div>
              <span className="text-gray-500">Most Played:</span>{' '}
              <div className="font-medium text-sm mt-2 text-blue-600">{most_played}</div>
            </div>
          )}
        </div>
      </div>

      {/* Opening Statistics */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Opening Statistics</h2>
        
        {/* Search and Filters */}
        <div className="mb-4 space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search openings..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <select
              value={filterConfig.colorFilter}
              onChange={(e) => handleFilterChange('colorFilter', e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Colors</option>
              <option value="white">As White</option>
              <option value="black">As Black</option>
            </select>
          </div>
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm text-gray-600 mb-1">Minimum Games</label>
              <input
                type="number"
                min="0"
                value={filterConfig.minGames}
                onChange={(e) => handleFilterChange('minGames', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm text-gray-600 mb-1">Minimum Win Rate (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={filterConfig.minWinRate}
                onChange={(e) => handleFilterChange('minWinRate', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="w-8 p-4"></th>
                <th scope="col" className="p-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" onClick={() => handleSort('opening_name')}>
                  Opening
                  {sortConfig.key === 'opening_name' && (
                    <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th scope="col" className="w-24 p-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" onClick={() => handleSort('total_games')}>
                  Games
                  {sortConfig.key === 'total_games' && (
                    <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th scope="col" className="w-28 p-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" onClick={() => handleSort('games_as_white')}>
                  As White
                  {sortConfig.key === 'games_as_white' && (
                    <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th scope="col" className="w-28 p-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" onClick={() => handleSort('games_as_black')}>
                  As Black
                  {sortConfig.key === 'games_as_black' && (
                    <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th scope="col" className="w-24 p-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" onClick={() => handleSort('win_rate')}>
                  Win Rate
                  {sortConfig.key === 'win_rate' && (
                    <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedOpenings.map((opening, index) => (
                <OpeningRow 
                  key={`${opening.opening_name}-${index}`} 
                  opening={opening} 
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
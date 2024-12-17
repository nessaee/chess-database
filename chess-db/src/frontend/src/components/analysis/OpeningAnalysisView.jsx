import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { AnalysisService } from '../../services/AnalysisService';
import { ResponsiveContainer, ComposedChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Bar, Line } from 'recharts';

const analysisService = new AnalysisService();

// Helper functions
const getWinRateColor = (rate) => {
  if (rate === null || rate === undefined) return 'text-gray-600';
  if (rate >= 60) return 'text-emerald-600';
  if (rate >= 50) return 'text-blue-600';
  if (rate >= 40) return 'text-amber-600';
  return 'text-red-600';
};

const formatWinRate = (rate) => {
  if (rate === null || rate === undefined) return '0.0%';
  return `${Number(rate).toFixed(1)}%`;
};

const formatDrawRate = (rate) => {
  if (rate === null || rate === undefined) return '0.0%';
  return `${Number(rate).toFixed(1)}%`;
};

const formatGameLength = (length) => {
  if (length === null || length === undefined) return '0.0';
  return Number(length).toFixed(1);
};

/**
 * Analysis Insight component for displaying individual analysis insights
 * @param {Object} props - Component properties
 * @param {Object} props.insight - Analysis insight data
 */
const AnalysisInsight = ({ insight }) => {
  const winRateColor = getWinRateColor(insight.win_rate);
  const drawRate = insight.total_games > 0 ? (insight.draw_count / insight.total_games) * 100 : 0;
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
          <span className="font-medium">{formatGameLength(insight.avg_game_length)} moves</span>
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
  const drawRate = opening.total_games > 0 ? (opening.draw_count / opening.total_games) * 100 : 0;
  const drawRateColor = drawRate >= 30 ? 'text-blue-600' : 'text-gray-600';

  const renderTrendGraph = () => {
    if (!opening.trend_data || !opening.trend_data.months || !opening.trend_data.games || !opening.trend_data.win_rates) return null;

    // Sort data chronologically
    const sortedIndices = opening.trend_data.months
      .map((_, idx) => idx)
      .sort((a, b) => new Date(opening.trend_data.months[a]) - new Date(opening.trend_data.months[b]));

    const sortedData = {
      months: sortedIndices.map(i => opening.trend_data.months[i]),
      games: sortedIndices.map(i => opening.trend_data.games[i]),
      win_rates: sortedIndices.map(i => opening.trend_data.win_rates[i])
    };

    const maxGames = Math.max(...sortedData.games);
    const height = 400; // Increased height
    const width = Math.min(1600, sortedData.months.length * 60); // Increased width and spacing
    const padding = { top: 20, right: 40, bottom: 40, left: 60 }; // Increased padding
    const graphHeight = (height - padding.top - padding.bottom) / 2;

    // Format dates for better display
    const formatDate = (date) => {
      const d = new Date(date);
      return `${d.toLocaleString('default', { month: 'short' })} ${d.getFullYear()}`;
    };

    return (
      <div className="trend-graph" style={{ marginTop: '1rem' }}>
        <ResponsiveContainer width="100%" height={height}>
          <ComposedChart
            data={sortedData.months.map((month, i) => ({
              month: formatDate(month),
              games: sortedData.games[i],
              winRate: sortedData.win_rates[i]
            }))}
            margin={padding}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="month"
              angle={-45}
              textAnchor="end"
              height={60}
              interval={0}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              yAxisId="left"
              orientation="left"
              domain={[0, maxGames * 1.1]}
              label={{ value: 'Games Played', angle: -90, position: 'insideLeft' }}
              tickFormatter={(value) => Math.round(value)}
              allowDecimals={false}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[0, 100]}
              label={{ value: 'Win Rate (%)', angle: 90, position: 'insideRight' }}
            />
            <Tooltip />
            <Legend verticalAlign="top" height={36} />
            <Bar
              yAxisId="left"
              dataKey="games"
              fill="#8884d8"
              name="Games Played"
              barSize={30}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="winRate"
              stroke="#82ca9d"
              name="Win Rate"
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <>
      <tr 
        className="border-b hover:bg-gray-100 cursor-pointer transition-colors duration-150 ease-in-out" 
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <td className="px-6 py-4 flex items-center space-x-3">
          <div className={`transition-transform duration-200 ${isExpanded ? 'transform rotate-180' : ''}`}>
            <ChevronDown size={20} className="text-gray-500" />
          </div>
          <span className="font-medium text-gray-800">{opening.opening_name}</span>
        </td>
        <td className="px-6 py-4 text-right">
          <span className={`font-semibold ${winRateColor}`}>{opening.win_rate.toFixed(1)}%</span>
        </td>
        <td className="px-6 py-4 text-right font-medium">{opening.total_games}</td>
        <td className="px-6 py-4 text-right">{opening.games_as_white}</td>
        <td className="px-6 py-4 text-right">{opening.games_as_black}</td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan="5" className="px-6 py-6 bg-gray-50">
            <div className="space-y-6">
              <div className="bg-white p-4 rounded-lg shadow-sm">
                <div className="flex justify-between items-center text-lg">
                  <div className="space-x-4">
                    <span className="text-gray-600">Wins: <span className="font-medium text-green-600">{opening.win_count}</span></span>
                    <span className="text-gray-600">Draws: <span className="font-medium text-blue-600">{opening.draw_count}</span></span>
                    <span className="text-gray-600">Losses: <span className="font-medium text-red-600">{opening.loss_count}</span></span>
                  </div>
                  <div className="text-gray-600">
                    Avg. Length: <span className="font-medium text-indigo-600">{Math.round(opening.avg_game_length)} moves</span>
                  </div>
                </div>
              </div>
              {renderTrendGraph(opening)}
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
 * @param {Object} props.data - Opening data
 * @param {Object} props.playerName - Player name
 */
const OpeningAnalysisView = ({ data, playerName }) => {
  const [openingData, setOpeningData] = useState(data || null);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'total_games', direction: 'desc' });

  useEffect(() => {
    // If data is provided directly, use it
    if (data) {
      setOpeningData(data);
      return;
    }

    // Otherwise, fetch data using playerName
    const fetchData = async () => {
      if (!playerName) {
        setError('Player name is required');
        return;
      }

      try {
        const fetchedData = await analysisService.getPlayerOpeningAnalysis(playerName);
        setOpeningData(fetchedData);
      } catch (err) {
        setError(err.message);
      }
    };

    fetchData();
  }, [data, playerName]);

  const sortData = (key) => {
    let direction = 'desc';
    if (sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  const getSortedOpenings = () => {
    if (!openingData?.analysis) return [];
    
    return [...openingData.analysis].sort((a, b) => {
      let aValue = a[sortConfig.key];
      let bValue = b[sortConfig.key];
      
      if (sortConfig.direction === 'asc') {
        return aValue - bValue;
      }
      return bValue - aValue;
    });
  };

  const renderSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) return '↕';
    return sortConfig.direction === 'asc' ? '↑' : '↓';
  };

  if (error) return <div className="text-red-500">Error: {error}</div>;
  if (!openingData) return <div>Loading...</div>;

  return (
    <div className="opening-analysis p-4">
      <div className="overflow-x-auto">
        <table className="min-w-full table-auto">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-4 py-2 text-left">Opening</th>
              <th 
                className="px-4 py-2 text-right cursor-pointer hover:bg-gray-200"
                onClick={() => sortData('win_rate')}
              >
                Win Rate {renderSortIcon('win_rate')}
              </th>
              <th 
                className="px-4 py-2 text-right cursor-pointer hover:bg-gray-200"
                onClick={() => sortData('total_games')}
              >
                Total Games {renderSortIcon('total_games')}
              </th>
              <th 
                className="px-4 py-2 text-right cursor-pointer hover:bg-gray-200"
                onClick={() => sortData('games_as_white')}
              >
                Games as White {renderSortIcon('games_as_white')}
              </th>
              <th 
                className="px-4 py-2 text-right cursor-pointer hover:bg-gray-200"
                onClick={() => sortData('games_as_black')}
              >
                Games as Black {renderSortIcon('games_as_black')}
              </th>
            </tr>
          </thead>
          <tbody>
            {getSortedOpenings().map((opening, index) => (
              <OpeningRow key={index} opening={opening} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OpeningAnalysisView;
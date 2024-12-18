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
  return `${rate.toFixed(1)}%`;
};

const formatDrawRate = (rate) => {
  if (rate === null || rate === undefined) return '0.0%';
  return `${rate.toFixed(1)}%`;
};

const formatGameLength = (length) => {
  if (length === null || length === undefined) return '0.0';
  return Number(length).toFixed(1);
};

// Group data by year and month
const groupDataByPeriod = (data, groupBy) => {
  const groupedData = {};
  
  data.forEach((item, i) => {
    const date = new Date(item.month);
    const key = groupBy === 'yearly' 
      ? date.getFullYear().toString()
      : `${date.toLocaleString('default', { month: 'short' })} ${date.getFullYear()}`;
    
    if (!groupedData[key]) {
      groupedData[key] = {
        month: key,
        games: 0,
        winRate: 0,
        count: 0
      };
    }
    
    groupedData[key].games += item.games;
    groupedData[key].winRate += item.winRate * item.games; // Weight by number of games
    groupedData[key].count += item.games;
  });

  // Calculate weighted averages for win rates
  Object.values(groupedData).forEach(group => {
    group.winRate = group.count > 0 ? group.winRate / group.count : 0;
  });

  return Object.values(groupedData);
};

/**
 * Analysis Insight component for displaying individual analysis insights
 * @param {Object} props - Component properties
 * @param {Object} props.insight - Analysis insight data
 */
const AnalysisInsight = ({ insight }) => {
  const winRateColor = getWinRateColor(insight.win_rate);
  const drawRate = insight.total_games > 0 ? (insight.draw_count / insight.total_games * 100) : 0;
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
 * @param {string} props.timeGrouping - Time grouping option ('monthly' or 'yearly')
 */
const OpeningRow = ({ opening, timeGrouping }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const winRateColor = getWinRateColor(opening.win_rate);
  const drawRate = opening.total_games > 0 ? (opening.draws / opening.total_games * 100) : 0;
  const drawRateColor = drawRate >= 30 ? 'text-blue-600' : 'text-gray-600';

  const renderTrendGraph = () => {
    if (!opening.trend_data || !opening.trend_data.months || !opening.trend_data.games || !opening.trend_data.win_rates) return null;

    // Create initial monthly data
    const monthlyData = opening.trend_data.months.map((month, i) => ({
      month,
      games: opening.trend_data.games[i],
      winRate: opening.trend_data.win_rates[i] // win_rates are already percentages
    }));

    // Group data based on selected time period
    const chartData = groupDataByPeriod(monthlyData, timeGrouping);
    const maxGames = Math.max(...chartData.map(d => d.games));
    const height = 400;
    const padding = { top: 20, right: 40, bottom: 60, left: 60 };

    return (
      <div className="trend-graph" style={{ marginTop: '1rem' }}>
        <ResponsiveContainer width="100%" height={height}>
          <ComposedChart
            data={chartData}
            margin={padding}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="month"
              angle={-90}
              textAnchor="end"
              height={60}
              interval={0}
              tick={{ fontSize: 12 }}
              tickMargin={10}
            />
            <YAxis
              yAxisId="left"
              orientation="left"
              domain={[0, maxGames * 1.1]}
              label={{ value: 'Games Played', angle: -90, position: 'insideLeft' }}
              tickFormatter={(value) => Math.round(value)}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[0, 100]}
              label={{ value: 'Win Rate (%)', angle: 90, position: 'insideRight' }}
              tickFormatter={(value) => Math.round(value)}
            />
            <Tooltip />
            <Legend />
            <Bar
              yAxisId="left"
              dataKey="games"
              fill="#8884d8"
              name="Games Played"
              barSize={timeGrouping === 'yearly' ? 40 : 20}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="winRate"
              stroke="#82ca9d"
              name="Win Rate"
              dot={{ r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    );
  };

  const StatCard = ({ label, value, color = 'text-gray-900', subValue = null }) => (
    <div className="bg-gray-50 rounded-lg p-3 flex flex-col">
      <span className="text-sm text-gray-500">{label}</span>
      <span className={`text-lg font-semibold ${color}`}>{value}</span>
      {subValue && <span className="text-xs text-gray-500 mt-1">{subValue}</span>}
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200 mb-4 hover:border-blue-200 transition-colors">
      <div 
        className="flex flex-col space-y-4"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h3 className="font-medium text-gray-900 text-lg">
                {opening.opening_name}
              </h3>
              <span className="text-gray-500 text-sm px-2 py-0.5 bg-gray-100 rounded-full">
                {opening.eco_code}
              </span>
            </div>
          </div>
          <button className="ml-4 text-gray-400 hover:text-gray-600 transition-colors">
            {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <StatCard
            label="Total Games"
            value={opening.total_games}
            subValue=""
          />
          <StatCard
            label="Games as White"
            value={opening.games_as_white}
            subValue={`${((opening.games_as_white / opening.total_games) * 100).toFixed(1)}% of games`}
          />
          <StatCard
            label="Games as Black"
            value={opening.games_as_black}
            subValue={`${((opening.games_as_black / opening.total_games) * 100).toFixed(1)}% of games`}
          />
          <StatCard
            label="Win Rate"
            value={`${opening.win_rate.toFixed(1)}%`}
            color={winRateColor}
            subValue={`${drawRate.toFixed(1)}% draws`}
          />
          <StatCard
            label="Avg Game Length"
            value={`${formatGameLength(opening.avg_game_length)}`}
            subValue=""
          />
        </div>
      </div>

      {isExpanded && (
        <div className="mt-6 border-t pt-4">
          {opening.complexity_stats?.complexity_score && (
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Complexity Score</span>
                <span className="font-medium text-gray-900">
                  {Number(opening.complexity_stats.complexity_score).toFixed(2)}
                </span>
              </div>
            </div>
          )}
          {renderTrendGraph()}
        </div>
      )}
    </div>
  );
};

/**
 * Opening Analysis View component for displaying comprehensive opening statistics
 * @param {Object} props - Component properties
 * @param {Object} props.data - Opening analysis data
 * @param {string} props.playerName - Player name
 */
const OpeningAnalysisView = ({ data, playerName }) => {
  const [timeGrouping, setTimeGrouping] = useState('monthly');
  const [sortBy, setSortBy] = useState('total_games');
  const [sortDirection, setSortDirection] = useState('desc');

  if (!data) return null;

  const getSortValue = (opening, field) => {
    switch (field) {
      case 'games_as_white':
        return opening.games_as_white || 0;
      case 'games_as_black':
        return opening.games_as_black || 0;
      case 'win_rate':
        return opening.win_rate || 0;
      case 'avg_game_length':
        return opening.avg_game_length || 0;
      case 'total_games':
        return opening.total_games || 0;
      default:
        return 0;
    }
  };

  const sortedAnalysis = [...data.analysis].sort((a, b) => {
    const aValue = getSortValue(a, sortBy);
    const bValue = getSortValue(b, sortBy);
    return sortDirection === 'desc' ? bValue - aValue : aValue - bValue;
  });

  const handleSortChange = (field) => {
    if (sortBy === field) {
      setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setSortDirection('desc');
    }
  };

  const SortButton = ({ field, label }) => (
    <button
      onClick={() => handleSortChange(field)}
      className={`px-3 py-1 text-sm rounded-md border ${
        sortBy === field
          ? 'bg-blue-50 border-blue-200 text-blue-700'
          : 'border-gray-300 text-gray-600 hover:bg-gray-50'
      }`}
    >
      {label}
      {sortBy === field && (
        <span className="ml-1">
          {sortDirection === 'desc' ? '↓' : '↑'}
        </span>
      )}
    </button>
  );

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex flex-col space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">
              Opening Analysis for {playerName}
            </h2>
            <select
              value={timeGrouping}
              onChange={(e) => setTimeGrouping(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="monthly">Monthly View</option>
              <option value="yearly">Yearly View</option>
            </select>
          </div>
          
          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-sm text-gray-600">Sort by:</span>
            <SortButton field="total_games" label="Total Games" />
            <SortButton field="games_as_white" label="Games as White" />
            <SortButton field="games_as_black" label="Games as Black" />
            <SortButton field="win_rate" label="Win Rate" />
            <SortButton field="avg_game_length" label="Avg Game Length" />
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center mt-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{data.total_openings}</div>
            <div className="text-sm text-gray-600">Openings Played</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{data.total_games}</div>
            <div className="text-sm text-gray-600">Total Games</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {formatWinRate(data.total_wins / data.total_games * 100)}
            </div>
            <div className="text-sm text-gray-600">Overall Win Rate</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{formatGameLength(data.avg_game_length)}</div>
            <div className="text-sm text-gray-600">Avg Game Length</div>
          </div>
        </div>
      </div>

      {data.insights && data.insights.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Key Insights</h3>
          {data.insights.map((insight, index) => (
            <AnalysisInsight key={index} insight={insight} />
          ))}
        </div>
      )}

      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900">Opening Statistics</h3>
        <div className="space-y-2">
          {sortedAnalysis.map((opening, index) => (
            <OpeningRow 
              key={index} 
              opening={opening} 
              timeGrouping={timeGrouping}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default OpeningAnalysisView;
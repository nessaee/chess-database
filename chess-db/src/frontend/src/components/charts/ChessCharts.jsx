import React from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts';
import { MoveCountTooltip, PerformanceTooltip } from '../tooltips/ChessTooltips';
import { useMemo } from 'react';
import PropTypes from 'prop-types';

export const MoveDistributionChart = ({ data }) => (
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
            dataKey="move_count"
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
            dataKey="game_count"
            fill="#8884d8"
            name="Games"
            radius={[4, 4, 0, 0]}
            className="hover:opacity-80 transition-opacity"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
    <div className="mt-4 text-sm text-gray-500">
      <p>Distribution of chess games by number of moves. Hover over bars for detailed information.</p>
    </div>
  </div>
);

MoveDistributionChart.propTypes = {
  data: PropTypes.arrayOf(PropTypes.shape({
    move_count: PropTypes.number.isRequired,
    game_count: PropTypes.number.isRequired,
    avg_bytes: PropTypes.number.isRequired
  })).isRequired
};



/**
 * Performance timeline visualization component with enhanced data processing
 * and error handling.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {Array<Object>} props.data - Performance data array
 * @param {string} [props.title] - Optional chart title
 * @param {string} [props.timeRange] - Time range for x-axis formatting
 */
export const PerformanceTimeline = ({ data, title, timeRange = 'monthly' }) => {
  // Process and validate data for visualization
  const processedData = useMemo(() => {
    if (!Array.isArray(data)) return [];
    
    return data
      .map(entry => ({
        timePeriod: entry.timePeriod,
        gamesPlayed: Number(entry.gamesPlayed) || 0,
        winRate: Number(entry.winRate) || 0,
        avgMoves: Number(entry.avgMoves) || 0,
        eloRating: entry.eloRating ? Number(entry.eloRating) : null
      }))
      .sort((a, b) => new Date(a.timePeriod) - new Date(b.timePeriod));
  }, [data]);

  // Format time period based on specified range
  const formatXAxis = (value) => {
    try {
      const date = new Date(value);
      if (isNaN(date.getTime())) return value;

      return timeRange === 'yearly' 
        ? date.getFullYear().toString()
        : date.toLocaleDateString(undefined, { month: 'short', year: 'numeric' });
    } catch (error) {
      console.error('Error formatting date:', error);
      return value;
    }
  };

  // Custom tooltip formatter
  const formatTooltip = (value, name) => {
    switch (name) {
      case 'winRate':
        return `${value.toFixed(1)}%`;
      case 'gamesPlayed':
        return value.toLocaleString();
      case 'eloRating':
        return value ? value.toLocaleString() : 'N/A';
      default:
        return value;
    }
  };

  if (!processedData.length) {
    return (
      <div className="bg-white rounded-lg shadow p-4 text-center text-gray-500">
        No performance data available
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-xl font-bold mb-4">
        {title || 'Performance Timeline'}
      </h2>
      <div className="h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={processedData}
            margin={{ top: 20, right: 30, left: 40, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
            <XAxis 
              dataKey="timePeriod"
              tickFormatter={formatXAxis}
              label={{ 
                value: 'Time Period', 
                position: 'bottom', 
                offset: -10 
              }}
            />
            <YAxis 
              yAxisId="rate"
              domain={[0, 100]}
              label={{ 
                value: 'Win Rate (%)', 
                angle: -90, 
                position: 'insideLeft', 
                offset: 10 
              }}
            />
            <YAxis 
              yAxisId="games"
              orientation="right"
              label={{ 
                value: 'Games Played', 
                angle: 90, 
                position: 'insideRight', 
                offset: 10 
              }}
            />
            <Tooltip 
              formatter={formatTooltip}
              labelFormatter={formatXAxis}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="winRate"
              stroke="#10B981"
              yAxisId="rate"
              name="Win Rate"
              dot={false}
              activeDot={{ r: 6 }}
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="gamesPlayed"
              stroke="#6366F1"
              yAxisId="games"
              name="Games Played"
              dot={false}
              activeDot={{ r: 6 }}
              strokeWidth={2}
            />
            {processedData.some(d => d.eloRating) && (
              <Line
                type="monotone"
                dataKey="eloRating"
                stroke="#EC4899"
                yAxisId="games"
                name="ELO Rating"
                dot={false}
                activeDot={{ r: 6 }}
                strokeWidth={2}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

PerformanceTimeline.propTypes = {
  data: PropTypes.arrayOf(PropTypes.shape({
    timePeriod: PropTypes.string.isRequired,
    gamesPlayed: PropTypes.number.isRequired,
    winRate: PropTypes.number.isRequired,
    avgMoves: PropTypes.number.isRequired,
    eloRating: PropTypes.number
  })).isRequired,
  title: PropTypes.string,
  timeRange: PropTypes.oneOf(['monthly', 'yearly'])
};

PerformanceTimeline.defaultProps = {
  timeRange: 'monthly'
};
import React, { useMemo, useState } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend, Area, ComposedChart
} from 'recharts';
import { Activity, TrendingUp, Award, Clock, Shuffle } from 'lucide-react';
import MetricCard from './shared/MetricCard';

const formatDate = (timePeriod, timeScale) => {
  const date = new Date(timePeriod);
  if (timeScale === 'year') {
    return date.getFullYear().toString();
  }
  return `${date.getFullYear()}-${date.toLocaleDateString('en-US', { month: 'short' })}`;
};

/**
 * Performance trend visualization component
 */
const PerformanceTrendChart = ({ data, timeScale, setTimeScale }) => {
  const [visibleTrends, setVisibleTrends] = useState({
    games: true,
    rating: true,
    winRate: false,
    openingDiversity: false
  });

  // Chart configuration
  const maxGames = Math.max(...data.map(d => d.games_played));
  const gamesPadding = Math.ceil(maxGames * 0.1);
  const minRating = Math.min(...data.map(d => d.rating));
  const maxRating = Math.max(...data.map(d => d.rating));
  const ratingPadding = Math.ceil((maxRating - minRating) * 0.1);

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-medium mb-4">Performance Trend</h3>
      
      <div className="flex gap-4 mb-4">
        {/* Trend toggles */}
        <div className="flex gap-2">
          <button
            onClick={() => setVisibleTrends(prev => ({ ...prev, games: !prev.games }))}
            className={`px-3 py-1 rounded ${
              visibleTrends.games ? 'bg-gray-200 text-gray-800' : 'bg-gray-100 text-gray-500'
            }`}
          >
            Games Played
          </button>
          <button
            onClick={() => setVisibleTrends(prev => ({ ...prev, rating: !prev.rating }))}
            className={`px-3 py-1 rounded ${
              visibleTrends.rating ? 'bg-blue-200 text-blue-800' : 'bg-gray-100 text-gray-500'
            }`}
          >
            Rating
          </button>
          <button
            onClick={() => setVisibleTrends(prev => ({ ...prev, winRate: !prev.winRate }))}
            className={`px-3 py-1 rounded ${
              visibleTrends.winRate ? 'bg-green-200 text-green-800' : 'bg-gray-100 text-gray-500'
            }`}
          >
            Win Rate
          </button>
          <button
            onClick={() => setVisibleTrends(prev => ({ ...prev, openingDiversity: !prev.openingDiversity }))}
            className={`px-3 py-1 rounded ${
              visibleTrends.openingDiversity ? 'bg-purple-200 text-purple-800' : 'bg-gray-100 text-gray-500'
            }`}
          >
            Opening Diversity
          </button>
        </div>

        {/* Time scale toggle */}
        <div className="flex gap-2">
          <button
            onClick={() => setTimeScale('month')}
            className={`px-3 py-1 rounded ${
              timeScale === 'month' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setTimeScale('year')}
            className={`px-3 py-1 rounded ${
              timeScale === 'year' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
            }`}
          >
            Yearly
          </button>
        </div>
      </div>

      <div className="h-[600px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart 
            data={data}
            margin={{ top: 20, right: 140, bottom: 100, left: 80 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="time_period" 
              tickFormatter={(value) => formatDate(value, timeScale)} 
              angle={-45}
              textAnchor="end"
              height={60}
              interval={timeScale === 'year' ? 0 : 6}
              label={{ 
                value: 'Time Period', 
                position: 'bottom',
                offset: 50
              }}
              tick={{
                fontSize: 12,
                dy: 20
              }}
            />
            {/* Games Played Axis (Hidden) */}
            <YAxis 
              yAxisId="games"
              orientation="left"
              domain={[0, maxGames + gamesPadding]}
              axisLine={false}
              tick={false}
              width={30}
            />
            {/* Percentage Axis */}
            <YAxis 
              yAxisId="percentage" 
              orientation="left" 
              domain={[0, 100]}
              label={{ 
                value: 'Percentage', 
                angle: -90, 
                position: 'insideLeft',
                offset: 0
              }}
              tickFormatter={(value) => value}
              tick={{
                fontSize: 12,
                dx: -5
              }}
              width={80}
              minTickGap={5}
              axisLine={{
                strokeWidth: 1
              }}
            />
            {/* Rating Axis */}
            <YAxis 
              yAxisId="right" 
              orientation="right" 
              domain={[minRating - ratingPadding, maxRating + ratingPadding]}
              label={{ 
                value: 'Rating', 
                angle: 90, 
                position: 'insideRight',
                offset: 25
              }}
              tickFormatter={(value) => Math.round(value)}
              tick={{
                fontSize: 12,
                dx: 5
              }}
              width={80}
              minTickGap={5}
              axisLine={{
                strokeWidth: 1
              }}
            />
            
            <Tooltip 
              labelFormatter={(value) => formatDate(value, timeScale)}
              formatter={(value, name) => {
                switch(name) {
                  case 'Win Rate':
                  case 'Opening Diversity':
                    return [`${value}%`, name];
                  case 'Rating':
                    return [Math.round(value), name];
                  case 'Games Played':
                    return [value, name];
                  default:
                    return [value, name];
                }
              }}
            />

            {visibleTrends.games && (
              <Line
                yAxisId="games"
                type="monotone"
                dataKey="games_played"
                name="Games Played"
                stroke="#9CA3AF"
                dot={false}
                strokeWidth={1}
              />
            )}
            {visibleTrends.rating && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="rating"
                name="Rating"
                stroke="#3B82F6"
                dot={false}
                strokeWidth={2}
              />
            )}
            {visibleTrends.winRate && (
              <Line
                yAxisId="percentage"
                type="monotone"
                dataKey="win_rate"
                name="Win Rate"
                stroke="#10B981"
                dot={false}
                strokeWidth={2}
              />
            )}
            {visibleTrends.openingDiversity && (
              <Line
                yAxisId="percentage"
                type="monotone"
                dataKey="opening_diversity"
                name="Opening Diversity"
                stroke="#8B5CF6"
                dot={false}
                strokeWidth={2}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

/**
 * Player Metrics Component - Displays comprehensive player performance analytics
 * @param {Object} props - Component properties
 * @param {Array} props.performanceData - Player performance data array
 */
export default function PlayerMetricsView({ performanceData = [] }) {
  const [timeScale, setTimeScale] = useState('month'); // 'month' or 'year'

  const metrics = useMemo(() => {
    if (!performanceData?.length) return null;

    const latestData = performanceData[performanceData.length - 1];
    const totalGames = performanceData.reduce((sum, month) => sum + month.games_played, 0);
    const weightedWinRate = performanceData.reduce((sum, month) => 
      sum + (month.win_rate * month.games_played), 0) / totalGames;
    const maxRating = Math.max(...performanceData.map(month => month.avg_elo));
    const avgGameLength = performanceData.reduce((sum, month) => 
      sum + (month.avg_game_length * month.games_played), 0) / totalGames;
    const avgOpeningDiversity = performanceData.reduce((sum, month) => 
      sum + (month.opening_diversity * month.games_played), 0) / totalGames;

    return {
      totalGames,
      winRate: weightedWinRate,
      peakRating: maxRating,
      avgGameLength: Math.round(avgGameLength),
      openingDiversity: avgOpeningDiversity * 100
    };
  }, [performanceData]);

  if (!metrics) {
    return <div className="text-gray-500">No performance data available</div>;
  }

  // Group data by year if yearly scale is selected
  const getScaledData = () => {
    if (timeScale === 'year') {
      const yearlyData = {};
      performanceData.forEach(item => {
        const year = new Date(item.time_period).getFullYear();
        if (!yearlyData[year]) {
          yearlyData[year] = {
            time_period: `${year}-01-01`,
            games_played: 0,
            rating: 0,
            win_rate: 0,
            opening_diversity: 0,
            count: 0
          };
        }
        yearlyData[year].games_played += item.games_played;
        yearlyData[year].rating += item.avg_elo;
        yearlyData[year].win_rate += item.win_rate;
        yearlyData[year].opening_diversity += item.opening_diversity;
        yearlyData[year].count += 1;
      });

      return Object.values(yearlyData).map(item => ({
        ...item,
        rating: Math.round(item.rating / item.count),
        win_rate: Number((item.win_rate / item.count).toFixed(2)),
        opening_diversity: Number((item.opening_diversity / item.count).toFixed(2))
      }));
    }
    return performanceData.map(item => ({
      ...item,
      rating: item.avg_elo
    }));
  };

  const data = getScaledData();

  return (
    <div className="space-y-8">
      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
        <MetricCard
          title="Overall Win Rate"
          value={`${metrics.winRate.toFixed(1)}%`}
          icon={<TrendingUp className="h-8 w-8" />}
          description="Weighted average across all games"
        />
        <MetricCard
          title="Total Games"
          value={metrics.totalGames}
          icon={<Activity className="h-8 w-8" />}
          description="Total games played in period"
        />
        <MetricCard
          title="Peak Rating"
          value={metrics.peakRating}
          icon={<Award className="h-8 w-8" />}
          description="Highest average rating achieved"
        />
        <MetricCard
          title="Avg Game Length"
          value={`${metrics.avgGameLength}`}
          icon={<Clock className="h-8 w-8" />}
          description="Average moves per game"
        />
        <MetricCard
          title="Opening Diversity"
          value={`${metrics.openingDiversity.toFixed(1)}%`}
          icon={<Shuffle className="h-8 w-8" />}
          description="Variety in opening choices"
        />
      </div>

      {/* Performance Trend Chart */}
      <PerformanceTrendChart data={data} timeScale={timeScale} setTimeScale={setTimeScale} />
    </div>
  );
}

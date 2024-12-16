import React from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { AlertCircle, Database, User, Activity, TrendingUp } from 'lucide-react';

/**
 * Player Metrics Component - Displays comprehensive player performance analytics
 * @param {Object} props - Component properties
 * @param {Object} props.data - Player performance data
 * @param {string} props.data.overallWinRate - Overall win rate percentage
 * @param {number} props.data.totalGames - Total number of games played
 * @param {number} props.data.peakRating - Peak ELO rating achieved
 * @param {Array} props.data.trend - Performance trend data over time
 * @param {Array} props.data.colorStats - Statistics by piece color
 * @param {Array} props.data.gameLengths - Game length distribution data
 */
export const PlayerMetricsView = ({ data }) => {
  if (!data) return null;

  // Format trend data for visualization
  const formattedTrendData = data.trend?.map(item => ({
    ...item,
    winRate: parseFloat(item.winRate).toFixed(1),
    date: new Date(item.date).toLocaleDateString(),
  })) || [];

  return (
    <div className="space-y-6">
      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Overall Win Rate"
          value={`${data.overallWinRate}%`}
          icon={<TrendingUp className="h-8 w-8 text-green-500" />}
        />
        <MetricCard
          title="Total Games"
          value={data.totalGames?.toLocaleString()}
          icon={<Activity className="h-8 w-8 text-blue-500" />}
        />
        <MetricCard
          title="Peak Rating"
          value={data.peakRating || 'N/A'}
          icon={<AlertCircle className="h-8 w-8 text-yellow-500" />}
        />
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PerformanceTrendChart data={formattedTrendData} />
        <ColorPerformanceChart data={data.colorStats} />
        <GameLengthDistribution data={data.gameLengths} />
      </div>
    </div>
  );
};

/**
 * Database Metrics Component - Displays database performance and statistics
 * @param {Object} props - Component properties
 * @param {Object} props.data - Database metrics data
 * @param {number} props.data.totalGames - Total games in database
 * @param {number} props.data.totalPlayers - Total players in database
 * @param {number} props.data.avgResponseTime - Average query response time
 * @param {Array} props.data.growth - Database growth metrics over time
 * @param {Array} props.data.performance - Query performance metrics
 */
export const DatabaseMetricsView = ({ data }) => {
  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Database Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Total Games"
          value={data.totalGames?.toLocaleString()}
          icon={<Database className="h-8 w-8 text-blue-500" />}
        />
        <MetricCard
          title="Total Players"
          value={data.totalPlayers?.toLocaleString()}
          icon={<User className="h-8 w-8 text-green-500" />}
        />
        <MetricCard
          title="Avg Response Time"
          value={`${data.avgResponseTime}ms`}
          icon={<Activity className="h-8 w-8 text-purple-500" />}
        />
      </div>

      {/* Database Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DatabaseGrowthChart data={data.growth} />
        <QueryPerformanceChart data={data.performance} />
      </div>
    </div>
  );
};

/**
 * Reusable metric card component for displaying key statistics
 */
const MetricCard = ({ title, value, icon }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-600">{title}</p>
        <p className="mt-1 text-2xl font-semibold">{value}</p>
      </div>
      {icon}
    </div>
  </div>
);

/**
 * Performance trend visualization component
 */
const PerformanceTrendChart = ({ data }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium mb-4">Performance Trend</h3>
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            label={{ value: 'Date', position: 'bottom' }} 
          />
          <YAxis 
            yAxisId="left"
            label={{ value: 'Win Rate (%)', angle: -90, position: 'insideLeft' }}
            domain={[0, 100]} 
          />
          <YAxis 
            yAxisId="right" 
            orientation="right"
            label={{ value: 'Rating', angle: 90, position: 'insideRight' }}
          />
          <Tooltip />
          <Legend />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="winRate"
            stroke="#3B82F6"
            strokeWidth={2}
            name="Win Rate"
            dot={false}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="rating"
            stroke="#10B981"
            strokeWidth={2}
            name="Rating"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>
);

/**
 * Color performance statistics visualization
 */
const ColorPerformanceChart = ({ data }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium mb-4">Color Performance</h3>
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="color" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="games" fill="#3B82F6" name="Games Played" />
          <Bar dataKey="wins" fill="#10B981" name="Wins" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  </div>
);

/**
 * Game length distribution visualization
 */
const GameLengthDistribution = ({ data }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium mb-4">Game Length Distribution</h3>
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="moves" 
            label={{ value: 'Number of Moves', position: 'bottom' }} 
          />
          <YAxis 
            label={{ value: 'Number of Games', angle: -90, position: 'insideLeft' }} 
          />
          <Tooltip />
          <Bar dataKey="count" fill="#8B5CF6" name="Games" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  </div>
);

/**
 * Database growth visualization
 */
const DatabaseGrowthChart = ({ data }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium mb-4">Database Growth</h3>
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="games"
            stroke="#3B82F6"
            strokeWidth={2}
            name="Games"
          />
          <Line
            type="monotone"
            dataKey="players"
            stroke="#10B981"
            strokeWidth={2}
            name="Players"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>
);

/**
 * Query performance visualization
 */
const QueryPerformanceChart = ({ data }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium mb-4">Query Performance</h3>
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="query" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar
            dataKey="avgTime"
            fill="#8B5CF6"
            name="Average Response Time (ms)"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  </div>
);
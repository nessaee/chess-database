import React from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { AlertCircle, Database, User, Activity, TrendingUp } from 'lucide-react';
import MetricCard from './shared/MetricCard';

/**
 * Database growth visualization component
 * @param {Object} props - Component properties
 * @param {Array} props.data - Growth trend data
 */
const DatabaseGrowthChart = ({ data }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium mb-4">Database Growth</h3>
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="games" stroke="#6366F1" name="Games" />
          <Line type="monotone" dataKey="players" stroke="#10B981" name="Players" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>
);

/**
 * Query performance visualization component
 * @param {Object} props - Component properties
 * @param {Array} props.data - Query performance data
 */
const QueryPerformanceChart = ({ data }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium mb-4">Query Performance</h3>
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="avgResponseTime" stroke="#6366F1" name="Avg Response Time (ms)" />
          <Line type="monotone" dataKey="queryCount" stroke="#10B981" name="Query Count" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>
);

/**
 * Database Metrics Component - Displays database performance and statistics
 * @param {Object} props - Component properties
 * @param {Object} props.data - Database metrics data
 */
export default function DatabaseMetricsView({ data }) {
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
          title="Avg Moves/Game"
          value={data.avgMovesPerGame?.toFixed(1)}
          icon={<Activity className="h-8 w-8 text-purple-500" />}
        />
      </div>

      {/* Performance Metrics */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">Performance Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricCard
            title="White Win Rate"
            value={`${(data.performance?.white_win_rate * 100).toFixed(1)}%`}
            icon={<TrendingUp className="h-8 w-8 text-green-500" />}
          />
          <MetricCard
            title="Draw Rate"
            value={`${(data.performance?.draw_rate * 100).toFixed(1)}%`}
            icon={<Activity className="h-8 w-8 text-yellow-500" />}
          />
          <MetricCard
            title="Avg Game Length"
            value={data.performance?.avg_game_length?.toFixed(1)}
            icon={<AlertCircle className="h-8 w-8 text-blue-500" />}
          />
        </div>
      </div>

      {/* Growth Trends */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">Growth Trends</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium mb-2">Monthly Averages</h4>
            <div className="grid grid-cols-2 gap-4">
              <MetricCard
                title="Games"
                value={data.growthTrends?.avg_monthly_games?.toFixed(0)}
                icon={<Database className="h-6 w-6 text-blue-500" />}
              />
              <MetricCard
                title="Players"
                value={data.growthTrends?.avg_monthly_players?.toFixed(0)}
                icon={<User className="h-6 w-6 text-green-500" />}
              />
            </div>
          </div>
          <div>
            <h4 className="text-sm font-medium mb-2">Peak Numbers</h4>
            <div className="grid grid-cols-2 gap-4">
              <MetricCard
                title="Games"
                value={data.growthTrends?.peak_monthly_games?.toLocaleString()}
                icon={<Database className="h-6 w-6 text-blue-500" />}
              />
              <MetricCard
                title="Players"
                value={data.growthTrends?.peak_monthly_players?.toLocaleString()}
                icon={<User className="h-6 w-6 text-green-500" />}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Health Metrics */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">Data Quality</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricCard
            title="Missing Moves"
            value={`${(data.healthMetrics?.null_moves_rate * 100).toFixed(2)}%`}
            icon={<AlertCircle className="h-8 w-8 text-red-500" />}
          />
          <MetricCard
            title="Missing Players"
            value={`${(data.healthMetrics?.missing_player_rate * 100).toFixed(2)}%`}
            icon={<AlertCircle className="h-8 w-8 text-yellow-500" />}
          />
          <MetricCard
            title="Missing Results"
            value={`${(data.healthMetrics?.missing_result_rate * 100).toFixed(2)}%`}
            icon={<AlertCircle className="h-8 w-8 text-orange-500" />}
          />
        </div>
      </div>

      {/* Growth and Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DatabaseGrowthChart data={data.growthTrends?.monthly_data || []} />
        <QueryPerformanceChart data={data.performance?.query_metrics || []} />
      </div>
    </div>
  );
};

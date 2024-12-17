import React from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { AlertCircle, Activity, TrendingUp } from 'lucide-react';
import MetricCard from './shared/MetricCard';

/**
 * Performance trend visualization component
 * @param {Object} props - Component properties
 * @param {Array} props.data - Performance trend data
 */
export const PerformanceTrendChart = ({ data }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium mb-4">Performance Trend</h3>
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="winRate" stroke="#10B981" name="Win Rate %" />
          <Line type="monotone" dataKey="rating" stroke="#6366F1" name="Rating" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>
);

/**
 * Color performance statistics visualization
 * @param {Object} props - Component properties
 * @param {Array} props.data - Color performance data
 */
export const ColorPerformanceChart = ({ data }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium mb-4">Color Performance</h3>
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="color" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="gamesPlayed" fill="#6366F1" name="Games Played" />
          <Bar dataKey="wins" fill="#10B981" name="Wins" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  </div>
);

/**
 * Game length distribution visualization
 * @param {Object} props - Component properties
 * @param {Array} props.data - Game length distribution data
 */
export const GameLengthDistribution = ({ data }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium mb-4">Game Length Distribution</h3>
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="moves" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="games" fill="#6366F1" name="Games" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  </div>
);

/**
 * Opening Analysis View
 * @param {Object} props - Component properties
 * @param {Object} props.data - Opening analysis data
 */
export const OpeningAnalysisView = ({ data }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium mb-4">Opening Analysis</h3>
    <div className="h-80">
      {/* Opening analysis visualization */}
    </div>
  </div>
);

/**
 * Player Metrics Component - Displays comprehensive player performance analytics
 * @param {Object} props - Component properties
 * @param {Object} props.data - Player performance data
 * @param {Object} props.openingAnalysis - Opening analysis data
 */
export default function PlayerMetricsView({ data = {} }) {
  const { 
    overallWinRate = 0, 
    totalGames = 0, 
    peakRating = 0, 
    trend = [], 
    colorStats = [], 
    gameLengths = [] 
  } = data || {};

  return (
    <div className="space-y-8">
      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard
          title="Overall Win Rate"
          value={`${Number(overallWinRate).toFixed(1)}%`}
          icon={<TrendingUp className="h-8 w-8" />}
        />
        <MetricCard
          title="Total Games"
          value={totalGames}
          icon={<Activity className="h-8 w-8" />}
        />
        <MetricCard
          title="Peak Rating"
          value={peakRating}
          icon={<AlertCircle className="h-8 w-8" />}
        />
      </div>

      {/* Performance Charts */}
      {trend.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PerformanceTrendChart data={trend} />
          <ColorPerformanceChart data={colorStats} />
        </div>
      )}

      {/* Game Length Distribution */}
      {gameLengths.length > 0 && (
        <div className="mt-8">
          <GameLengthDistribution data={gameLengths} />
        </div>
      )}
    </div>
  );
};

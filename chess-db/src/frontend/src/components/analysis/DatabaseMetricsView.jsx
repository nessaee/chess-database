import React, { useState, useEffect, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer
} from 'recharts';
import { AlertCircle, Database, User, Activity } from 'lucide-react';
import { databaseMetricsService } from '../../services/DatabaseMetricsService';
import { LoadingState, ErrorState } from '../states/LoadingStates';
import MetricCard from './shared/MetricCard';

/**
 * Query performance visualization component
 * @param {Object} props - Component properties
 * @param {Array} props.data - Query performance data
 */
const EndpointPerformanceChart = ({ data = [] }) => {
  const [selectedMetrics, setSelectedMetrics] = useState({
    responseTime: true,
    successRate: true,
    responseSize: false
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({
    metric: 'avg_response_time',
    direction: 'desc'
  });

  const metrics = [
    { id: 'responseTime', name: 'Avg Response Time', dataKey: 'avg_response_time', color: '#2563eb', unit: 'ms' },
    { id: 'successRate', name: 'Success Rate', dataKey: 'success_rate', color: '#16a34a', unit: '%' },
    { id: 'responseSize', name: 'Avg Response Size', dataKey: 'avg_response_size', color: '#9333ea', unit: 'KB' }
  ];

  const toggleMetric = (metricId) => {
    // Prevent deselecting all metrics
    const newState = {
      ...selectedMetrics,
      [metricId]: !selectedMetrics[metricId]
    };
    
    // Ensure at least one metric is selected
    if (Object.values(newState).some(v => v)) {
      setSelectedMetrics(newState);
      
      // Update sort config if the currently sorted metric is being deselected
      const metric = metrics.find(m => m.id === metricId);
      if (metric && !newState[metricId] && sortConfig.metric === metric.dataKey) {
        // Find first active metric to sort by
        const firstActiveMetric = metrics.find(m => newState[m.id]);
        if (firstActiveMetric) {
          setSortConfig(prev => ({
            ...prev,
            metric: firstActiveMetric.dataKey
          }));
        }
      }
    }
  };

  const activeMetrics = metrics.filter(metric => selectedMetrics[metric.id]);

  // Calculate dynamic scales for each metric
  const getMetricDomain = (metricKey, data) => {
    if (metricKey === 'success_rate') return [0, 100];
    const values = data.map(d => parseFloat(d[metricKey]) || 0);
    const max = Math.max(...values);
    // Round up to next nice number for better visualization
    const niceMax = Math.ceil(max / Math.pow(10, Math.floor(Math.log10(max)))) * Math.pow(10, Math.floor(Math.log10(max)));
    return [0, niceMax];
  };

  // Filter and sort data
  const processedData = useMemo(() => {
    let filteredData = data
      .filter(d => d.endpoint.toLowerCase().includes(searchTerm.toLowerCase()))
      .map(d => ({
        ...d,
        avg_response_size: d.avg_response_size ? (d.avg_response_size / 1024).toFixed(2) : 0,
        endpoint: d.endpoint.replace(/^\/api\//, '/') // Clean up endpoint display
      }));

    return filteredData.sort((a, b) => {
      const aValue = parseFloat(a[sortConfig.metric]) || 0;
      const bValue = parseFloat(b[sortConfig.metric]) || 0;
      return sortConfig.direction === 'desc' ? bValue - aValue : aValue - bValue;
    });
  }, [data, searchTerm, sortConfig]);

  // Calculate left margin based on longest endpoint name
  const maxEndpointLength = useMemo(() => {
    return Math.min(
      200,
      Math.max(
        180,
        Math.max(...processedData.map(d => d.endpoint.length)) * 6
      )
    );
  }, [processedData]);

  // Format value for display
  const formatValue = (value, metric) => {
    if (metric.dataKey === 'success_rate') {
      return `${parseFloat(value).toFixed(1)}%`;
    }
    if (metric.dataKey === 'avg_response_size') {
      return `${parseFloat(value).toFixed(1)} KB`;
    }
    if (metric.dataKey === 'avg_response_time') {
      const ms = parseFloat(value);
      if (ms >= 1000) {
        return `${(ms/1000).toFixed(1)}s`;
      }
      return `${ms.toFixed(0)}ms`;
    }
    return value;
  };

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      <div className="p-6 space-y-6">
        {/* Header and Title */}
        <div className="flex items-center justify-between border-b border-gray-200 pb-4">
          <h3 className="text-xl font-semibold text-gray-900">
            Endpoint Performance
            <span className="ml-2 text-sm font-normal text-gray-500">Last 24h</span>
          </h3>
        </div>

        {/* Controls Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Metric Toggles */}
          <div className="flex flex-wrap gap-3">
            {metrics.map(metric => {
              const isActive = selectedMetrics[metric.id];
              return (
                <button
                  key={metric.id}
                  onClick={() => toggleMetric(metric.id)}
                  style={{
                    backgroundColor: isActive ? metric.color : '#f3f4f6',
                    borderColor: metric.color,
                    color: isActive ? 'white' : '#4b5563'
                  }}
                  className={`
                    px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200
                    border-2 hover:shadow-md
                    ${isActive ? 'shadow-sm' : 'hover:bg-gray-100'}
                  `}
                  title={isActive ? `Click to hide ${metric.name}` : `Click to show ${metric.name}`}
                >
                  <span className="flex items-center gap-2">
                    <span 
                      className="w-2 h-2 rounded-full" 
                      style={{ 
                        backgroundColor: isActive ? 'white' : metric.color,
                        boxShadow: isActive ? 'none' : '0 0 0 2px rgba(255,255,255,0.8)'
                      }} 
                    />
                    {metric.name}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Search and Sort Controls */}
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <input
                type="text"
                placeholder="Search endpoints..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
              />
              <svg
                className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
            <div className="flex items-center gap-2 min-w-[200px]">
              <select
                value={sortConfig.metric}
                onChange={(e) => setSortConfig(prev => ({ ...prev, metric: e.target.value }))}
                className="flex-1 rounded-lg border border-gray-300 py-2 pl-3 pr-10 focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
              >
                {metrics.map(metric => (
                  <option key={metric.dataKey} value={metric.dataKey}>{metric.name}</option>
                ))}
              </select>
              <button
                onClick={() => setSortConfig(prev => ({
                  ...prev,
                  direction: prev.direction === 'desc' ? 'asc' : 'desc'
                }))}
                className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 shadow-sm"
              >
                {sortConfig.direction === 'desc' ? '↓' : '↑'}
              </button>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="h-[800px] mt-8">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={processedData}
              layout="vertical" 
              margin={{ 
                left: maxEndpointLength, 
                right: 40, 
                top: 40, 
                bottom: 20 
              }}
              barSize={20}
              barGap={2}
            >
              <CartesianGrid strokeDasharray="3 3" />
              {activeMetrics.map((metric, index) => (
                <XAxis 
                  key={metric.id}
                  type="number"
                  xAxisId={metric.id}
                  orientation={index === 0 ? "bottom" : "top"}
                  domain={getMetricDomain(metric.dataKey, processedData)}
                  tickFormatter={(value) => formatValue(value, metric)}
                  label={{ 
                    value: `${metric.name} (${metric.unit})`, 
                    position: index === 0 ? "bottom" : "top",
                    style: { fill: metric.color }
                  }}
                />
              ))}
              <YAxis 
                type="category" 
                dataKey="endpoint" 
                width={maxEndpointLength - 20}
                tick={{ 
                  fill: '#374151',
                  fontSize: '12px',
                  textAnchor: 'end',
                }}
              />
              <Tooltip 
                contentStyle={{ 
                  borderRadius: '8px',
                  border: 'none',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
                }}
                formatter={(value, name) => {
                  const metric = metrics.find(m => m.name === name);
                  return [formatValue(value, metric), name];
                }}
              />
              {activeMetrics.map(metric => (
                <Bar 
                  key={metric.id}
                  dataKey={metric.dataKey}
                  name={metric.name}
                  fill={metric.color}
                  xAxisId={metric.id}
                  radius={[4, 4, 4, 4]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

/**
 * Database Metrics View Component
 * Displays comprehensive database performance and statistics
 */
const DatabaseMetricsView = ({ metrics, onRefresh }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [metricsData, setMetricsData] = useState(metrics || null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Update metrics when prop changes
  useEffect(() => {
    if (metrics) {
      setMetricsData(metrics);
    }
  }, [metrics]);

  const handleRefresh = async () => {
    if (isRefreshing) return;
    setIsRefreshing(true);
    try {
      await onRefresh();
    } catch (err) {
      setError(err.message || 'Failed to refresh metrics');
    } finally {
      setIsRefreshing(false);
    }
  };

  if (!metricsData) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (loading && metricsData) return <LoadingState />;

  const {
    total_games = 0,
    total_players = 0,
    avg_moves_per_game = 0,
    endpoint_metrics = [],
    health_metrics = { status: 'healthy' }
  } = metricsData;

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="flex justify-between items-center">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 flex-1">
          <MetricCard
            title="Total Games"
            value={total_games.toLocaleString()}
            icon={<Database className="h-6 w-6" />}
          />
          <MetricCard
            title="Total Players"
            value={total_players.toLocaleString()}
            icon={<User className="h-6 w-6" />}
          />
          <MetricCard
            title="Avg Moves/Game"
            value={avg_moves_per_game.toFixed(1)}
            icon={<Activity className="h-6 w-6" />}
          />
        </div>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className={`
            ml-4 p-2 rounded-lg border border-gray-300 hover:bg-gray-50 
            transition-all duration-200 ${isRefreshing ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          title="Refresh metrics"
        >
          <svg
            className={`h-5 w-5 text-gray-600 ${isRefreshing ? 'animate-spin' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </button>
      </div>

      {/* Endpoint Performance Chart */}
      <EndpointPerformanceChart data={endpoint_metrics} />

      {/* Health Status */}
      {health_metrics.status !== 'healthy' && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-yellow-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                Database health check detected issues. Status: {health_metrics.status}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Loading Overlay */}
      {loading && metricsData && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-4 flex items-center space-x-3">
            <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span className="text-gray-700">Refreshing metrics...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatabaseMetricsView;

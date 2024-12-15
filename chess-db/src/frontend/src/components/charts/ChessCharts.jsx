import React from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts';
import { MoveCountTooltip, PerformanceTooltip } from '../tooltips/ChessTooltips';

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
            dataKey="actual_full_moves"
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
            dataKey="number_of_games"
            fill="#8884d8"
            name="Games"
            radius={[4, 4, 0, 0]}
            className="hover:opacity-80 transition-opacity"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  </div>
);

export const PerformanceTimeline = ({ data, title }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <h2 className="text-xl font-bold mb-4">{title || 'Performance Timeline'}</h2>
    <div className="h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 20, right: 30, left: 40, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
          <XAxis 
            dataKey="time_period"
            label={{ value: 'Time Period', position: 'bottom', offset: -10 }}
          />
          <YAxis 
            yAxisId="rate"
            label={{ value: 'Win Rate (%)', angle: -90, position: 'insideLeft', offset: 10 }}
          />
          <YAxis 
            yAxisId="games"
            orientation="right"
            label={{ value: 'Games Played', angle: 90, position: 'insideRight', offset: 10 }}
          />
          <Tooltip content={<PerformanceTooltip />} />
          <Legend />
          <Line
            type="monotone"
            dataKey="win_rate"
            stroke="#10B981"
            yAxisId="rate"
            name="Win Rate"
          />
          <Line
            type="monotone"
            dataKey="games_played"
            stroke="#6366F1"
            yAxisId="games"
            name="Games Played"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>
);

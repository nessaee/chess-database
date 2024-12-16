import React from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { BookOpen, Swords, Calendar } from 'lucide-react';

// Helper function to format win rate
const formatWinRate = (rate) => `${rate.toFixed(1)}%`;

// Helper to determine color based on win rate
const getWinRateColor = (rate) => {
  if (rate >= 60) return '#10B981';
  if (rate >= 50) return '#6366F1';
  return '#EC4899';
};

const OpeningSummaryCard = ({ title, value, subtitle, icon: Icon }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
        {subtitle && (
          <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
        )}
      </div>
      {Icon && <Icon className="h-5 w-5 text-gray-400" />}
    </div>
  </div>
);

const OpeningPerformanceTable = ({ openings }) => (
  <div className="bg-white rounded-lg shadow overflow-hidden">
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Opening
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Games
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Win Rate
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              W/D/L
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Avg Length
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {openings.map((opening, idx) => (
            <tr key={opening.eco_code} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {opening.opening_name}
                  </div>
                  <div className="text-sm text-gray-500">
                    {opening.eco_code}
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {opening.total_games}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900 font-medium" style={{ color: getWinRateColor(opening.win_rate) }}>
                  {formatWinRate(opening.win_rate)}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {`${opening.win_count}/${opening.draw_count}/${opening.loss_count}`}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {opening.avg_game_length.toFixed(1)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

const OpeningWinRateChart = ({ openings }) => {
  const data = openings
    .sort((a, b) => b.win_rate - a.win_rate)
    .slice(0, 10)
    .map(opening => ({
      name: opening.eco_code,
      winRate: opening.win_rate,
      games: opening.total_games,
    }));

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Top Opening Win Rates</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" />
            <YAxis domain={[0, 100]} />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-2 border rounded shadow-lg">
                    <p className="font-medium">{data.name}</p>
                    <p className="text-sm">Win Rate: {data.winRate.toFixed(1)}%</p>
                    <p className="text-sm">Games: {data.games}</p>
                  </div>
                );
              }}
            />
            <Bar dataKey="winRate" fill="#6366F1">
              {data.map((entry, index) => (
                <Cell key={index} fill={getWinRateColor(entry.winRate)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const OpeningAnalysisView = ({ data }) => {
  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <OpeningSummaryCard
          title="Total Openings"
          value={data.total_openings}
          icon={BookOpen}
        />
        <OpeningSummaryCard
          title="Most Successful"
          value={data.most_successful}
          subtitle={`${data.analysis.find(o => o.eco_code === data.most_successful)?.win_rate.toFixed(1)}% Win Rate`}
          icon={Swords}
        />
        <OpeningSummaryCard
          title="Average Game Length"
          value={`${data.avg_game_length.toFixed(1)} moves`}
          icon={Calendar}
        />
      </div>

      {/* Win Rate Chart */}
      <OpeningWinRateChart openings={data.analysis} />

      {/* Detailed Performance Table */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Opening Performance Details</h3>
        <OpeningPerformanceTable openings={data.analysis} />
      </div>
    </div>
  );
};

export default OpeningAnalysisView;
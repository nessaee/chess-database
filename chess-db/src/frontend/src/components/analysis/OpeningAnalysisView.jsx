import React from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts';
import { BookOpen, Sword, Clock, Target, TrendingUp } from 'lucide-react';

// Helper function to format win rate
const formatWinRate = (rate) => `${rate.toFixed(1)}%`;

// Helper to determine color based on win rate
const getWinRateColor = (rate) => {
  if (rate >= 60) return '#10B981';
  if (rate >= 50) return '#6366F1';
  return '#EC4899';
};

const OpeningSummaryCard = ({ title, value, subtitle, icon: Icon, trend }) => (
  <div className="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
        {subtitle && (
          <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
        )}
        {trend && (
          <p className={`mt-1 text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% vs prev period
          </p>
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
              Color Split
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {openings.map((opening, idx) => (
            <tr key={opening.eco} className={idx % 2 === 0 ? 'bg-white hover:bg-gray-50' : 'bg-gray-50 hover:bg-gray-100'}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {opening.name}
                  </div>
                  <div className="text-sm text-gray-500">
                    {opening.eco}
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {opening.games_played}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                    <div 
                      className="rounded-full h-2" 
                      style={{ 
                        width: `${opening.win_rate}%`,
                        backgroundColor: getWinRateColor(opening.win_rate)
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium" style={{ color: getWinRateColor(opening.win_rate) }}>
                    {formatWinRate(opening.win_rate)}
                  </span>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <span className="text-green-600">{opening.wins}</span>
                <span className="text-gray-500">/{opening.draws}/</span>
                <span className="text-red-600">{opening.losses}</span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <div className="flex items-center space-x-1">
                  <div className="w-4 h-4 bg-white border rounded-full" title="White"></div>
                  <span>{opening.white_games}</span>
                  <div className="w-4 h-4 bg-gray-800 rounded-full" title="Black"></div>
                  <span>{opening.black_games}</span>
                </div>
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
      name: opening.eco,
      winRate: opening.win_rate,
      games: opening.games_played,
      openingName: opening.name
    }));

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Top Opening Win Rates</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis 
              dataKey="name" 
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => value}
            />
            <YAxis domain={[0, 100]} />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 border rounded shadow-lg">
                    <p className="font-medium">{data.openingName}</p>
                    <p className="text-sm font-medium">{data.name}</p>
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

const ColorDistributionChart = ({ openings }) => {
  const totalWhite = openings.reduce((sum, o) => sum + o.white_games, 0);
  const totalBlack = openings.reduce((sum, o) => sum + o.black_games, 0);
  const data = [
    { name: 'White', value: totalWhite, color: '#F3F4F6' },
    { name: 'Black', value: totalBlack, color: '#1F2937' }
  ];

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Color Distribution</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-2 border rounded shadow-lg">
                    <p className="font-medium">{data.name}</p>
                    <p className="text-sm">Games: {data.value}</p>
                    <p className="text-sm">
                      {((data.value / (totalWhite + totalBlack)) * 100).toFixed(1)}%
                    </p>
                  </div>
                );
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const OpeningAnalysisView = ({ data }) => {
  if (!data?.openings) return null;

  const { openings, total_games, total_wins, total_draws, total_losses } = data;
  const overallWinRate = (total_wins / total_games) * 100;

  const bestOpening = openings.reduce((best, current) => 
    current.win_rate > (best?.win_rate || 0) ? current : best
  , null);

  return (
    <div className="space-y-6">
      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <OpeningSummaryCard
          title="Total Openings"
          value={openings.length}
          subtitle={`${total_games} games analyzed`}
          icon={BookOpen}
        />
        <OpeningSummaryCard
          title="Most Successful"
          value={bestOpening?.name || 'N/A'}
          subtitle={bestOpening ? `${formatWinRate(bestOpening.win_rate)} Win Rate` : 'No data'}
          icon={Sword}
        />
        <OpeningSummaryCard
          title="Overall Performance"
          value={formatWinRate(overallWinRate)}
          subtitle={`${total_wins}W/${total_draws}D/${total_losses}L`}
          icon={TrendingUp}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Win Rate Chart */}
        <OpeningWinRateChart openings={openings} />
        {/* Color Distribution */}
        <ColorDistributionChart openings={openings} />
      </div>

      {/* Detailed Performance Table */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Opening Performance Details</h3>
        <OpeningPerformanceTable openings={openings} />
      </div>
    </div>
  );
};

export default OpeningAnalysisView;
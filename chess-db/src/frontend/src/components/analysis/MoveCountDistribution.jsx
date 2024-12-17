import React, { useEffect, useState } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { MoveCountTooltip } from '../tooltips/ChessTooltips';

const MoveCountDistribution = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/analysis/move-counts');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-80">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
        <p className="text-red-600">Error loading move count data: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-medium mb-4">Game Length Distribution</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="move_count" 
              label={{ 
                value: 'Number of Moves', 
                position: 'insideBottom', 
                offset: -5 
              }}
            />
            <YAxis 
              label={{ 
                value: 'Number of Games', 
                angle: -90, 
                position: 'insideLeft'
              }}
            />
            <Tooltip content={<MoveCountTooltip />} />
            <Legend />
            <Bar 
              dataKey="game_count" 
              fill="#6366F1" 
              name="Games"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 text-sm text-gray-500">
        <p>Distribution of chess games by number of moves played. Each bar represents the number of games that lasted for that many moves.</p>
      </div>
    </div>
  );
};

export default MoveCountDistribution;

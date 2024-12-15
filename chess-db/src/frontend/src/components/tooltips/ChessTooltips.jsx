import React from 'react';

export const MoveCountTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;

  const data = payload[0].payload;
  return (
    <div className="bg-white p-4 border rounded shadow-lg">
      <h4 className="font-semibold mb-2">Move Count Analysis</h4>
      <div className="space-y-1 text-sm">
        <p>Moves: {data.actual_full_moves}</p>
        <p>Games: {data.number_of_games.toLocaleString()}</p>
        <p>Average Size: {data.avg_bytes.toFixed(1)} bytes</p>
        {data.avg_stored_count && (
          <p>Average Stored Count: {data.avg_stored_count.toFixed(1)}</p>
        )}
        <div className="mt-2 text-xs text-gray-500">
          <p>Results: {data.results}</p>
        </div>
      </div>
    </div>
  );
};

export const PerformanceTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;

  const data = payload[0].payload;
  return (
    <div className="bg-white p-4 border rounded shadow-lg">
      <h4 className="font-semibold mb-2">{data.time_period}</h4>
      <div className="space-y-1 text-sm">
        <p>Games Played: {data.games_played.toLocaleString()}</p>
        <p>Win Rate: {data.win_rate.toFixed(1)}%</p>
        <p>Average Moves: {data.avg_moves.toFixed(1)}</p>
        <div className="mt-2 border-t pt-2">
          <p>White Games: {data.white_games}</p>
          <p>Black Games: {data.black_games}</p>
          {data.elo_rating && <p>ELO Rating: {data.elo_rating}</p>}
        </div>
      </div>
    </div>
  );
};

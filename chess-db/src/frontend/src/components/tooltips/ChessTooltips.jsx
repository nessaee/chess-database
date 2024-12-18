import React from 'react';
import PropTypes from 'prop-types';

export const MoveCountTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const data = payload[0].payload;
  return (
    <div className="bg-white p-3 rounded shadow-lg border border-gray-200">
      <p className="font-semibold text-gray-800">Move Count: {data.move_count}</p>
      <p className="text-gray-600">Games: {data.game_count.toLocaleString()}</p>
      <p className="text-gray-600">Avg Bytes: {data.avg_bytes.toFixed(2)}</p>
    </div>
  );
};

MoveCountTooltip.propTypes = {
  active: PropTypes.bool,
  payload: PropTypes.arrayOf(PropTypes.shape({
    payload: PropTypes.shape({
      move_count: PropTypes.number.isRequired,
      game_count: PropTypes.number.isRequired,
      avg_bytes: PropTypes.number.isRequired
    })
  }))
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

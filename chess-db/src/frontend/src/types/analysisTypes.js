// src/types/analysisTypes.js

import PropTypes from 'prop-types';

/**
 * PropTypes definition for move distribution data item
 * Represents statistical data about chess move counts and frequencies
 */
export const MoveDistributionItemPropTypes = PropTypes.shape({
  /** Number of full moves in the game */
  actual_full_moves: PropTypes.number.isRequired,
  /** Count of games with this move count */
  number_of_games: PropTypes.number.isRequired,
  /** Average size of encoded game data */
  avg_bytes: PropTypes.number.isRequired,
  /** Aggregated game results */
  results: PropTypes.string.isRequired,
  /** Minimum number of stored moves */
  min_stored_count: PropTypes.number,
  /** Maximum number of stored moves */
  max_stored_count: PropTypes.number,
  /** Average number of stored moves */
  avg_stored_count: PropTypes.number.isRequired
});

/**
 * PropTypes definition for the analysis interface component
 * Defines the expected props for the main analysis control interface
 */
export const AnalysisInterfaceProps = {
  /** Time range for data aggregation (monthly/yearly) */
  timeRange: PropTypes.oneOf(['monthly', 'yearly']).isRequired,
  /** Date range for filtering analysis data */
  dateRange: PropTypes.shape({
    start: PropTypes.string,
    end: PropTypes.string
  }).isRequired,
  /** Callback for time range changes */
  onTimeRangeChange: PropTypes.func.isRequired,
  /** Callback for date range changes */
  onDateRangeChange: PropTypes.func.isRequired,
  /** Callback for player selection */
  onPlayerSelect: PropTypes.func.isRequired,
  /** Flag to disable the interface */
  disabled: PropTypes.bool
};

/**
 * PropTypes definition for performance timeline data
 * Represents player performance statistics over time
 */
export const PerformanceTimelineItemPropTypes = PropTypes.shape({
  /** Time period identifier */
  time_period: PropTypes.string.isRequired,
  /** Total games played in period */
  games_played: PropTypes.number.isRequired,
  /** Win rate percentage */
  win_rate: PropTypes.number.isRequired,
  /** Games played as white */
  white_games: PropTypes.number.isRequired,
  /** Games played as black */
  black_games: PropTypes.number.isRequired,
  /** Average game length in moves */
  avg_moves: PropTypes.number.isRequired,
  /** Optional ELO rating */
  elo_rating: PropTypes.number
});
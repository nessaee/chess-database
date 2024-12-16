// src/types/openingTypes.js

import PropTypes from 'prop-types';

/**
 * PropTypes definition for individual opening analysis data
 * Represents detailed statistics for a specific chess opening
 */
export const OpeningAnalysisPropTypes = PropTypes.shape({
  /** ECO code identifier for the opening */
  eco_code: PropTypes.string.isRequired,
  /** Full name of the opening */
  opening_name: PropTypes.string.isRequired,
  /** Total number of games played with this opening */
  total_games: PropTypes.number.isRequired,
  /** Number of games won */
  win_count: PropTypes.number.isRequired,
  /** Number of games drawn */
  draw_count: PropTypes.number.isRequired,
  /** Number of games lost */
  loss_count: PropTypes.number.isRequired,
  /** Win percentage (0-100) */
  win_rate: PropTypes.number.isRequired,
  /** Average game length in moves */
  avg_game_length: PropTypes.number.isRequired,
  /** Number of games played as white */
  games_as_white: PropTypes.number.isRequired,
  /** Number of games played as black */
  games_as_black: PropTypes.number.isRequired,
  /** Average opponent ELO rating */
  avg_opponent_rating: PropTypes.number,
  /** Date of most recent game */
  last_played: PropTypes.string,
  /** Most common response sequence */
  favorite_response: PropTypes.string
});

/**
 * PropTypes definition for the complete opening analysis response
 * Includes both individual opening data and aggregate statistics
 */
export const OpeningAnalysisResponsePropTypes = PropTypes.shape({
  /** Array of individual opening analyses */
  analysis: PropTypes.arrayOf(OpeningAnalysisPropTypes).isRequired,
  /** Total number of distinct openings played */
  total_openings: PropTypes.number.isRequired,
  /** ECO code of the most successful opening */
  most_successful: PropTypes.string,
  /** ECO code of the most frequently played opening */
  most_played: PropTypes.string,
  /** Overall average game length */
  avg_game_length: PropTypes.number.isRequired
});
import { BaseService } from './BaseService';
import { API_ENDPOINTS, API_CONFIG, CACHE_TIMEOUTS } from './constants';

/**
 * Service for handling chess game-related API interactions.
 */
export class GameService extends BaseService {
  /**
   * Get total number of games in the database
   * 
   * @returns {Promise<number>} Total game count
   */
  async getGameCount() {
    return this.getCachedData(
      'game-count',
      () => this.get(API_ENDPOINTS.GAMES.COUNT),
      CACHE_TIMEOUTS.SHORT
    );
  }

  /**
   * Get recent games
   * 
   * @param {Object} options - Query options
   * @param {number} [options.limit=10] - Maximum number of games to return
   * @param {string} [options.moveNotation='san'] - Move notation format ('uci' or 'san')
   * @returns {Promise<Array>} List of recent games
   */
  async getRecentGames({ limit = 10, moveNotation = API_CONFIG.MOVE_NOTATION } = {}) {
    return this.get(API_ENDPOINTS.GAMES.RECENT, {
      limit: Math.min(Math.max(1, limit), API_CONFIG.MAX_LIMIT),
      move_notation: moveNotation
    });
  }

  /**
   * Fetches games for a specific player.
   * 
   * @param {string} playerName - Name of the player
   * @param {Object} options - Query options
   * @param {string} [options.startDate] - Start date (YYYY-MM-DD)
   * @param {string} [options.endDate] - End date (YYYY-MM-DD)
   * @param {boolean} [options.onlyDated] - Only include games with dates
   * @param {number} [options.limit=50] - Maximum number of games to return
   * @param {string} [options.moveNotation='san'] - Move notation format
   * @returns {Promise<Array>} List of games
   */
  async getPlayerGames(playerName, {
    startDate,
    endDate,
    onlyDated = false,
    limit = API_CONFIG.DEFAULT_LIMIT,
    moveNotation = API_CONFIG.MOVE_NOTATION
  } = {}) {
    if (!playerName) {
      throw new Error('Player name is required');
    }

    return this.get(API_ENDPOINTS.GAMES.PLAYER_GAMES(playerName), {
      ...(startDate && { start_date: startDate }),
      ...(endDate && { end_date: endDate }),
      only_dated: onlyDated,
      limit: Math.min(Math.max(1, limit), API_CONFIG.MAX_LIMIT),
      move_notation: moveNotation
    });
  }

  /**
   * Get player name suggestions based on partial input
   * 
   * @param {string} name - Partial player name
   * @param {number} [limit=10] - Maximum number of suggestions
   * @returns {Promise<Array<string>>} List of player name suggestions
   */
  async getPlayerSuggestions(name, limit = 10) {
    return this.get(API_ENDPOINTS.GAMES.PLAYER_SUGGESTIONS, {
      name,
      limit: Math.min(Math.max(1, limit), API_CONFIG.MAX_LIMIT)
    });
  }

  /**
   * Get a specific game by ID
   * 
   * @param {number} gameId - Game ID
   * @param {string} [moveNotation='san'] - Move notation format
   * @returns {Promise<Object>} Game details
   */
  async getGameById(gameId, moveNotation = API_CONFIG.MOVE_NOTATION) {
    return this.get(API_ENDPOINTS.GAMES.GAME_BY_ID(gameId), {
      move_notation: moveNotation
    });
  }

  /**
   * Fetches game count statistics.
   * 
   * @returns {Promise<Object>} Game statistics
   */
  async getGameStats() {
    return this.getCachedData(
      'game-stats',
      () => this.get(API_ENDPOINTS.GAMES.STATS),
      CACHE_TIMEOUTS.MEDIUM
    );
  }
}

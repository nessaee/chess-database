import { BaseService } from './BaseService';

/**
 * Service for handling chess game-related API interactions.
 */
export class GameService extends BaseService {
  /**
   * Fetches games for a specific player.
   * 
   * @param {string} playerName - Name of the player
   * @param {Object} options - Query options
   * @param {string} [options.startDate] - Start date (YYYY-MM-DD)
   * @param {string} [options.endDate] - End date (YYYY-MM-DD)
   * @param {boolean} [options.onlyDated] - Only include games with dates
   * @param {number} [options.limit=50] - Maximum number of games to return
   * @returns {Promise<Array>} List of games
   */
  async getPlayerGames(playerName, { startDate, endDate, onlyDated = false, limit = 50 } = {}) {
    if (!playerName) {
      throw new Error('Player name is required');
    }

    return this.get(`/games/player/${encodeURIComponent(playerName)}`, {
      ...(startDate && { start_date: startDate }),
      ...(endDate && { end_date: endDate }),
      ...(onlyDated && { only_dated: 'true' }),
      limit: limit.toString(),
      move_notation: 'san'
    });
  }

  /**
   * Fetches game count statistics.
   * 
   * @returns {Promise<Object>} Game count statistics
   */
  async getGameStats() {
    return this.getCachedData('game-stats', () => 
      this.get('/games/stats')
    );
  }
}

import { BaseService } from './BaseService';
import { API_ENDPOINTS, API_CONFIG, CACHE_TIMEOUTS } from './constants';

/**
 * Service for handling player-related API interactions.
 */
export class PlayerService extends BaseService {
  /**
   * Search for players by name
   * 
   * @param {string} query - Search query (min length: 2)
   * @param {number} [limit=10] - Maximum number of results
   * @returns {Promise<Array>} List of matching players
   */
  async searchPlayers(query, limit = 10) {
    return this.get(API_ENDPOINTS.PLAYERS.SEARCH, {
      q: query,
      limit: Math.min(Math.max(1, limit), API_CONFIG.MAX_LIMIT)
    });
  }

  /**
   * Get detailed player information
   * 
   * @param {number} playerId - Player ID
   * @returns {Promise<Object>} Player details
   */
  async getPlayer(playerId) {
    const cacheKey = `player_${playerId}`;
    return this.getCachedData(
      cacheKey,
      () => this.get(API_ENDPOINTS.PLAYERS.PLAYER_BY_ID(playerId)),
      CACHE_TIMEOUTS.MEDIUM
    );
  }

  /**
   * Get player performance statistics
   * 
   * @param {number} playerId - Player ID
   * @param {Object} options - Query options
   * @param {string} [options.timePeriod] - Time period filter (e.g., '1y', '6m', '3m', '1m')
   * @returns {Promise<Array>} Performance statistics
   */
  async getPlayerPerformance(playerId, { timePeriod } = {}) {
    const cacheKey = `player_${playerId}_performance_${timePeriod || 'all'}`;
    return this.getCachedData(
      cacheKey,
      () => this.get(API_ENDPOINTS.PLAYERS.PERFORMANCE(playerId), {
        ...(timePeriod && { time_period: timePeriod })
      }),
      CACHE_TIMEOUTS.SHORT
    );
  }

  /**
   * Get detailed player statistics
   * 
   * @param {number} playerId - Player ID
   * @param {Object} options - Query options
   * @param {string} [options.timePeriod] - Time period filter
   * @returns {Promise<Object>} Detailed statistics
   */
  async getDetailedStats(playerId, { timePeriod } = {}) {
    const cacheKey = `player_${playerId}_stats_${timePeriod || 'all'}`;
    return this.getCachedData(
      cacheKey,
      () => this.get(API_ENDPOINTS.PLAYERS.DETAILED_STATS(playerId), {
        ...(timePeriod && { time_period: timePeriod })
      }),
      CACHE_TIMEOUTS.SHORT
    );
  }

  /**
   * Get player opening analysis
   * 
   * @param {number} playerId - Player ID
   * @param {Object} options - Query options
   * @param {number} [options.minGames=5] - Minimum number of games for opening analysis
   * @param {number} [options.limit] - Maximum number of openings to return
   * @param {string} [options.startDate] - Start date (YYYY-MM-DD)
   * @param {string} [options.endDate] - End date (YYYY-MM-DD)
   * @returns {Promise<Object>} Opening analysis
   */
  async getPlayerOpenings(playerId, {
    minGames = 5,
    limit = null,
    startDate,
    endDate
  } = {}) {
    const cacheKey = `player_${playerId}_openings_${minGames}_${limit}_${startDate}_${endDate}`;
    return this.getCachedData(
      cacheKey,
      () => this.get(API_ENDPOINTS.PLAYERS.OPENINGS(playerId), {
        min_games: minGames,
        ...(limit && { limit: Math.min(limit, API_CONFIG.MAX_LIMIT) }),
        ...(startDate && { start_date: startDate }),
        ...(endDate && { end_date: endDate })
      }),
      CACHE_TIMEOUTS.MEDIUM
    );
  }

  /**
   * Get player performance by name (alternative to ID-based lookup)
   * @param {string} playerName - Player name
   * @param {Object} options - Query options
   * @param {string} options.timeRange - Time grouping (daily, weekly, monthly, yearly)
   * @param {string} options.startDate - Start date (YYYY-MM-DD)
   * @param {string} options.endDate - End date (YYYY-MM-DD)
   * @returns {Promise<Array>} Performance statistics
   */
  async getPlayerPerformanceByName(playerName, options = {}) {
    const { timeRange = 'monthly', startDate, endDate } = options;
    try {
      const params = {
        time_range: timeRange,
      };
      
      // Only add date parameters if they are valid
      if (startDate && startDate.trim()) {
        params.start_date = startDate;
      }
      if (endDate && endDate.trim()) {
        params.end_date = endDate;
      }

      return await this.get(`/players/${playerName}/performance`, params);
    } catch (error) {
      console.error('Error fetching player performance:', error);
      throw new Error('Failed to fetch player performance');
    }
  }
}

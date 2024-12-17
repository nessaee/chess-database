import { BaseService } from './BaseService';

/**
 * Service class for handling player-related API calls
 */
export class PlayerService extends BaseService {
  /**
   * Search for players by name
   * @param {string} query - Search query (min length: 2)
   * @param {number} limit - Maximum number of results (default: 10, max: 50)
   * @returns {Promise<Array>} List of matching players
   */
  async searchPlayers(query, limit = 10) {
    try {
      return await this.get('/players/search', {
        q: query,
        limit: Math.min(Math.max(1, limit), 50)
      });
    } catch (error) {
      console.error('Error searching players:', error);
      throw new Error('Failed to search players');
    }
  }

  /**
   * Get detailed player information
   * @param {number} playerId - Player ID
   * @returns {Promise<Object>} Player details
   */
  async getPlayer(playerId) {
    try {
      const cacheKey = `player_${playerId}`;
      return await this.getCachedData(cacheKey, () => 
        this.get(`/players/${playerId}`)
      );
    } catch (error) {
      console.error('Error fetching player:', error);
      throw new Error('Failed to fetch player details');
    }
  }

  /**
   * Get player performance statistics
   * @param {number} playerId - Player ID
   * @param {Object} options - Query options
   * @param {string} options.timeRange - Time grouping (daily, weekly, monthly, yearly)
   * @param {string} options.startDate - Start date (YYYY-MM-DD)
   * @param {string} options.endDate - End date (YYYY-MM-DD)
   * @returns {Promise<Array>} Performance statistics
   */
  async getPlayerPerformance(playerId, options = {}) {
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

      return await this.get(`/players/${playerId}/performance`, params);
    } catch (error) {
      console.error('Error fetching player performance:', error);
      throw new Error('Failed to fetch player performance');
    }
  }

  /**
   * Get player opening analysis
   * @param {number} playerId - Player ID
   * @param {Object} options - Query options
   * @param {number} options.minGames - Minimum games for opening analysis (default: 5)
   * @param {number} options.limit - Maximum openings to return
   * @param {string} options.startDate - Start date (YYYY-MM-DD)
   * @param {string} options.endDate - End date (YYYY-MM-DD)
   * @returns {Promise<Object>} Opening analysis
   */
  async getPlayerOpenings(playerId, options = {}) {
    const { minGames = 5, limit, startDate, endDate } = options;
    try {
      const params = {
        min_games: minGames,
      };

      // Only add optional parameters if they are valid
      if (limit) {
        params.limit = limit;
      }
      if (startDate && startDate.trim()) {
        params.start_date = startDate;
      }
      if (endDate && endDate.trim()) {
        params.end_date = endDate;
      }

      return await this.get(`/players/${playerId}/openings`, params);
    } catch (error) {
      console.error('Error fetching player openings:', error);
      throw new Error('Failed to fetch player openings');
    }
  }

  /**
   * Get detailed player statistics
   * @param {number} playerId - Player ID
   * @param {string} timePeriod - Time period filter (e.g., '1y', '6m', '3m', '1m')
   * @returns {Promise<Object>} Detailed statistics
   */
  async getDetailedStats(playerId, timePeriod) {
    try {
      const params = {};
      if (timePeriod) {
        params.time_period = timePeriod;
      }
      return await this.get(`/players/${playerId}/detailed-stats`, params);
    } catch (error) {
      console.error('Error fetching detailed stats:', error);
      throw new Error('Failed to fetch detailed statistics');
    }
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

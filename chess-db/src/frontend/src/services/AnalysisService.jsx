/**
 * Service for handling chess analysis API interactions.
 * Provides methods for fetching various types of analysis data.
 */

export class AnalysisService {
  constructor(baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000') {
    this.baseUrl = baseUrl;
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }

  async getCachedData(key, fetchFn) {
    const cached = this.cache.get(key);
    if (cached && (Date.now() - cached.timestamp < this.cacheTimeout)) {
      return cached.data;
    }

    const data = await fetchFn();
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
    return data;
  }

  async handleResponse(response) {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  /**
   * Fetches move count distribution data.
   * 
   * @returns {Promise<Array>} Move count distribution data
   */
  async getMoveCountDistribution() {
    return this.getCachedData('move-distribution', async () => {
      const response = await fetch(`${this.baseUrl}/analysis/move-counts`);
      return this.handleResponse(response);
    });
  }

  /**
   * Fetches database metrics and trends.
   * 
   * @param {string} timePeriod - Time period for metrics (1m, 3m, 6m, 1y)
   * @returns {Promise<Object>} Database metrics data
   */
  async getDatabaseMetrics(timePeriod = '1m') {
    const cacheKey = `db-metrics-${timePeriod}`;
    return this.getCachedData(cacheKey, async () => {
      const response = await fetch(
        `${this.baseUrl}/analysis/database-metrics?time_period=${timePeriod}`
      );
      return this.handleResponse(response);
    });
  }

  /**
   * Fetches opening analysis data for a specific player.
   * 
   * @param {number} playerId - The ID of the player to analyze
   * @param {Object} options - Query options
   * @param {number} [options.minGames=5] - Minimum games threshold
   * @param {string} [options.startDate] - Start date for analysis (YYYY-MM-DD)
   * @param {string} [options.endDate] - End date for analysis (YYYY-MM-DD)
   * @returns {Promise<Object>} Opening analysis data
   */
  async getPlayerOpeningAnalysis(playerId, { minGames = 5, startDate, endDate } = {}) {
    const cacheKey = `opening-analysis-${playerId}-${minGames}-${startDate}-${endDate}`;
    return this.getCachedData(cacheKey, async () => {
      const params = new URLSearchParams({
        min_games: minGames,
        ...(startDate && { start_date: startDate }),
        ...(endDate && { end_date: endDate })
      });
      const response = await fetch(
        `${this.baseUrl}/analysis/player/${playerId}/openings?${params}`
      );
      return this.handleResponse(response);
    });
  }

  /**
   * Fetches performance metrics for a player.
   * 
   * @param {number} playerId - The ID of the player to analyze
   * @param {Object} options - Query options
   * @param {string} [options.timeRange='monthly'] - Time grouping (daily, weekly, monthly, yearly)
   * @param {string} [options.startDate] - Start date (YYYY-MM-DD)
   * @param {string} [options.endDate] - End date (YYYY-MM-DD)
   * @returns {Promise<Object>} Player performance data
   */
  async getPlayerPerformance(playerId, { timeRange = 'monthly', startDate, endDate } = {}) {
    const cacheKey = `player-performance-${playerId}-${timeRange}-${startDate}-${endDate}`;
    return this.getCachedData(cacheKey, async () => {
      const params = new URLSearchParams({
        time_range: timeRange,
        ...(startDate && { start_date: startDate }),
        ...(endDate && { end_date: endDate })
      });
      const response = await fetch(
        `${this.baseUrl}/analysis/player/${playerId}/performance?${params}`
      );
      return this.handleResponse(response);
    });
  }

  /**
   * Searches for players by name.
   * 
   * @param {string} query - Search query
   * @param {number} [limit=10] - Maximum number of results
   * @returns {Promise<Array>} List of matching players
   */
  async searchPlayers(query, limit = 10) {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString()
    });
    const response = await fetch(
      `${this.baseUrl}/analysis/players/search?${params}`
    );
    return this.handleResponse(response);
  }
}
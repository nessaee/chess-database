import { BaseService } from './BaseService';
import { PlayerService } from './PlayerService';
import { GameService } from './GameService';

/**
 * Service for handling chess analysis API interactions.
 * Provides methods for fetching various types of analysis data.
 */
export class AnalysisService extends BaseService {
  constructor(baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000') {
    super(baseUrl);
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    this.playerService = new PlayerService(baseUrl);
    this.gameService = new GameService(baseUrl);
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
    return this.getCachedData('move-distribution', () => 
      this.get('/analysis/move-counts')
    );
  }

  /**
   * Fetches database metrics and trends.
   * 
   * @returns {Promise<Object>} Database metrics data
   */
  async getDatabaseMetrics() {
    return this.getCachedData('db-metrics', () => 
      this.get('/analysis/database-metrics')
    );
  }

  /**
   * Fetches opening analysis data for a specific player.
   * 
   * @param {string} playerName - The name of the player to analyze
   * @param {Object} options - Query options
   * @param {number} [options.minGames=20] - Minimum games threshold
   * @param {string} [options.startDate] - Start date for analysis (YYYY-MM-DD)
   * @param {string} [options.endDate] - End date for analysis (YYYY-MM-DD)
   * @returns {Promise<Object>} Opening analysis data
   */
  async getPlayerOpeningAnalysis(playerName, { minGames = 20, startDate, endDate } = {}) {
    if (!playerName) {
      throw new Error('Player name is required');
    }
    return this.get(`/analysis/players/${encodeURIComponent(playerName)}/openings`, {
      min_games: minGames.toString(),
      ...(startDate && { start_date: startDate }),
      ...(endDate && { end_date: endDate })
    });
  }

  // Delegate player-related methods to PlayerService
  searchPlayers(query, limit) {
    return this.playerService.searchPlayers(query, limit);
  }

  getPlayerPerformance(playerName, options) {
    return this.playerService.getPlayerPerformance(playerName, options);
  }

  // Delegate game-related methods to GameService
  getPlayerGames(playerName, options) {
    return this.gameService.getPlayerGames(playerName, options);
  }

  getGameStats() {
    return this.gameService.getGameStats();
  }
}
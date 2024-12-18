import { BaseService } from './BaseService';
import { API_ENDPOINTS, API_CONFIG, CACHE_TIMEOUTS } from './constants';

/**
 * Service for handling chess analysis-related API interactions.
 */
export class AnalysisService extends BaseService {
  constructor(baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000') {
    super(baseUrl);
    this.cache = new Map();
  }

  async getCachedData(key, fetchFn, timeout = CACHE_TIMEOUTS.SHORT) {
    const cached = this.cache.get(key);
    if (cached && (Date.now() - cached.timestamp < timeout)) {
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
   * Get analysis for a specific game position
   * 
   * @param {Object} options - Analysis options
   * @param {string} options.fen - FEN string of the position
   * @param {number} [options.depth=20] - Analysis depth
   * @param {number} [options.multiPv=3] - Number of variations to analyze
   * @returns {Promise<Object>} Position analysis
   */
  async analyzePosition({ fen, depth = 20, multiPv = 3 } = {}) {
    if (!fen) {
      throw new Error('FEN string is required');
    }

    return this.get(API_ENDPOINTS.ANALYSIS.POSITION, {
      fen,
      depth: Math.min(Math.max(1, depth), API_CONFIG.MAX_ANALYSIS_DEPTH),
      multi_pv: Math.min(Math.max(1, multiPv), API_CONFIG.MAX_VARIATIONS)
    });
  }

  /**
   * Get engine evaluation for a game
   * 
   * @param {number} gameId - Game ID
   * @param {Object} options - Analysis options
   * @param {number} [options.depth=20] - Analysis depth
   * @returns {Promise<Object>} Game analysis
   */
  async analyzeGame(gameId, { depth = 20 } = {}) {
    const cacheKey = `game_analysis_${gameId}_${depth}`;
    return this.getCachedData(
      cacheKey,
      () => this.get(API_ENDPOINTS.ANALYSIS.GAME(gameId), {
        depth: Math.min(Math.max(1, depth), API_CONFIG.MAX_ANALYSIS_DEPTH)
      }),
      CACHE_TIMEOUTS.LONG
    );
  }

  /**
   * Get opening statistics for a position
   * 
   * @param {string} fen - FEN string of the position
   * @returns {Promise<Object>} Opening statistics
   */
  async getOpeningStats(fen) {
    if (!fen) {
      throw new Error('FEN string is required');
    }

    const cacheKey = `opening_stats_${fen}`;
    return this.getCachedData(
      cacheKey,
      () => this.get(API_ENDPOINTS.ANALYSIS.OPENING_STATS, { fen }),
      CACHE_TIMEOUTS.MEDIUM
    );
  }

  /**
   * Get similar games for a position
   * 
   * @param {string} fen - FEN string of the position
   * @param {Object} options - Query options
   * @param {number} [options.limit=10] - Maximum number of games to return
   * @param {number} [options.minElo=2000] - Minimum player Elo rating
   * @returns {Promise<Array>} Similar games
   */
  async getSimilarGames(fen, { limit = 10, minElo = 2000 } = {}) {
    if (!fen) {
      throw new Error('FEN string is required');
    }

    return this.get(API_ENDPOINTS.ANALYSIS.SIMILAR_GAMES, {
      fen,
      limit: Math.min(Math.max(1, limit), API_CONFIG.MAX_LIMIT),
      min_elo: Math.max(0, minElo)
    });
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
   * @param {string} playerId - The ID of the player to analyze
   * @param {Object} options - Query options
   * @param {number} [options.minGames=20] - Minimum games threshold
   * @param {string} [options.startDate] - Start date for analysis (YYYY-MM-DD)
   * @param {string} [options.endDate] - End date for analysis (YYYY-MM-DD)
   * @returns {Promise<Object>} Opening analysis data
   */
  async getPlayerOpeningAnalysis(playerId, { minGames = 20, startDate, endDate } = {}) {
    if (!playerId) {
      throw new Error('Player ID is required');
    }
    return this.get(`/analysis/players/${encodeURIComponent(playerId)}/openings`, {
      min_games: minGames.toString(),
      ...(startDate && { start_date: startDate }),
      ...(endDate && { end_date: endDate })
    });
  }

  // Delegate player-related methods to PlayerService
  searchPlayers(query, limit) {
    return this.playerService.searchPlayers(query, limit);
  }

  getPlayerPerformance(playerId, options) {
    return this.playerService.getPlayerPerformance(playerId, options);
  }

  // Delegate game-related methods to GameService
  getPlayerGames(playerName, options) {
    return this.gameService.getPlayerGames(playerName, options);
  }

  getGameStats() {
    return this.gameService.getGameStats();
  }
}
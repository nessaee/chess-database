import { BaseService } from './BaseService';
import { API_ENDPOINTS, CACHE_TIMEOUTS } from './constants';

/**
 * Service for handling database metrics-related API interactions.
 */
class DatabaseMetricsService extends BaseService {
  /**
   * Fetches comprehensive database metrics including performance, health, and storage metrics
   * 
   * @returns {Promise<Object>} Database metrics data
   */
  async getDatabaseMetrics() {
    return this.getCachedData(
      'database-metrics',
      () => this.get(API_ENDPOINTS.DATABASE.METRICS),
      CACHE_TIMEOUTS.SHORT
    );
  }
}

// Export both the class and a singleton instance
export { DatabaseMetricsService };
export const databaseMetricsService = new DatabaseMetricsService();
export default databaseMetricsService;

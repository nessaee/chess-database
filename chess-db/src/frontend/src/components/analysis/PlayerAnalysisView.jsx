import React from 'react';
import OpeningAnalysisView from './OpeningAnalysisView';
import PlayerMetricsView from './PlayerMetricsView';
import DatabaseMetricsView from './DatabaseMetricsView';

/**
 * Player Analysis View Component
 * Displays player performance metrics and opening analysis
 */
export default function PlayerAnalysisView({ performanceData, openingAnalysis, databaseMetrics }) {
  return (
    <div className="space-y-6">
      <div className="space-y-8">
        {/* Performance Metrics */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Performance Metrics</h2>
          </div>
          <div className="p-4">
            <PlayerMetricsView performanceData={performanceData} />
          </div>
        </div>

        {/* Opening Analysis */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Opening Analysis</h2>
          </div>
          <div className="p-4">
            <OpeningAnalysisView data={openingAnalysis} />
          </div>
        </div>

      </div>
    </div>
  );
}

import React from 'react';
import { AlertCircle } from 'lucide-react';

export const LoadingState = () => (
  <div className="p-4 bg-white rounded-lg shadow animate-pulse">
    <div className="h-8 w-48 bg-gray-200 rounded mb-4"/>
    <div className="h-[400px] bg-gray-100 rounded flex items-center justify-center">
      <span className="text-gray-500">Loading analysis data...</span>
    </div>
  </div>
);

export const ErrorState = ({ error, onRetry }) => (
  <div className="p-6 bg-white rounded-lg shadow-lg border border-red-100">
    <div className="flex items-start space-x-4">
      <div className="flex-shrink-0">
        <AlertCircle className="h-6 w-6 text-red-500" />
      </div>
      <div className="flex-1 min-w-0">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Analysis Error
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          {error?.message || 'An unexpected error occurred while analyzing data'}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center px-4 py-2 bg-red-100 text-red-700 
                     rounded-md hover:bg-red-200 focus:outline-none focus:ring-2 
                     focus:ring-red-500 focus:ring-offset-2 transition-colors
                     text-sm font-medium"
          >
            Retry Analysis
          </button>
        )}
      </div>
    </div>
  </div>
);

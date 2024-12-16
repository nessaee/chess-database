// components/ErrorBoundary.jsx
import React from 'react';
import { AlertCircle } from 'lucide-react';

export class AnalysisErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Analysis Error:', error, errorInfo);
        // Here you could send to an error tracking service
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="p-6 bg-white rounded-lg shadow-lg border border-red-100">
                    <div className="flex items-start space-x-4">
                        <AlertCircle className="h-6 w-6 text-red-500" />
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900">
                                Analysis Error
                            </h2>
                            <p className="text-sm text-gray-600">
                                {this.state.error?.message || 'An unexpected error occurred'}
                            </p>
                            <button
                                onClick={() => this.setState({ hasError: false, error: null })}
                                className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-md"
                            >
                                Try Again
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
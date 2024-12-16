import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { AnalysisService } from '../../services/AnalysisService';

// Create a single instance of the service
const analysisService = new AnalysisService();

// Helper function to get color based on win rate
const getWinRateColor = (rate) => {
  if (rate >= 60) return 'text-emerald-600';
  if (rate >= 50) return 'text-blue-600';
  if (rate >= 40) return 'text-amber-600';
  return 'text-red-600';
};

// Helper function to format win rate
const formatWinRate = (rate) => `${rate.toFixed(1)}%`;

const OpeningRow = ({ opening }) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <tr className="border-b bg-white hover:bg-gray-50">
        <td className="p-4">
          <button
            onClick={() => setOpen(!open)}
            className="p-1 hover:bg-gray-100 rounded-full"
            aria-label="toggle opening details"
          >
            {open ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
        </td>
        <td className="p-4">{opening.name}</td>
        <td className="p-4 text-right">{opening.games_played}</td>
        <td className="p-4 text-right">{opening.white_games}</td>
        <td className="p-4 text-right">{opening.black_games}</td>
        <td className={`p-4 text-right ${getWinRateColor(opening.win_rate)}`}>
          {formatWinRate(opening.win_rate)}
        </td>
      </tr>
      {open && (
        <tr className="border-b bg-gray-50">
          <td colSpan="6" className="p-4">
            <div className="space-y-2">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <span className="text-gray-500">Wins:</span>{' '}
                  <span className="font-medium">{opening.wins}</span>
                </div>
                <div>
                  <span className="text-gray-500">Draws:</span>{' '}
                  <span className="font-medium">{opening.draws}</span>
                </div>
                <div>
                  <span className="text-gray-500">Losses:</span>{' '}
                  <span className="font-medium">{opening.losses}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-500">Games as White:</span>{' '}
                  <span className="font-medium">{opening.white_games}</span>
                </div>
                <div>
                  <span className="text-gray-500">Games as Black:</span>{' '}
                  <span className="font-medium">{opening.black_games}</span>
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

const OpeningAnalysisView = ({ playerId }) => {
  const [openings, setOpenings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchOpenings = async () => {
      try {
        setLoading(true);
        const data = await analysisService.getPlayerOpeningAnalysis(playerId);
        setOpenings(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (playerId) {
      fetchOpenings();
    }
  }, [playerId]);

  if (loading) {
    return <div className="text-center p-4">Loading opening analysis...</div>;
  }

  if (error) {
    return <div className="text-red-600 p-4">Error: {error}</div>;
  }

  if (!openings || !openings.openings || openings.openings.length === 0) {
    return <div className="text-gray-600 p-4">No opening data available.</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="p-4 w-10"></th>
            <th scope="col" className="p-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Opening
            </th>
            <th scope="col" className="p-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Games
            </th>
            <th scope="col" className="p-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              As White
            </th>
            <th scope="col" className="p-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              As Black
            </th>
            <th scope="col" className="p-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Win Rate
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {openings.openings.map((opening, index) => (
            <OpeningRow key={opening.name} opening={opening} />
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default OpeningAnalysisView;
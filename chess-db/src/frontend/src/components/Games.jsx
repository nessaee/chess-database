import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  CircularProgress,
  Alert,
  Box
} from '@mui/material';
import GameSearch from './GameSearch';
import GameList from './GameList';
import { GameService } from '../services/GameService';

const gameService = new GameService();

const Games = () => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadGames = async (searchParams = {}) => {
    setLoading(true);
    setError(null);
    try {
      const gamesData = await gameService.getRecentGames(searchParams);
      setGames(gamesData);
    } catch (err) {
      setError(err.message || 'Failed to load games');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGames();
  }, []);

  const handleSearch = async (searchParams) => {
    await loadGames(searchParams);
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Chess Games
        </Typography>
        
        <GameSearch onSearch={handleSearch} />

        {error && (
          <Alert severity="error" sx={{ my: 2 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <GameList games={games} />
        )}
      </Box>
    </Container>
  );
};

export default Games;

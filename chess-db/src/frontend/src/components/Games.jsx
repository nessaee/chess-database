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
import { fetchGames } from '../services/api';

const Games = () => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (searchParams) => {
    try {
      setLoading(true);
      setError(null);

      // Build query string from search params
      const params = new URLSearchParams();
      if (searchParams.player_name) {
        params.append('player_name', searchParams.player_name);
      }
      if (searchParams.start_date) {
        params.append('start_date', searchParams.start_date);
      }
      if (searchParams.end_date) {
        params.append('end_date', searchParams.end_date);
      }
      if (searchParams.only_dated) {
        params.append('only_dated', 'true');
      }

      const response = await fetch(`/games?${params.toString()}`);
      if (!response.ok) {
        throw new Error('Failed to fetch games');
      }

      const data = await response.json();
      setGames(data);
    } catch (err) {
      console.error('Error fetching games:', err);
      setError('Failed to load games. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" component="h1" gutterBottom>
        Chess Games
      </Typography>

      <GameSearch onSearch={handleSearch} />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : (
        <GameList games={games} />
      )}
    </Container>
  );
};

export default Games;

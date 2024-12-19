# API Reference

## Base URL
All endpoints are prefixed with `/api`

## Endpoints

### Games (`/games`)
#### GET /games
- Query Parameters:
  - `limit`: Maximum number of games to return
  - `offset`: Number of games to skip
  - `player`: Filter by player name
  - `date_from`: Filter games after date
  - `date_to`: Filter games before date

#### POST /games
- Creates a new game record
- Request Body: Game details in JSON format

#### GET /games/{game_id}
- Retrieves specific game details

### Players (`/players`)
#### GET /players
- Query Parameters:
  - `limit`: Maximum number of players to return
  - `offset`: Number of players to skip
  - `rating_min`: Minimum rating filter
  - `rating_max`: Maximum rating filter

#### POST /players
- Creates a new player profile
- Request Body: Player details in JSON format

### Analysis (`/analysis`)
#### GET /analysis/game/{game_id}
- Retrieves analysis for specific game

#### POST /analysis/game/{game_id}
- Submits new analysis for a game
- Request Body: Analysis details

### Database (`/database`)
#### GET /database/health
- Returns database health status

#### GET /database/stats
- Returns database statistics

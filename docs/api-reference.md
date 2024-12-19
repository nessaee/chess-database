---
layout: default
title: API Reference
description: Complete reference for the Chess Database API endpoints
---
<script type="module">
	import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
	mermaid.initialize({
		startOnLoad: true,
		theme: 'light'
	});
</script>
# API Reference

[← Documentation Home](index.md) | [System Architecture](architecture.md)

## Quick Links

- [Games API](#games-api)
- [Players API](#players-api)
- [Analysis API](#analysis-api)
- [Database API](#database-api)

## API Overview

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    subgraph API["API Layer"]
        GAMES["/api/games"]
        PLAYERS["/api/players"]
        ANALYSIS["/api/analysis"]
        DATABASE["/api/database"]
    end
    
    subgraph Methods["HTTP Methods"]
        GET[["GET"]]
    end
    
    GET --> GAMES & PLAYERS & ANALYSIS & DATABASE
    
    classDef endpoint fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef method fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    
    class GAMES,PLAYERS,ANALYSIS,DATABASE endpoint
    class GET method
</pre>
</div>

## Request Flow

<div class="mermaid-wrapper">
<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant M as Middleware
    participant H as Handler
    participant D as Database
    participant Cache as Cache
    
    C->>M: Request
    M->>Cache: Check Cache
    
    alt Cache Hit
        Cache-->>C: Cached Response
    else Cache Miss
        M->>H: Process
        H->>D: Query
        D-->>H: Result
        H->>Cache: Store
        H-->>C: Response
    end
    
    Note over M: Performance Monitoring
</pre>
</div>

## Games API

### Endpoints

#### GET /api/games
List chess games with filtering options.

**Parameters:**
- `limit` (int, default: 10): Number of games to return
- `offset` (int, default: 0): Number of games to skip
- `player` (string, optional): Filter by player name
- `date_from` (date, optional): Filter games after this date
- `date_to` (date, optional): Filter games before this date
- `move_notation` (string, default: 'san'): Move notation format ('uci' or 'san')

#### GET /api/games/count
Get total number of games in the database.

#### GET /api/games/recent
Get recent games.

**Parameters:**
- `limit` (int, default: 10): Maximum number of games to return
- `move_notation` (string, default: 'san'): Move notation format

#### GET /api/games/stats
Get game statistics.

#### GET /api/games/player/{playerName}
Get games for a specific player.

**Parameters:**
- `start_date` (date, optional): Start date (YYYY-MM-DD)
- `end_date` (date, optional): End date (YYYY-MM-DD)
- `only_dated` (boolean, default: false): Only include games with dates
- `limit` (int, default: 50): Maximum number of games to return
- `move_notation` (string, default: 'san'): Move notation format

#### GET /api/games/players/suggest
Get player name suggestions for autocomplete.

#### GET /api/games/{gameId}
Get detailed information about a specific game.

## Players API

### Endpoints

#### GET /api/players
List chess players with filtering options.

**Parameters:**
- `limit` (int, default: 10): Number of players to return
- `offset` (int, default: 0): Number of players to skip
- `name` (string, optional): Filter by player name

#### GET /api/players/search
Search for players.

**Parameters:**
- `query` (string): Search query
- `limit` (int, default: 10): Maximum number of results

#### GET /api/players/{playerId}
Get basic player information.

#### GET /api/players/{playerId}/performance
Get detailed player performance statistics.

#### GET /api/players/{playerId}/detailed-stats
Get comprehensive player statistics.

#### GET /api/players/{playerId}/openings
Get player's opening repertoire statistics.

## Analysis API

### Endpoints

#### GET /api/analysis/position
Analyze a specific chess position.

**Parameters:**
- `fen` (string, required): FEN string of the position
- `depth` (int, default: 20): Analysis depth
- `multi_pv` (int, default: 3): Number of variations to analyze

#### GET /api/analysis/game/{gameId}
Get analysis for a specific game.

#### GET /api/analysis/opening-stats
Get general opening statistics.

#### GET /api/analysis/similar-games
Find games with similar positions or patterns.

#### GET /api/analysis/move-counts
Get distribution of move counts across games.

#### GET /api/analysis/popular-openings
Get statistics for popular chess openings.

**Parameters:**
- `start_date` (date, optional): Start date for analysis
- `end_date` (date, optional): End date for analysis
- `min_games` (int, default: 100): Minimum games threshold
- `limit` (int, default: 10): Number of openings to return

## Database API

### Endpoints

#### GET /api/database/metrics
Get comprehensive database metrics.

**Response:**
```json
{
  "total_games": 0,
  "total_players": 0,
  "avg_moves_per_game": 0,
  "avg_rating": 0,
  "date_range": {
    "earliest": "string",
    "latest": "string"
  }
}
```

## Caching

The API implements caching with the following timeouts:
- Short: 1 minute
- Medium: 5 minutes
- Long: 15 minutes
- Very Long: 1 hour

Cached endpoints are marked with appropriate cache control headers.

## Error Handling

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    subgraph Errors["Error Types"]
        V[Validation]
        D[Database]
        S[System]
    end
    
    subgraph Handler["Error Handler"]
        M[Middleware]
        L[Logger]
        R[Response]
    end
    
    V & D & S --> M
    M --> L
    M --> R
    
    classDef error fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    classDef handler fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    
    class V,D,S error
    class M,L,R handler
</pre>
</div>

## Rate Limiting

<div class="mermaid-wrapper">
<pre class="mermaid">
graph LR
    R[Request] --> C[Check Rate]
    C --> L[Log Request]
    
    C -->|Under Limit| H[Handler]
    C -->|Over Limit| E[429 Error]
    
    classDef flow fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    class R,C,L,H,E flow
</pre>
</div>

## Health Check

### GET /health
Check API and database health.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "string"
}
```

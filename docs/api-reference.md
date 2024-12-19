---
layout: default
title: API Reference
description: Complete reference for the Chess Database API endpoints
---

# API Reference

[← Documentation Home](README.md) | [System Architecture](architecture.md)

<script type="module">
	import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
	mermaid.initialize({
		startOnLoad: true,
		theme: 'light'
	});
</script>

## Quick Links

- [Authentication](#authentication)
- [Game Operations](#games-api)
- [Player Operations](#players-api)
- [Analysis Operations](#analysis-api)

## API Overview

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    subgraph API["API Layer"]
        GAMES["/games"]
        PLAYERS["/players"]
        ANALYSIS["/analysis"]
        METRICS["/metrics"]
    end
    
    subgraph Methods["HTTP Methods"]
        GET[["GET"]]
        POST[["POST"]]
        PUT[["PUT"]]
        DELETE[["DELETE"]]
    end
    
    GET --> GAMES & PLAYERS & ANALYSIS & METRICS
    POST --> GAMES & ANALYSIS
    PUT --> GAMES & PLAYERS
    DELETE --> GAMES
    
    classDef endpoint fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef method fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    
    class GAMES,PLAYERS,ANALYSIS,METRICS endpoint
    class GET,POST,PUT,DELETE method
</pre>
</div>

## Authentication Flow

<div class="mermaid-wrapper">
<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant A as Auth
    participant API as API
    participant D as DB
    
    C->>A: Request Token
    A->>D: Validate
    D-->>A: Result
    
    alt is valid
        A-->>C: JWT Token
        C->>API: Request + Token
        API->>A: Verify Token
        A-->>API: Valid
        API-->>C: Response
    else is invalid
        A-->>C: Error
    end
</pre>
</div>

## Request Flow

<div class="mermaid-wrapper">
<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant M as Middleware
    participant V as Validator
    participant H as Handler
    participant D as DB
    
    C->>M: Request
    M->>V: Validate
    V->>H: Process
    H->>D: Query
    D-->>H: Result
    H-->>C: Response
</pre>
</div>

## Error Handling

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    subgraph Errors["Error Types"]
        V[Validation]
        A[Auth]
        D[Database]
        S[System]
    end
    
    subgraph Handler["Error Handler"]
        M[Middleware]
        L[Logger]
        R[Response]
    end
    
    V & A & D & S --> M
    M --> L
    M --> R
    
    classDef error fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    classDef handler fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    
    class V,A,D,S error
    class M,L,R handler
</pre>
</div>

## Rate Limiting

<div class="mermaid-wrapper">
<pre class="mermaid">
graph LR
    R[Request] --> C[Check Limit]
    C --> S[Store Count]
    P[Policy] --> C
    
    C -->|Allow| H[Handler]
    C -->|Block| E[Error]
    
    classDef flow fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    class R,C,S,P,H,E flow
</pre>
</div>

## API Components

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    subgraph Core["Core API"]
        G["/games"]
        P["/players"]
        A["/analysis"]
    end
    
    subgraph Auth["Auth"]
        T["/token"]
        R["/refresh"]
    end
    
    subgraph Admin["Admin"]
        U["/users"]
        C["/config"]
    end
    
    Client --> T
    T --> G & P & A
    T --> U & C
    
    classDef core fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef auth fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef admin fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    
    class G,P,A core
    class T,R auth
    class U,C admin
</pre>
</div>

## Overview

The Chess Database API is built using FastAPI and provides endpoints for managing chess games, players, and analysis. The API is versioned and follows RESTful principles.

## Base URL

```
https://api.chess-database.org/v1
```

## Authentication

All API requests require authentication using an API key. Include the key in the request header:

```http
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### Games API (`/api/games`)

#### List Games
- `GET /api/games`
  - Query parameters:
    - `limit`: Maximum number of games to return
    - `offset`: Number of games to skip
    - `player`: Filter by player name
    - `date_from`: Filter games after date
    - `date_to`: Filter games before date

#### Get Game
- `GET /api/games/{game_id}`
  - Returns detailed game information including moves and analysis

#### Import Game
- `POST /api/games/import`
  - Body: PGN format chess game

### Players API (`/api/players`)

#### List Players
- `GET /api/players`
  - Query parameters:
    - `limit`: Maximum number of players to return
    - `offset`: Number of players to skip
    - `name`: Filter by player name

#### Get Player
- `GET /api/players/{player_id}`
  - Returns player statistics and game history

#### Search Players
- `GET /api/players/search`
  - Query parameters:
    - `query`: Search term
    - `limit`: Maximum results

### Analysis API (`/api/analysis`)

#### Analyze Position
- `POST /api/analysis/position`
  - Body: FEN position string
  - Returns position evaluation and suggested moves

#### Game Analysis
- `POST /api/analysis/game`
  - Body: Game ID or PGN
  - Returns full game analysis

### Database API (`/api/database`)

#### Database Stats
- `GET /api/database/stats`
  - Returns database statistics

#### Database Maintenance
- `POST /api/database/maintenance`
  - Performs database optimization tasks

## Endpoint Structure

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    subgraph "Games API"
        G["/games"]
        GID["/games/{id}"]
        GP["/games/player/{name}"]
        GR["/games/recent"]
    end
    
    subgraph "Players API"
        P["/players"]
        PID["/players/{id}"]
        PS["/players/search"]
        PP["/players/{id}/performance"]
    end
    
    subgraph "Analysis API"
        A["/analysis"]
        AG["/analysis/game/{id}"]
        AP["/analysis/position"]
        AO["/analysis/opening"]
    end
    
    G --> GID
    G --> GP
    G --> GR
    
    P --> PID
    P --> PS
    P --> PP
    
    A --> AG
    A --> AP
    A --> AO
    
    classDef endpoint fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    
    class G,GID,GP,GR,P,PID,PS,PP,A,AG,AP,AO endpoint;
    
    style "Games API" fill:#f5f5f5,stroke:#333,stroke-width:2px;
    style "Players API" fill:#f5f5f5,stroke:#333,stroke-width:2px;
    style "Analysis API" fill:#f5f5f5,stroke:#333,stroke-width:2px;
</pre>
</div>

## Request/Response Flow

<div class="mermaid-wrapper">
<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant M as Middleware
    participant V as Validator
    participant H as Handler
    participant D as Database
    
    C->>M: HTTP Request
    M->>V: Validate Request
    V->>H: Process Request
    H->>D: Database Query
    D-->>H: Query Result
    H-->>M: Format Response
    M-->>C: HTTP Response
    
    classDef client fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef middleware fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef validator fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef handler fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef database fill:#f5f5f5,stroke:#333,stroke-width:2px;
    
    class C client;
    class M middleware;
    class V validator;
    class H handler;
    class D database;
</pre>
</div>

## Authentication Flow

<div class="mermaid-wrapper">
<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant A as Auth
    participant API as API
    participant D as Database
    
    C->>A: Authentication Request
    A->>D: Validate Credentials
    D-->>A: Validation Result
    
    alt Valid Credentials
        A-->>C: JWT Token
        C->>API: API Request + Token
        API->>A: Validate Token
        A-->>API: Token Valid
        API-->>C: API Response
    else Invalid Credentials
        A-->>C: Auth Error
    end
    
    classDef client fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef auth fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef api fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef database fill:#f5f5f5,stroke:#333,stroke-width:2px;
    
    class C client;
    class A auth;
    class API api;
    class D database;
</pre>
</div>

## Error Handling

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    subgraph "Error Types"
        VAL["Validation Error"]
        AUTH["Auth Error"]
        DB["Database Error"]
        SYS["System Error"]
    end
    
    subgraph "Error Handling"
        MID["Middleware"]
        LOG["Logger"]
        RESP["Response"]
    end
    
    VAL --> MID
    AUTH --> MID
    DB --> MID
    SYS --> MID
    
    MID --> LOG
    MID --> RESP
    
    classDef error fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef middleware fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef logger fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef response fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    
    class VAL,AUTH,DB,SYS error;
    class MID middleware;
    class LOG logger;
    class RESP response;
</pre>
</div>

## Rate Limiting

<div class="mermaid-wrapper">
<pre class="mermaid">
graph LR
    subgraph "Rate Limit Components"
        CHECK["Limit Checker"]
        STORE["Rate Store"]
        POLICY["Rate Policy"]
    end
    
    Request --> CHECK
    CHECK --> STORE
    POLICY --> CHECK
    
    CHECK -->|Allow| Handler
    CHECK -->|Block| Error
    
    classDef component fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    
    class CHECK,STORE,POLICY component;
</pre>
</div>

## Response Format

All API responses follow this format:

```json
{
  "status": "success|error",
  "data": {
    // Response data
  },
  "message": "Optional message"
}
```

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 404: Not Found
- 500: Server Error

Error responses include detailed messages:

```json
{
  "status": "error",
  "message": "Detailed error message",
  "code": "ERROR_CODE"
}
```

## Rate Limiting

API requests are limited to ensure system stability. Current limits:
- 100 requests per minute per IP
- 1000 requests per hour per IP

## Metrics and Monitoring

The API includes middleware for:
- Performance monitoring
- Request metrics
- Error tracking

## API Versioning

The current API version is specified in the configuration. Version information is included in the API path when needed.

## Endpoint Details

### Games API

<div class="mermaid-wrapper">
<pre class="mermaid">
classDiagram
    class GameEndpoint {
        +GET /games
        +GET /games/{id}
        +GET /games/player/{name}
        +POST /games
        +PUT /games/{id}
        +DELETE /games/{id}
    }
    
    class GameResponse {
        +id: int
        +white_player: Player
        +black_player: Player
        +result: string
        +moves: string
        +date: date
    }
    
    GameEndpoint -- GameResponse
    
    classDef endpoint fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef response fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    
    class GameEndpoint endpoint;
    class GameResponse response;
</pre>
</div>

### Players API

<div class="mermaid-wrapper">
<pre class="mermaid">
classDiagram
    class PlayerEndpoint {
        +GET /players
        +GET /players/{id}
        +GET /players/search
        +GET /players/{id}/performance
    }
    
    class PlayerResponse {
        +id: int
        +name: string
        +rating: int
        +games: Game[]
        +statistics: Stats
    }
    
    PlayerEndpoint -- PlayerResponse
    
    classDef endpoint fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef response fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    
    class PlayerEndpoint endpoint;
    class PlayerResponse response;
</pre>
</div>

### Analysis API

<div class="mermaid-wrapper">
<pre class="mermaid">
classDiagram
    class AnalysisEndpoint {
        +GET /analysis/game/{id}
        +GET /analysis/position
        +GET /analysis/opening
    }
    
    class AnalysisResponse {
        +score: float
        +best_move: string
        +variation: string[]
        +statistics: Stats
    }
    
    AnalysisEndpoint -- AnalysisResponse
    
    classDef endpoint fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef response fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    
    class AnalysisEndpoint endpoint;
    class AnalysisResponse response;
</pre>
</div>

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    %% API Components
    subgraph Endpoints["API Endpoints"]
        GAMES["/games"]
        PLAYERS["/players"]
        ANALYSIS["/analysis"]
        METRICS["/metrics"]
    end
    
    subgraph Auth["Authentication"]
        AUTH["/auth"]
        TOKEN["/token"]
        REFRESH["/refresh"]
    end
    
    subgraph Admin["Admin"]
        USERS["/users"]
        ROLES["/roles"]
        CONFIG["/config"]
    end
    
    %% Relationships
    CLIENT(("Client")) --> AUTH
    AUTH --> TOKEN
    TOKEN --> REFRESH
    
    TOKEN --> GAMES
    TOKEN --> PLAYERS
    TOKEN --> ANALYSIS
    TOKEN --> METRICS
    
    TOKEN --> USERS
    TOKEN --> ROLES
    TOKEN --> CONFIG
    
    %% Styling
    classDef endpoint fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef auth fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef admin fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef client fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    
    class GAMES,PLAYERS,ANALYSIS,METRICS endpoint;
    class AUTH,TOKEN,REFRESH auth;
    class USERS,ROLES,CONFIG admin;
    class CLIENT client;
    
    %% Group Styling
    style Endpoints fill:#f5f5f5,stroke:#333,stroke-width:2px;
    style Auth fill:#f5f5f5,stroke:#333,stroke-width:2px;
    style Admin fill:#f5f5f5,stroke:#333,stroke-width:2px;
</pre>
</div>

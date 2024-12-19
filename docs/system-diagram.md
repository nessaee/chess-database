# Interactive System Diagram

[← Documentation Home](../index.md) | [Design Overview](README.md) | [API Reference](backend/api.md)

## Navigation
- [Overview](#overview)
- [High-Level Architecture](#high-level-architecture)
- [Component Details](#component-details)
  - [Frontend Layer](#frontend-layer)
  - [API Layer](#api-layer)
  - [Repository Layer](#repository-layer)
- [Usage Guide](#usage-guide)

## Overview
This document provides an interactive system diagram of the Chess Database System. Click on any component to explore its details.

## High-Level Architecture
```mermaid
graph TB
    %% Main Components
    Client[Client Layer]
    Frontend[Frontend Layer]
    API[API Layer]
    Repository[Repository Layer]
    DB[(Database Layer)]
    
    %% Frontend Components
    subgraph Frontend[Frontend Layer]
        UI[UI Components]
        State[State Management]
        Services[Frontend Services]
    end
    
    %% API Components
    subgraph API[API Layer]
        Routes[API Routes]
        Middleware[Middleware Stack]
        Validation[Request Validation]
    end
    
    %% Repository Components
    subgraph Repository[Repository Layer]
        GameRepo[Game Repository]
        PlayerRepo[Player Repository]
        AnalysisRepo[Analysis Repository]
        OpeningRepo[Opening Repository]
    end
    
    %% Database Components
    subgraph DB[Database Layer]
        Models[Data Models]
        Cache[Cache Layer]
        Migrations[Schema Migrations]
    end
    
    %% Connections
    Client --> Frontend
    Frontend --> API
    API --> Repository
    Repository --> DB
    
    %% Click Actions
    click Frontend "frontend/components.md" "View Frontend Documentation"
    click API "backend/api.md" "View API Documentation"
    click Repository "backend/repository.md" "View Repository Documentation"
    click DB "backend/models.md" "View Database Documentation"
```

## Component Details

### Frontend Layer
```mermaid
graph TB
    %% UI Components
    subgraph UI[UI Components]
        Games[Chess Games Viewer]
        Analysis[Analysis Interface]
        Players[Player Management]
    end
    
    %% State Management
    subgraph State[State Management]
        GameState[Game State]
        AnalysisState[Analysis State]
        UIState[UI State]
    end
    
    %% Services
    subgraph Services[Frontend Services]
        GameService[Game Service]
        AnalysisService[Analysis Service]
        PlayerService[Player Service]
    end
    
    %% Connections
    UI --> State
    State --> Services
    Services --> API
    
    %% Click Actions
    click Games "frontend/components.md#chessgamesviewer" "View Games Viewer Documentation"
    click Analysis "frontend/components.md#chessanalysis" "View Analysis Documentation"
    click Players "frontend/components.md#playersearch" "View Player Management Documentation"
```

### API Layer
```mermaid
graph LR
    %% API Routes
    subgraph Routes[API Routes]
        GameRoutes[Game Routes]
        PlayerRoutes[Player Routes]
        AnalysisRoutes[Analysis Routes]
    end
    
    %% Middleware
    subgraph Middleware[Middleware Stack]
        Auth[Authentication]
        Metrics[Metrics Collection]
        Cache[Caching]
    end
    
    %% Validation
    subgraph Validation[Request Validation]
        Schema[Schema Validation]
        Business[Business Rules]
    end
    
    %% Connections
    Routes --> Middleware
    Middleware --> Validation
    Validation --> Repository
    
    %% Click Actions
    click GameRoutes "backend/api.md#game-operations" "View Game API Documentation"
    click PlayerRoutes "backend/api.md#player-operations" "View Player API Documentation"
    click AnalysisRoutes "backend/api.md#analysis-operations" "View Analysis API Documentation"
```

### Repository Layer
```mermaid
graph TB
    %% Repositories
    subgraph Repositories[Domain Repositories]
        Game[Game Repository]
        Player[Player Repository]
        Analysis[Analysis Repository]
        Opening[Opening Repository]
    end
    
    %% Common Components
    subgraph Common[Common Components]
        Error[Error Handling]
        Validation[Data Validation]
        Utils[Utilities]
    end
    
    %% Database Access
    subgraph Access[Database Access]
        Models[Data Models]
        Queries[Query Builder]
        Cache[Cache Layer]
    end
    
    %% Connections
    Repositories --> Common
    Common --> Access
    Access --> DB
    
    %% Click Actions
    click Game "backend/repository.md#game-repository" "View Game Repository Documentation"
    click Player "backend/repository.md#player-repository" "View Player Repository Documentation"
    click Analysis "backend/repository.md#analysis-repository" "View Analysis Repository Documentation"
```

## Usage Guide

### Navigation
1. Click on any component in the diagrams to view its detailed documentation
2. Use the layer diagrams to understand component relationships
3. Follow the connections to trace data flow

### Component Types
- **Boxes**: Represent system components or modules
- **Subgraphs**: Group related components
- **Arrows**: Show data flow and dependencies

### Documentation Links
- Each component links to its detailed documentation
- Links are context-sensitive to the specific component
- Documentation includes implementation details and examples

## Implementation Notes

### Adding New Components
1. Update relevant diagram section
2. Add component documentation
3. Link component in diagram
4. Update relationships

### Modifying Components
1. Update component documentation
2. Reflect changes in diagram
3. Update affected relationships
4. Verify documentation links

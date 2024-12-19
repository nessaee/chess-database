---
layout: default
title: Chess Database Documentation
description: A powerful system for analyzing chess games and tracking player statistics
nav_order: 1
---
<script type="module">
	import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
	mermaid.initialize({
		startOnLoad: true,
		theme: 'light'
	});
</script>
# Chess Database Documentation

{: .fs-9 }
Welcome to the Chess Database documentation.

{: .fs-6 .fw-300 }
A comprehensive guide to the Chess Database system architecture, implementation, and API.

[Get Started](guides/setup.md){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View Demo](demos.md){: .btn .btn-blue .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View on GitHub](https://github.com/nessaee/chess-database){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## Getting Started
1. [Setup Guide](guides/setup.md)
2. [Development Guide](guides/development.md)

## Architecture
1. [System Overview](architecture.md)
2. [System Diagram](system-diagram.md)

## Backend
1. [Database Design](backend/database.md)
   - Entity Relationships
   - Table Partitioning
   - Materialized Views
2. [Move Encoding](backend/encoding.md)
   - Compression Algorithm
   - Performance Metrics
3. [Data Processing](backend/pipelines.md)
   - Game Pipeline
   - Opening Pipeline
   - Error Handling
4. [API Implementation](backend/api.md)
   - FastAPI Setup
   - Endpoint Design
   - Error Handling
5. [Data Models](backend/models.md)
   - Schema Definitions
   - Validation Rules
6. [Repository Layer](backend/repository.md)
   - Data Access
   - Query Optimization

## Frontend
1. [React Components](frontend/components.md)
   - Game Viewer
   - Analysis Board
   - Statistics Dashboard

## API Documentation
1. [REST API](api-reference.md)
   - Endpoints Overview
   - Request/Response Format
   - Authentication

## Performance
1. [Database Optimizations](optimizations.md)
   - Indexing Strategy
   - Query Performance
   - Cache Management
2. [Metrics & Monitoring](backend/metrics.md)
   - System Metrics
   - API Performance
   - Resource Usage

## Development
1. [Development Setup](guides/development.md)
   - Local Environment
   - Testing Tools
   - Debug Configuration

## System Architecture

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    %% Frontend Layer
    subgraph Frontend["Frontend Layer"]
        UI[React UI]
        BOARD[Game View]
        STATS[Analysis View]
    end
    
    %% API Layer
    subgraph API["API Layer"]
        FASTAPI[FastAPI Server]
        METRICS[Performance Metrics]
        SERVICES[Game Services]
    end
    
    %% Data Layer
    subgraph Data["Data Layer"]
        PG[(PostgreSQL)]
        VIEWS[Materialized Views]
        PARTITIONS[Partitioned Tables]
    end
    
    %% Relationships
    UI --> BOARD
    UI --> STATS
    BOARD --> FASTAPI
    STATS --> FASTAPI
    
    FASTAPI --> METRICS
    FASTAPI --> SERVICES
    
    SERVICES --> PG
    SERVICES --> VIEWS
    PG --> PARTITIONS
    
    %% Styling
    classDef frontend fill:#61DAFB,stroke:#333,stroke-width:2px;
    classDef api fill:#009688,stroke:#333,stroke-width:2px;
    classDef data fill:#336791,stroke:#333,stroke-width:2px;
    
    class UI,BOARD,STATS frontend;
    class FASTAPI,METRICS,SERVICES api;
    class PG,VIEWS,PARTITIONS data;
</pre>
</div>

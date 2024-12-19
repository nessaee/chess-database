---
layout: default
title: Chess Database Documentation
description: A powerful system for analyzing chess games and tracking player statistics
---

# Chess Database Documentation

<script type="module">
	import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
	mermaid.initialize({
		startOnLoad: true,
		theme: 'light'
	});
</script>

The Chess Database is a powerful system for analyzing chess games and tracking player statistics. This documentation will help you understand, use, and contribute to the project.

{: .fs-6 .fw-300 }
Built with modern technologies and designed for scalability.

[Get Started](guides/setup.md){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View on GitHub](https://github.com/nessaee/chess-database){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## Quick Start

1. [Setup your environment](guides/setup.md)
2. [Learn the architecture](architecture.md)
3. [Explore the API](api-reference.md)
4. [Start developing](guides/development.md)

## System Overview

The Chess Database is a full-stack application built with modern technologies:

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    %% System Overview
    subgraph Frontend["Frontend Layer"]
        UI["User Interface"]
        STATE["State Management"]
        SERVICES["API Services"]
    end
    
    subgraph Backend["Backend Layer"]
        API["API Gateway"]
        AUTH["Authentication"]
        HANDLERS["Request Handlers"]
    end
    
    subgraph Data["Data Layer"]
        CACHE["Redis Cache"]
        DB["PostgreSQL"]
        MODELS["Data Models"]
    end
    
    %% Relationships
    UI --> STATE
    STATE --> SERVICES
    SERVICES --> API
    
    API --> AUTH
    AUTH --> HANDLERS
    HANDLERS --> CACHE
    HANDLERS --> DB
    
    DB --> MODELS
    MODELS --> HANDLERS
    CACHE --> HANDLERS
    
    %% Styling
    classDef frontend fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef backend fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef data fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    
    class UI,STATE,SERVICES frontend;
    class API,AUTH,HANDLERS backend;
    class CACHE,DB,MODELS data;
    
    %% Group Styling
    style Frontend fill:#f5f5f5,stroke:#333,stroke-width:2px;
    style Backend fill:#f5f5f5,stroke:#333,stroke-width:2px;
    style Data fill:#f5f5f5,stroke:#333,stroke-width:2px;
</pre>
</div>

## Key Features

{: .highlight }
> - **Interactive Game Analysis**: Analyze games move by move with engine evaluation
> - **Player Statistics**: Track player performance and progress over time
> - **Opening Theory**: Study and explore chess openings with statistical insights
> - **Data Import/Export**: Support for PGN import and various export formats

## Documentation Structure

The documentation is organized into several key sections:

### Core Concepts
- [Architecture Overview](architecture.md)
- [Data Models](models.md)
- [API Reference](api-reference.md)

### Development
- [Setup Guide](guides/setup.md): Instructions for setting up the development environment
- [Development Guide](guides/development.md): Guidelines for development
- [Deployment Guide](deployment.md)

### Components
- [Frontend Components](frontend/components.md)
- [Backend Services](backend/api.md)
- [Database Schema](backend/models.md)

## Contributing

We welcome contributions! See our [Development Guide](guides/development.md) to get started.

{: .warning }
> Please read our contribution guidelines before submitting changes.

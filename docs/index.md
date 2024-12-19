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
A high-performance chess database for game analysis and player statistics.

{: .fs-6 .fw-300 }
Built with modern technologies and optimized for performance.

[Get Started](guides/setup.md){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View on GitHub](https://github.com/nessaee/chess-database){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## Quick Start

1. [Setup Guide](guides/setup.md)
2. [System Architecture](architecture.md)
3. [API Reference](api-reference.md)
4. [Feature Demos](demos.md)

## System Overview

The Chess Database is built with performance and scalability in mind:

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    %% Frontend Layer
    subgraph Frontend["Frontend Layer"]
        UI[React UI]
        BOARD[Chess Board]
        STATS[Statistics View]
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

## Core Features

1. **Game Analysis**
   - [Move Encoding](backend/encoding.md)
   - [Storage Optimization](backend/database.md)
   - Performance Monitoring

2. **Database Features**
   - [Partitioned Tables](backend/database.md#table-partitioning)
   - [Materialized Views](backend/database.md#materialized-views)
   - [Performance Indexes](backend/database.md#indexes)

3. **API Services**
   - [RESTful Endpoints](api-reference.md)
   - [Performance Metrics](backend/database.md#endpoint-performance-stats)
   - [Error Handling](architecture.md#error-handling)

## Documentation Structure

1. **Getting Started**
   - [Setup Guide](guides/setup.md)
   - [Development Guide](guides/development.md)
   - [Feature Demos](demos.md)

2. **Architecture**
   - [System Overview](architecture.md)
   - [Database Design](backend/database.md)
   - [Move Encoding](backend/encoding.md)

3. **API Reference**
   - [Endpoints](api-reference.md)
   - [Data Models](backend/models.md)
   - [Authentication](api-reference.md#authentication)

4. **Frontend**
   - [Components](frontend/components.md)
   - [State Management](frontend/state.md)
   - [API Integration](frontend/api.md)

## Performance Features

{: .highlight }
> - **Efficient Storage**: Binary move encoding reduces storage by ~70%
> - **Fast Queries**: Materialized views and smart indexing
> - **Scalable Design**: Table partitioning and performance monitoring
> - **Real-time Analysis**: Pre-computed statistics and cached results

## Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) to get started.

## Support

Need help? Check out our:
- [FAQ](guides/faq.md)
- [Troubleshooting Guide](guides/troubleshooting.md)
- [GitHub Issues](https://github.com/nessaee/chess-database/issues)

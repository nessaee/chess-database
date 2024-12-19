---
layout: default
title: Data Processing Pipelines
parent: Backend
nav_order: 4
---

# Data Processing Pipelines

{: .fs-9 }
Detailed documentation of the game and opening data processing pipelines.

{: .fs-6 .fw-300 }
The Chess Database uses sophisticated pipelines to process and store chess games and openings efficiently.

---
<script type="module">
	import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
	mermaid.initialize({
		startOnLoad: true,
		theme: 'light'
	});
</script>
## Overview

The system implements two main data processing pipelines:
1. Game Pipeline: Processes and imports chess games from PGN files
2. Opening Pipeline: Processes and stores chess openings from TSV files

Both pipelines use asynchronous processing and efficient data encoding for optimal performance.

## Game Pipeline

### Architecture

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    subgraph Input["Input Processing"]
        PGN[PGN Files]
        CHUNK[Chunk Parser]
        META[Metadata Extractor]
    end
    
    subgraph Processing["Game Processing"]
        VALID[Validation]
        ENC[Move Encoder]
        BATCH[Batch Processor]
    end
    
    subgraph Storage["Database Storage"]
        PLAYER[Player Storage]
        GAME[Game Storage]
        STATS[Statistics Update]
    end
    
    PGN --> CHUNK
    CHUNK --> META
    META --> VALID
    VALID --> ENC
    ENC --> BATCH
    BATCH --> PLAYER
    BATCH --> GAME
    GAME --> STATS
    
    classDef input fill:#f9f9f9,stroke:#333,stroke-width:2px
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef storage fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    
    class PGN,CHUNK,META input
    class VALID,ENC,BATCH process
    class PLAYER,GAME,STATS storage
</pre>
</div>

### Components

#### 1. Input Processing
- **PGN File Handling**
  - Supports single files and directories
  - Handles compressed archives
  - Implements concurrent file processing
- **Chunk Processing**
  - Processes PGN files in chunks for memory efficiency
  - Default chunk size: 50,000 bytes
  - Configurable through `ProcessingConfig`

#### 2. Game Processing
- **Validation**
  - Verifies PGN format
  - Checks move validity
  - Validates player information
- **Move Encoding**
  - Uses `ChessMoveEncoder` for efficient storage
  - Converts moves to binary format
  - Handles special cases (castling, promotions)

#### 3. Database Storage
- **Player Management**
  - Automatic player creation
  - Rating tracking
  - Name normalization
- **Game Storage**
  - Batch inserts for performance
  - Hash-based partitioning
  - Automatic ECO classification

### Configuration

```python
@dataclass
class ProcessingConfig:
    max_open_files: int = 5          # Maximum concurrent open files
    db_batch_size: int = 1000        # Database batch size
    parsing_chunk_size: int = 50_000  # PGN parsing chunk size
    download_concurrency: int = 1     # Concurrent downloads
    process_pool_size: Optional[int]  # Process pool size (default: CPU count - 1)
```

### Performance Metrics

The pipeline tracks various metrics:
- Files processed/failed
- Games processed/failed
- Database operations and retries
- Processing speed (games/second)
- Success rate

## Opening Pipeline

### Architecture

<div class="mermaid-wrapper">
<pre class="mermaid">
graph TB
    subgraph Input["Input Processing"]
        TSV[TSV Files]
        PARSE[TSV Parser]
        VALID[Move Validator]
    end
    
    subgraph Processing["Opening Processing"]
        ECO[ECO Classifier]
        ENC[Move Encoder]
        BATCH[Batch Processor]
    end
    
    subgraph Storage["Database Storage"]
        OPEN[Opening Storage]
        IDX[Index Updates]
    end
    
    TSV --> PARSE
    PARSE --> VALID
    VALID --> ECO
    ECO --> ENC
    ENC --> BATCH
    BATCH --> OPEN
    OPEN --> IDX
    
    classDef input fill:#f9f9f9,stroke:#333,stroke-width:2px
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef storage fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    
    class TSV,PARSE,VALID input
    class ECO,ENC,BATCH process
    class OPEN,IDX storage
</pre>
</div>

### Components

#### 1. Input Processing
- **TSV File Handling**
  - Processes tab-separated opening files
  - Format: ECO code, name, PGN moves
  - Supports batch processing

#### 2. Opening Processing
- **Move Validation**
  - Verifies move sequences
  - Checks ECO code validity
  - Validates opening names
- **Move Encoding**
  - Uses same encoder as game pipeline
  - Optimized for opening sequences
  - Maintains move order integrity

#### 3. Database Storage
- **Opening Table**
  - ECO classification
  - Named openings
  - Encoded move sequences
- **Indexing**
  - ECO code indexing
  - Name-based search support
  - Move sequence lookup

### Database Schema

```sql
CREATE TABLE openings (
    id SERIAL PRIMARY KEY,
    eco VARCHAR(3) NOT NULL,
    name TEXT NOT NULL,
    moves BYTEA NOT NULL
);

CREATE INDEX idx_openings_eco ON openings(eco);
```

### Error Handling

Both pipelines implement comprehensive error handling:
1. **Input Validation**
   - File format checking
   - Data integrity verification
   - Character encoding handling

2. **Processing Errors**
   - Move validation failures
   - Encoding errors
   - Memory management

3. **Database Errors**
   - Connection handling
   - Transaction management
   - Constraint violations

4. **Recovery Strategies**
   - Automatic retries
   - Partial batch commits
   - Error logging and reporting

## Usage Examples

### Game Pipeline

```python
# Initialize pipeline
pipeline = ChessDataPipeline(
    db_config=DatabaseConfig(
        host="localhost",
        port=5432,
        database="chess",
        user="user",
        password="pass"
    ),
    processing_config=ProcessingConfig(
        max_open_files=5,
        db_batch_size=1000
    )
)

# Process directory of PGN files
await pipeline.process_directory("/path/to/pgn/files")
```

### Opening Pipeline

```python
# Initialize processor
processor = OpeningProcessor(
    db_config=DatabaseConfig(
        host="localhost",
        port=5432,
        database="chess",
        user="user",
        password="pass"
    )
)

# Process opening file
await processor.process_tsv_file("/path/to/openings.tsv")
```

## Performance Optimization

1. **Memory Management**
   - Chunk-based processing
   - Batch database operations
   - Efficient move encoding

2. **Concurrency**
   - Asynchronous I/O
   - Process pool for CPU-intensive tasks
   - Connection pooling

3. **Database Optimization**
   - Prepared statements
   - Bulk inserts
   - Index management

4. **Monitoring**
   - Real-time metrics
   - Performance logging
   - Error tracking

---
layout: default
title: Data Processing Pipelines
parent: Backend
nav_order: 4
---

# Data Processing Pipelines

{: .fs-9 }
Detailed documentation of the game and opening data processing pipelines.

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

Both pipelines use asynchronous processing and data encoding for optimal performance.

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
- **Source Handling**
  - Downloads PGN/ZIP files from configured sources
  - Implements concurrency control
  - Supports multiple file formats
- **Chunk Processing**
  - Configurable chunk sizes for memory efficiency
  - Parallel processing capability
  - Optimized for large files

#### 2. Game Processing
- **Validation**
  - ECO code format verification (letter + 2 digits)
  - Game result validation (1-0, 0-1, 1/2-1/2, *)
  - Player and date information checks
- **Move Encoding**
  - UCI format conversion
  - Binary encoding for storage efficiency
  - Special move handling

#### 3. Database Operations
- **Player Management**
  - Unique batch processing
  - Rating history tracking
  - Duplicate prevention
- **Game Storage**
  - Configurable batch sizes
  - Exponential backoff retry (5 attempts)
  - Integrity constraint checks

#### 4. Performance Monitoring
- **Metrics Tracking**
  - Processing rates and success ratios
  - Database operations and retries
  - File and game-level metrics
  - Real-time progress updates

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
- **Data Source**
  - TSV file reading
  - Opening definition parsing
  - Batch processing support

#### 2. Move Validation
- **Validation Checks**
  - Move sequence legality verification
  - ECO code assignment validation
  - Opening name format checks
  - Comprehensive error logging

#### 3. Storage Operations
- **Data Storage**
  - Binary move encoding
  - Opening metadata storage
  - Processing statistics tracking
  - Batch operation support

#### 4. Error Handling
- **Error Management**
  - Invalid move sequence logging
  - Database operation failure tracking
  - Processing statistics maintenance
  - Detailed error reporting

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

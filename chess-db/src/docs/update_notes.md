# Update Notes

## 2024-12-16: Binary Format Change for Move Data
- 22:55 GET /analysis/move-counts materialized view
### Changes
- Modified binary format for move data storage:
  - First 2 bytes: Move count (uint16, big-endian)
  - Remaining bytes: Game moves (2 bytes per move)

### Database Updates
- Created materialized view `move_count_stats` for optimized move count analysis
- Added automatic refresh trigger on games table updates
- Added validation for move count range (0-500 moves)

### Performance Improvements
- Reduced header size from 19 bytes to 2 bytes
- Simplified move count extraction
- Added concurrent refresh for materialized view
- Added index on move count for faster queries

### Migration Notes
If you have existing data, you'll need to update the binary format of the moves column. A migration script will be provided in a separate update.


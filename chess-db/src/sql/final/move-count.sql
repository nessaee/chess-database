WITH game_moves_analysis AS (
  SELECT 
    -- Calculate actual moves based on data length
    (length(moves) - 20) / 4 as actual_full_moves,
    result,
    (get_byte(moves, 17) << 8 | get_byte(moves, 18)) as stored_move_count,
    length(moves) as total_bytes
  FROM games
)
SELECT 
  actual_full_moves,
  COUNT(*) as number_of_games,
  ROUND(AVG(total_bytes), 2) as avg_bytes,
  string_agg(DISTINCT result, ', ' ORDER BY result) as results,
  MIN(stored_move_count) as min_stored_count,
  MAX(stored_move_count) as max_stored_count,
  ROUND(AVG(stored_move_count), 2) as avg_stored_count
FROM game_moves_analysis
WHERE actual_full_moves >= 0  -- Filter out any potentially corrupted data
GROUP BY actual_full_moves
ORDER BY number_of_games ASC
LIMIT 15;
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


-- This query analyzes the moves encoding in the "games" table. It calculates the actual full moves
-- from the binary "moves" field by using the structure:
--   - The first 20 bytes are a header.
--   - After the header, each full move is represented by 4 bytes (2 for white's move, 2 for black's move).
--   Thus, (length(moves) - 20) / 4 gives the number of full moves.
--
-- Additionally, it compares the calculated number of moves to the stored move count obtained from bytes 17 and 18
-- and provides statistics such as minimum, maximum, and average stored counts. It also groups games by the calculated
-- number of actual full moves, counting how many games fall into each category, and showing the results present in them.

WITH game_moves_analysis AS (
    SELECT 
        (length(moves) - 20) / 4 AS actual_full_moves,
        result,
        (get_byte(moves, 17) << 8 | get_byte(moves, 18)) AS stored_move_count,
        length(moves) AS total_bytes
    FROM games
)
SELECT 
    actual_full_moves,
    COUNT(*) AS number_of_games,
    ROUND(AVG(total_bytes), 2) AS avg_bytes,
    string_agg(DISTINCT result, ', ' ORDER BY result) AS results,
    MIN(stored_move_count) AS min_stored_count,
    MAX(stored_move_count) AS max_stored_count,
    ROUND(AVG(stored_move_count), 2) AS avg_stored_count
FROM game_moves_analysis
WHERE actual_full_moves >= 0
GROUP BY actual_full_moves
ORDER BY number_of_games ASC
LIMIT 15;

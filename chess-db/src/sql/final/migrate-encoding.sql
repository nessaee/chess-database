-- First let's verify our data before making changes
WITH move_analysis AS (
    SELECT 
        id,
        length(moves) as original_length,
        get_byte(moves, 17) << 8 | get_byte(moves, 18) as stored_move_count,
        moves
    FROM games
    WHERE moves IS NOT NULL
)
SELECT 
    COUNT(*) as total_games,
    AVG(original_length) as avg_length,
    MIN(original_length) as min_length,
    MAX(original_length) as max_length,
    AVG(stored_move_count) as avg_move_count
FROM move_analysis;

-- Create backup table before modifying data
CREATE TABLE games_moves_backup AS 
SELECT id, moves FROM games;

-- Update the moves column, keeping only from byte 19 onwards
UPDATE games
SET moves = substring(moves from 19)
WHERE moves IS NOT NULL;

-- Verify the update
WITH move_analysis AS (
    SELECT 
        id,
        length(moves) as new_length,
        get_byte(moves, 0) as first_byte,
        get_byte(moves, 1) as second_byte
    FROM games
    WHERE moves IS NOT NULL
)
SELECT 
    COUNT(*) as total_games,
    AVG(new_length) as avg_length,
    MIN(new_length) as min_length,
    MAX(new_length) as max_length,
    AVG(first_byte << 8 | second_byte) as avg_move_count
FROM move_analysis;

-- If something goes wrong, here's how to rollback:
-- UPDATE games g
-- SET moves = b.moves
-- FROM games_moves_backup b
-- WHERE g.id = b.id;

-- Once everything is verified, you can drop the backup:
-- DROP TABLE games_moves_backup;


5,313,048
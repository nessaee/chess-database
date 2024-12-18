WITH game_moves AS (
    SELECT 
        id as game_id,
        (get_byte(moves::bytea, 0) << 8 | get_byte(moves::bytea, 1))::integer as game_move_length,
        substring(moves::bytea from 3) as game_moves_no_length
    FROM games 
    WHERE id = 13256467
),
opening_matches AS (
    SELECT DISTINCT ON (o.name)
        g.game_id,
        o.name as opening_name,
        g.game_move_length,
        (get_byte(o.moves::bytea, 0) << 8 | get_byte(o.moves::bytea, 1))::integer as opening_move_length,
        array_length(string_to_array(o.name, ':'), 1) as variation_depth,
        -- Show complete sequences for both game and opening
        encode(g.game_moves_no_length, 'hex') as full_game_sequence,
        encode(substring(o.moves::bytea from 3), 'hex') as full_opening_sequence,
        -- Compare next few moves after the common sequence
        encode(substring(g.game_moves_no_length from 15), 'hex') as next_game_moves,
        encode(substring(o.moves::bytea from 17), 'hex') as next_opening_moves
    FROM game_moves g
    CROSS JOIN openings o
    WHERE (get_byte(o.moves::bytea, 0) << 8 | get_byte(o.moves::bytea, 1)) <= g.game_move_length
        AND (get_byte(o.moves::bytea, 0) << 8 | get_byte(o.moves::bytea, 1)) >= 2
        AND substring(g.game_moves_no_length for 14) = 
            substring(o.moves::bytea from 3 for 14)
)
SELECT * FROM opening_matches
ORDER BY opening_move_length DESC, variation_depth DESC
LIMIT 5;
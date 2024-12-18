#!/bin/bash

echo "Database Size:"
docker-compose exec -T db psql -U postgres chess-test -c "SELECT pg_size_pretty(pg_database_size('chess-test'));"

echo -e "\nTable Sizes:"
docker-compose exec -T db psql -U postgres chess-test -c "SELECT table_name, pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size FROM information_schema.tables WHERE table_schema = 'public' ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;"

echo -e "\nGames Table Details:"
docker-compose exec -T db psql -U postgres chess-test -c "SELECT count(*) as row_count, pg_size_pretty(pg_total_relation_size('games')) as total_size, pg_size_pretty(pg_relation_size('games')) as table_size, pg_size_pretty(pg_total_relation_size('games') - pg_relation_size('games')) as index_size FROM games;"

echo -e "\nColumn Sizes in Games Table:"
docker-compose exec -T db psql -U postgres chess-test -c "SELECT column_name, pg_column_size(column_name::text) as column_definition_size, pg_size_pretty(SUM(pg_column_size(games.*))) as total_data_size FROM information_schema.columns LEFT JOIN games ON true WHERE table_name = 'games' GROUP BY column_name ORDER BY pg_column_size(column_name::text) DESC;"
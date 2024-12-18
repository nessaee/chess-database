#!/bin/bash

# Base URL for the API
API_URL="http://localhost:5000"

# Test player search endpoint
echo "Testing player search endpoint..."
curl -X GET "${API_URL}/players/search?q=Magnus&limit=5"

echo -e "\n\nTesting player opening endpoint..."
curl -X GET "${API_URL}/analysis/players/1394/openings?min_games=20"



# Test get player performance endpoint (no dates)
echo -e "\n\nTesting player performance endpoint (no dates)..."
curl -X GET "${API_URL}/players/1394/performance?time_range=monthly"

# Test get player performance with valid date range
echo -e "\n\nTesting player performance with date range..."
START_DATE=$(date -d "1 year ago" +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)
curl -X GET "${API_URL}/players/1394/performance?time_range=monthly&start_date=${START_DATE}&end_date=${END_DATE}"

# Test get analysis endpoint
echo -e "\n\nTesting analysis endpoint..."
curl -X GET "${API_URL}/analysis/player/1394/openings?min_games=20"

# Test get detailed stats endpoint with different time periods
echo -e "\n\nTesting detailed stats endpoint (1 year)..."
curl -X GET "${API_URL}/players/1394/detailed-stats?time_period=1y"

echo -e "\n\nTesting detailed stats endpoint (6 months)..."
curl -X GET "${API_URL}/players/1394/detailed-stats?time_period=6m"

echo -e "\n\nTesting detailed stats endpoint (3 months)..."
curl -X GET "${API_URL}/players/1394/detailed-stats?time_period=3m"
echo -e "\n\n"
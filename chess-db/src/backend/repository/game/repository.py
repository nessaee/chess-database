"""Repository for chess game data access."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, text, and_, case
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..models.game import GameDB, GameResponse
from ..models.player import PlayerDB
from .decoder import GameDecoder
from ..common.validation import DateHandler
from ..common.errors import DatabaseOperationError, EntityNotFoundError

logger = logging.getLogger(__name__)

class GameRepository:
    """Repository for chess game data access."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session and decoder."""
        self.db = db
        self.decoder = GameDecoder()
        self.date_handler = DateHandler()

    async def get_games(
            self,
            player_name: Optional[str] = None,
            player_id: Optional[int] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            only_dated: bool = False,
            limit: int = 50,
            move_notation: str = 'uci'
        ) -> List[GameResponse]:
        """
        Retrieve games with optional filtering.
        
        Args:
            player_name: Optional player name to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter
            only_dated: If True, only return games with dates
            limit: Maximum number of games to return
            move_notation: Move notation format ('uci' or 'san')
            
        Returns:
            List of GameResponse objects
        """
        try:
            # Build base query with eager loading of player relationships
            query = (
                select(GameDB)
                .options(
                    joinedload(GameDB.white_player),
                    joinedload(GameDB.black_player)
                )
            )

            # Add date filters
            if start_date:
                start = self.date_handler.validate_and_parse_date(start_date, "start_date")
                if start:
                    query = query.where(GameDB.date >= start)
            
            if end_date:
                end = self.date_handler.validate_and_parse_date(end_date, "end_date")
                if end:
                    query = query.where(GameDB.date <= end)

            if only_dated:
                query = query.where(GameDB.date.isnot(None))

            # Add player name filter if provided
            if player_name:
                player_filter = or_(
                    GameDB.white_player.has(PlayerDB.name.ilike(f'%{player_name}%')),
                    GameDB.black_player.has(PlayerDB.name.ilike(f'%{player_name}%'))
                )
                query = query.where(player_filter)

            # Add player ID filter if provided
            if player_id:
                player_filter = or_(
                    GameDB.white_player_id == player_id,
                    GameDB.black_player_id == player_id
                )
                query = query.where(player_filter)
            # Add ordering and limit
            query = query.order_by(GameDB.date.desc()).limit(limit)

            # Execute query
            result = await self.db.execute(query)
            games = result.unique().scalars().all()

            # Process games and decode moves
            processed_games = []
            for game in games:
                try:
                    # Decode binary moves to UCI
                    uci_moves = self.decoder.decode_moves(game.moves)
                    
                    # Convert to SAN if requested
                    if move_notation == 'san':
                        san_moves, opening_name, num_moves = self.decoder.convert_uci_to_san(uci_moves)
                        moves_str = ' '.join(san_moves)
                    else:
                        moves_str = ' '.join(uci_moves)
                        opening_name = None
                        num_moves = len(uci_moves)
                    
                    # Create response with player names and moves
                    game_response = GameResponse(
                        id=game.id,
                        white_player_id=game.white_player_id,
                        black_player_id=game.black_player_id,
                        white_player_name=game.white_player.name if game.white_player else None,
                        black_player_name=game.black_player.name if game.black_player else None,
                        date=game.date,
                        result=game.result,
                        eco=game.eco,
                        moves=moves_str,
                        white_elo=game.white_elo,
                        black_elo=game.black_elo,
                        opening_name=opening_name,
                        num_moves=num_moves
                    )
                    processed_games.append(game_response)
                except Exception as e:
                    logger.error(f"Error processing game {game.id}: {str(e)}")
                    continue

            return processed_games

        except Exception as e:
            logger.error(f"Error in get_games: {str(e)}")
            raise DatabaseOperationError(f"Failed to fetch games: {str(e)}")

    async def get_game_by_id(self, game_id: int, move_notation: str = 'uci') -> Optional[GameResponse]:
        """
        Get a specific game by ID.
        
        Args:
            game_id: ID of the game to retrieve
            move_notation: Move notation format ('uci' or 'san')
            
        Returns:
            GameResponse object or None if not found
        """
        try:
            query = (
                select(GameDB)
                .options(
                    joinedload(GameDB.white_player),
                    joinedload(GameDB.black_player)
                )
                .where(GameDB.id == game_id)
            )
            
            result = await self.db.execute(query)
            game = result.unique().scalar_one_or_none()
            
            if not game:
                return None

            # Decode moves
            uci_moves = self.decoder.decode_moves(game.moves)
            
            # Convert to SAN if requested
            if move_notation == 'san':
                san_moves, opening_name, num_moves = self.decoder.convert_uci_to_san(uci_moves)
                moves_str = ' '.join(san_moves)
            else:
                moves_str = ' '.join(uci_moves)
                opening_name = None
                num_moves = len(uci_moves)

            return GameResponse(
                id=game.id,
                white_player_id=game.white_player_id,
                black_player_id=game.black_player_id,
                white_player_name=game.white_player.name if game.white_player else None,
                black_player_name=game.black_player.name if game.black_player else None,
                date=game.date,
                result=game.result,
                eco=game.eco,
                moves=moves_str,
                white_elo=game.white_elo,
                black_elo=game.black_elo,
                opening_name=opening_name,
                num_moves=num_moves
            )

        except Exception as e:
            logger.error(f"Error in get_game_by_id: {str(e)}")
            raise DatabaseOperationError(f"Failed to fetch game: {str(e)}")

    async def suggest_players(
            self,
            name: str,
            limit: int = 10
        ) -> List[str]:
        """Get player name suggestions based on partial input."""
        try:
            query = (
                select(PlayerDB.name)
                .where(PlayerDB.name.ilike(f'%{name}%'))
                .order_by(PlayerDB.name)
                .limit(limit)
            )
            
            result = await self.db.execute(query)
            return [row[0] for row in result.all()]

        except Exception as e:
            logger.error(f"Error in suggest_players: {str(e)}")
            raise DatabaseOperationError(f"Failed to fetch player suggestions: {str(e)}")

    async def get_game_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all games."""
        try:
            # Get total games
            total_query = select(func.count(GameDB.id))
            total_result = await self.db.execute(total_query)
            total_games = total_result.scalar()

            # Get total players
            players_query = select(func.count(PlayerDB.id))
            players_result = await self.db.execute(players_query)
            total_players = players_result.scalar()

            # Get result distribution
            results_query = (
                select(
                    GameDB.result,
                    func.count(GameDB.id).label('count')
                )
                .group_by(GameDB.result)
            )
            results_result = await self.db.execute(results_query)
            result_distribution = dict(results_result.all())

            return {
                "total_games": total_games,
                "total_players": total_players,
                "result_distribution": result_distribution
            }

        except Exception as e:
            logger.error(f"Error in get_game_stats: {str(e)}")
            raise DatabaseOperationError(f"Failed to fetch game stats: {str(e)}")
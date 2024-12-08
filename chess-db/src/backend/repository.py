from sqlalchemy.orm import Session,joinedload
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from models import ItemDB, ItemCreate, ItemUpdate
from models import GameDB, PlayerDB 

class ItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_item(self, item: ItemCreate) -> ItemDB:
        db_item = ItemDB(**item.model_dump())
        self.db.add(db_item)
        await self.db.commit()
        await self.db.refresh(db_item)
        return db_item

    async def get_items(self) -> list[ItemDB]:
        result = await self.db.execute(select(ItemDB))
        return result.scalars().all()

    async def get_item(self, item_id: int) -> ItemDB | None:
        result = await self.db.execute(select(ItemDB).filter(ItemDB.id == item_id))
        return result.scalar_one_or_none()

    async def update_item(self, item_id: int, item: ItemUpdate) -> ItemDB | None:
        db_item = await self.get_item(item_id)
        if not db_item:
            return None
            
        update_data = item.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_item, key, value)
            
        await self.db.commit()
        await self.db.refresh(db_item)
        return db_item

    async def delete_item(self, item_id: int) -> bool:
        db_item = await self.get_item(item_id)
        if not db_item:
            return False
            
        await self.db.delete(db_item)
        await self.db.commit()
        return True
    
class GameRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_games(self, player_name: str = None, start_date: str = None, 
                       end_date: str = None, limit: int = 50) -> list[GameDB]:
        query = (
            select(GameDB)
            .options(
                joinedload(GameDB.white_player),
                joinedload(GameDB.black_player)
            )
        )
        if player_name:
            # Create a case-insensitive search for partial matches
            player_filter = or_(
                GameDB.white_player.has(
                    PlayerDB.name.ilike(f'%{player_name}%')
                ),
                GameDB.black_player.has(
                    PlayerDB.name.ilike(f'%{player_name}%')
                )
            )
            query = query.where(player_filter)

        if start_date:
            query = query.where(GameDB.date >= start_date)
        
        if end_date:
            query = query.where(GameDB.date <= end_date)

        query = query.order_by(GameDB.date.desc()).limit(limit)
        result = await self.db.execute(query)
        
        return result.scalars().unique().all()
    
    async def get_game(self, game_id: int) -> GameDB | None:
        result = await self.db.execute(
            select(GameDB).filter(GameDB.id == game_id)
        )
        return result.scalar_one_or_none()

    async def get_player_games(self, player_id: int) -> list[GameDB]:
        result = await self.db.execute(
            select(GameDB).where(
                (GameDB.white_player_id == player_id) | 
                (GameDB.black_player_id == player_id)
            ).order_by(GameDB.date.desc())
        )
        return result.scalars().all()

    async def get_game_stats(self):
        # Get basic statistics about the games
        result = await self.db.execute("""
            SELECT 
                COUNT(*) as total_games,
                COUNT(DISTINCT white_player_id) + COUNT(DISTINCT black_player_id) as total_players,
                MIN(date) as earliest_game,
                MAX(date) as latest_game
            FROM games
        """)
        stats = await result.first()
        return {
            "total_games": stats[0],
            "total_players": stats[1],
            "earliest_game": stats[2],
            "latest_game": stats[3]
        }
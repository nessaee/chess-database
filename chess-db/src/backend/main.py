from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal, init_db
from repository import ItemRepository, GameRepository
from models import ItemCreate, ItemUpdate, ItemResponse, GameResponse
import logging

logger = logging.getLogger(__name__)
app = FastAPI()

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

@app.on_event("startup")
async def startup():
    await init_db()

# Item endpoints
@app.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    repo = ItemRepository(db)
    return await repo.create_item(item)

@app.get("/items", response_model=list[ItemResponse])
async def read_items(db: AsyncSession = Depends(get_db)):
    repo = ItemRepository(db)
    return await repo.get_items()

@app.get("/items/{item_id}", response_model=ItemResponse)
async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
    repo = ItemRepository(db)
    item = await repo.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item: ItemUpdate, db: AsyncSession = Depends(get_db)):
    repo = ItemRepository(db)
    updated_item = await repo.update_item(item_id, item)
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item

@app.delete("/items/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    repo = ItemRepository(db)
    success = await repo.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}

# Chess game endpoints
@app.get("/games", response_model=list[GameResponse])
async def read_games(
    player_name: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Received request with player_name: {player_name}")
    repo = GameRepository(db)
    games = await repo.get_games(
        player_name=player_name,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    logger.info(f"Found {len(games)} games matching criteria")
    return games

@app.get("/games/{game_id}", response_model=GameResponse)
async def read_game(game_id: int, db: AsyncSession = Depends(get_db)):
    repo = GameRepository(db)
    game = await repo.get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@app.get("/players/{player_id}/games", response_model=list[GameResponse])
async def read_player_games(player_id: int, db: AsyncSession = Depends(get_db)):
    repo = GameRepository(db)
    games = await repo.get_player_games(player_id)
    if not games:
        raise HTTPException(status_code=404, detail="No games found for this player")
    return games

@app.get("/stats/games")
async def get_game_stats(db: AsyncSession = Depends(get_db)):
    repo = GameRepository(db)
    stats = await repo.get_game_stats()
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
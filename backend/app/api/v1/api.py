from fastapi import APIRouter
from app.api.v1 import auth, market, portfolios, backtests, agents, settings

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(backtests.router, prefix="/backtests", tags=["backtests"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])

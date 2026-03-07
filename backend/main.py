import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from routers.condiment import router as condiment_router
from routers.fridge import router as fridge_router
from routers.ingredient_master import router as ingredient_master_router
from routers.recipe import router as recipe_router
from routers.shopping import router as shopping_router
from routers.suggest import router as suggest_router
from routers.user import router as user_router

logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("IntegrityError: %s %s — %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=409,
        content={"detail": "データの整合性制約に違反しました。"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s %s — %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "サーバーエラーが発生しました。"},
    )


app.include_router(user_router)
app.include_router(ingredient_master_router)
app.include_router(fridge_router)
app.include_router(condiment_router)
app.include_router(recipe_router)
app.include_router(suggest_router)
app.include_router(shopping_router)

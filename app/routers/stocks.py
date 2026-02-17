from fastapi import APIRouter, HTTPException
from typing import Optional, List

from app.models.schemas import (
    StockResponse,
    StockInfo,
    ErrorResponse,
    BatchStocksRequest
)
from app.services.scraper import scraper

router = APIRouter(prefix="/stocks")


@router.get("/{symbol}")
def get_stock_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: str = "1mo"
):
    """
    Pega dados históricos de uma ação da B3
    """
    try:
        data = scraper.get_stock_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@router.get("/{symbol}/info")
def get_stock_info(symbol: str):
    """
    Pega informações básicas de uma ação
    """
    try:
        data = scraper.get_stock_info(symbol)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@router.post("/batch")
def get_multiple_stocks(payload: BatchStocksRequest):
    """
    Pega dados de várias ações de uma vez
    """
    try:
        results = scraper.get_multiple_stocks(
            symbols=payload.symbols,
            start_date=payload.start_date,
            end_date=payload.end_date,
            period=payload.period,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular")
def get_popular_stocks():
    """Lista ações populares da B3"""
    return scraper.get_popular_stocks()

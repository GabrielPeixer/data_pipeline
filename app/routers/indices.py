from fastapi import APIRouter, HTTPException
from typing import Optional, Dict

from app.models.schemas import IndexResponse, ErrorResponse
from app.services.scraper import scraper

router = APIRouter(prefix="/indices")


@router.get("/{index_name}")
def get_index_data(
    index_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: str = "1mo"
):
    """
    Pega dados históricos de um índice da B3
    """
    try:
        data = scraper.get_index_data(
            index_name=index_name,
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@router.get("/")
def get_available_indices():
    """
    Lista índices disponíveis da B3
    """
    return scraper.get_available_indices()

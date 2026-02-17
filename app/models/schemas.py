from pydantic import BaseModel
from typing import Optional, List


class StockDataPoint(BaseModel):
    """Um ponto de dado de uma ação"""
    date: str
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int


class StockResponse(BaseModel):
    """Resposta com dados da ação"""
    symbol: str
    company_name: Optional[str] = None
    currency: str = "BRL"
    data: List[StockDataPoint]
    total_records: int


class StockInfo(BaseModel):
    """Info básica da ação"""
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    current_price: Optional[float] = None
    currency: str = "BRL"


class IndexDataPoint(BaseModel):
    """Um ponto de dado de um índice"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class IndexResponse(BaseModel):
    """Resposta com dados do índice"""
    index_name: str
    symbol: str
    data: List[IndexDataPoint]
    total_records: int


class ErrorResponse(BaseModel):
    """Erro"""
    error: str
    detail: Optional[str] = None


class BatchStocksRequest(BaseModel):
    """Para pedir várias ações de uma vez"""
    symbols: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period: str = "1mo"

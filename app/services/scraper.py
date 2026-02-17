import yfinance as yf
import pandas as pd
from typing import Optional, List, Dict, Any


# Índices da B3
B3_INDICES = {
    "IBOVESPA": "^BVSP",
    "IBRX100": "^IBX100",
    "IBRX50": "^IBX50",
    "IDIV": "IDIV11.SA",
    "SMALL": "SMAL11.SA",
}

# Ações populares
POPULAR_STOCKS = [
    "PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3",
    "B3SA3", "WEGE3", "RENT3", "SUZB3", "GGBR4"
]


class B3Scraper:
    """Classe para pegar dados da B3"""

    def __init__(self):
        self.suffix = ".SA"  # Para ações brasileiras

    def _format_symbol(self, symbol: str) -> str:
        """Adiciona .SA se não tiver"""
        symbol = symbol.upper().strip()
        if not symbol.endswith(self.suffix) and not symbol.startswith("^"):
            return f"{symbol}{self.suffix}"
        return symbol

    def _parse_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Converte DataFrame para lista de dicts"""
        if df.empty:
            return []

        df = df.reset_index()
        records = []

        for _, row in df.iterrows():
            record = {
                "date": row["Date"].strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "adj_close": round(float(row.get("Adj Close", row["Close"])), 2),
                "volume": int(row["Volume"])
            }
            records.append(record)

        return records

    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1mo"
    ) -> Dict[str, Any]:
        """
        Pega dados históricos de uma ação
        """
        formatted_symbol = self._format_symbol(symbol)
        print(f"Pegando dados de {formatted_symbol}")

        try:
            ticker = yf.Ticker(formatted_symbol)

            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date, interval="1d")
            else:
                df = ticker.history(period=period, interval="1d")

            if df.empty:
                raise ValueError(f"Nenhum dado para {symbol}")

            info = ticker.info
            company_name = info.get("longName") or info.get("shortName")

            records = self._parse_dataframe(df)

            return {
                "symbol": symbol.upper(),
                "company_name": company_name,
                "currency": "BRL",
                "data": records,
                "total_records": len(records)
            }

        except Exception as e:
            print(f"Erro em {symbol}: {str(e)}")
            raise

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Pega info básica da ação
        """
        formatted_symbol = self._format_symbol(symbol)

        try:
            ticker = yf.Ticker(formatted_symbol)
            info = ticker.info

            return {
                "symbol": symbol.upper(),
                "company_name": info.get("longName") or info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "currency": "BRL"
            }

        except Exception as e:
            print(f"Erro na info de {symbol}: {str(e)}")
            raise

    def get_index_data(
        self,
        index_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1mo"
    ) -> Dict[str, Any]:
        """
        Pega dados de um índice
        """
        index_name = index_name.upper()

        if index_name not in B3_INDICES:
            raise ValueError(f"Índice não encontrado: {index_name}")

        symbol = B3_INDICES[index_name]
        print(f"Pegando dados do índice {index_name}")

        try:
            ticker = yf.Ticker(symbol)

            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date, interval="1d")
            else:
                df = ticker.history(period=period, interval="1d")

            if df.empty:
                raise ValueError(f"Nenhum dado para {index_name}")

            records = self._parse_dataframe(df)

            # Remove adj_close para índices
            for record in records:
                record.pop("adj_close", None)

            return {
                "index_name": index_name,
                "symbol": symbol,
                "data": records,
                "total_records": len(records)
            }

        except Exception as e:
            print(f"Erro no índice {index_name}: {str(e)}")
            raise

    def get_multiple_stocks(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1mo"
    ) -> List[Dict[str, Any]]:
        """
        Pega dados de várias ações
        """
        results = []

        for symbol in symbols:
            try:
                data = self.get_stock_data(symbol, start_date, end_date, period)
                results.append(data)
            except Exception as e:
                print(f"Erro em {symbol}: {str(e)}")
                results.append({
                    "symbol": symbol.upper(),
                    "error": str(e)
                })

        return results

    def get_available_indices(self) -> Dict[str, str]:
        """Retorna índices disponíveis"""
        return B3_INDICES.copy()

    def get_popular_stocks(self) -> List[str]:
        """Retorna ações populares"""
        return POPULAR_STOCKS.copy()


# Instância global
scraper = B3Scraper()

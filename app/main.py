from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routers import stocks, indices

# Cria a aplicação FastAPI
app = FastAPI(
    title="B3 Data Scraper",
    description="API simples para pegar dados de ações e índices da B3",
    version="1.0.0"
)

# Permite requests de qualquer lugar (para desenvolvimento)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adiciona os endpoints
app.include_router(stocks.router)
app.include_router(indices.router)


@app.get("/")
def home():
    """Página inicial"""
    return {"message": "API de dados da B3", "docs": "/docs"}


@app.get("/health")
def health():
    """Verifica se a API está funcionando"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, Query
import ccxt
import time

app = FastAPI()

@app.get("/")
def root():
    return {"message": "✅ CCXT Proxy is running! Use /ohlcv or /price_impact endpoints."}

@app.get("/ohlcv")
def get_ohlcv(
    exchange: str = Query(..., description="Exchange ex: binance"),
    symbol: str = Query(..., description="Trading pair ex: ARB/USDT"),
    timeframe: str = Query("1m", description="Interval (1m, 5m, 15m, 1h, 4h)"),
    since: int = Query(..., description="UNIX timestamp în ms (momentul știrii)"),
    limit: int = Query(200, description="Număr de candles")
):
    try:
        ex = getattr(ccxt, exchange)()
        data = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
        return {"exchange": exchange, "symbol": symbol, "timeframe": timeframe, "ohlcv": data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/price_impact")
def get_price_impact(
    exchange: str = Query(..., description="Exchange ex: binance"),
    symbol: str = Query(..., description="Trading pair ex: ARB/USDT"),
    since: int = Query(..., description="UNIX timestamp în ms (momentul știrii)")
):
    try:
        ex = getattr(ccxt, exchange)()
        ohlcv = ex.fetch_ohlcv(symbol, timeframe="1m", since=since, limit=720)  # ~12h
        if not ohlcv:
            return {"error": "No OHLCV data found"}

        start_price = ohlcv[0][1]  # open price
        impacts = {}

        windows = {"15m": 15, "1h": 60, "4h": 240, "12h": 720}
        for label, mins in windows.items():
            if len(ohlcv) >= mins:
                close_price = ohlcv[mins-1][4]  # close
                impacts[label] = round(((close_price - start_price) / start_price) * 100, 2)

        return {
            "exchange": exchange,
            "symbol": symbol,
            "start_price": start_price,
            "impact": impacts
        }
    except Exception as e:
        return {"error": str(e)}

from fastapi import FastAPI, Query
import ccxt
import time

app = FastAPI()

@app.get("/ohlcv")
def get_ohlcv(
    exchange: str = Query(..., description="Exchange ex: binance"),
    symbol: str = Query(..., description="Trading pair ex: ARB/USDT"),
    timeframe: str = Query("1m", description="Interval (1m, 5m, 15m, 1h, 4h)"),
    since: int = Query(..., description="UNIX timestamp in ms (when event happened)"),
    limit: int = Query(200, description="Number of candles")
):
    try:
        ex = getattr(ccxt, exchange)()
        data = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
        return {"exchange": exchange, "symbol": symbol, "timeframe": timeframe, "ohlcv": data}
    except Exception as e:
        return {"error": str(e)}
@app.get("/price_impact")
def price_impact(
    exchange: str = Query(..., description="Exchange ex: binance"),
    symbol: str = Query(..., description="Trading pair ex: ARB/USDT"),
    since: int = Query(..., description="UNIX timestamp in ms (event time)")
):
    try:
        ex = getattr(ccxt, exchange)()
        # Luăm 12h de date minute-level după eveniment
        data = ex.fetch_ohlcv(symbol, timeframe="1m", since=since, limit=720)

        if not data or len(data) < 10:
            return {"error": "Not enough OHLCV data"}

        start_price = data[0][1]  # open price prima lumânare
        end_price_15m = data[min(15, len(data)-1)][4]
        end_price_1h = data[min(60, len(data)-1)][4]
        end_price_4h = data[min(240, len(data)-1)][4]
        end_price_12h = data[min(720, len(data)-1)][4]

        def pct_change(start, end):
            return round(((end - start) / start) * 100, 2)

        return {
            "exchange": exchange,
            "symbol": symbol,
            "start_price": start_price,
            "impact": {
                "15m": pct_change(start_price, end_price_15m),
                "1h": pct_change(start_price, end_price_1h),
                "4h": pct_change(start_price, end_price_4h),
                "12h": pct_change(start_price, end_price_12h)
            }
        }

    except Exception as e:
        return {"error": str(e)}

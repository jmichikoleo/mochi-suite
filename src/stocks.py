"""Stock portfolio tracking with technical analysis."""

import yfinance as yf
import numpy as np


def fetch_stock_data(symbol: str, period: str = "3mo") -> dict:
    """Fetch stock data and calculate technical indicators."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            return {"symbol": symbol, "error": "No data available", "has_data": False}

        close = hist["Close"]
        latest = close.iloc[-1]
        prev_close = close.iloc[-2] if len(close) > 1 else latest
        change = latest - prev_close
        change_pct = (change / prev_close) * 100

        # Technical indicators
        rsi = _calculate_rsi(close)
        sma_20 = close.rolling(window=20).mean().iloc[-1] if len(close) >= 20 else None
        sma_50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else None
        macd_data = _calculate_macd(close)

        # Signal interpretation
        signals = []
        if rsi is not None:
            if rsi > 70:
                signals.append("RSI overbought (>70)")
            elif rsi < 30:
                signals.append("RSI oversold (<30)")
            else:
                signals.append(f"RSI neutral ({rsi:.0f})")

        if sma_20 and sma_50:
            if sma_20 > sma_50:
                signals.append("SMA20 > SMA50 (bullish)")
            else:
                signals.append("SMA20 < SMA50 (bearish)")

        if macd_data.get("histogram") is not None:
            if macd_data["histogram"] > 0:
                signals.append("MACD positive (bullish)")
            else:
                signals.append("MACD negative (bearish)")

        # Stock news
        news_items = []
        try:
            for item in (ticker.news or [])[:3]:
                news_items.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "publisher": item.get("publisher", ""),
                })
        except Exception:
            pass

        return {
            "symbol": symbol,
            "has_data": True,
            "price": round(float(latest), 2),
            "change": round(float(change), 2),
            "change_pct": round(float(change_pct), 2),
            "rsi": round(float(rsi), 1) if rsi else None,
            "sma_20": round(float(sma_20), 2) if sma_20 else None,
            "sma_50": round(float(sma_50), 2) if sma_50 else None,
            "macd": macd_data,
            "signals": signals,
            "news": news_items,
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e), "has_data": False}


def _calculate_rsi(prices, period: int = 14):
    if len(prices) < period + 1:
        return None
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])


def _calculate_macd(prices):
    if len(prices) < 26:
        return {"macd_line": None, "signal_line": None, "histogram": None}
    ema_12 = prices.ewm(span=12, adjust=False).mean()
    ema_26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd_line": round(float(macd_line.iloc[-1]), 2),
        "signal_line": round(float(signal_line.iloc[-1]), 2),
        "histogram": round(float(histogram.iloc[-1]), 2),
    }


def get_portfolio_summary(symbols: list) -> dict:
    """Get data for all portfolio stocks."""
    stocks = []
    for symbol in symbols:
        stocks.append(fetch_stock_data(symbol))
    return {"stocks": stocks, "count": len(stocks)}

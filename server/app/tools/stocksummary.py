from langchain_core.tools import tool  
from typing import Dict, Union, Set, List
import yfinance as yf 
import datetime as dt 
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.volume import volume_weighted_average_price
import pandas as pd 
import numpy as np 
from sklearn.linear_model import LinearRegression




def get_stock_prices(ticker: str) -> Union[Dict, str]:
    """Fetches historical stock price data and technical indicator for a given ticker."""
    try:
        data = yf.download(
            ticker,
            start=dt.datetime.now() - dt.timedelta(weeks=24*3),
            end=dt.datetime.now(),
            interval='1d'
        )
        df= data.copy()
        if len(df.columns[0]) > 1:
            df.columns = [i[0] for i in df.columns]
        data.reset_index(inplace=True)
        data.Date = data.Date.astype(str)

        indicators = {}

        # Momentum Indicators
        rsi_series = RSIIndicator(df['Close'], window=14).rsi().iloc[-12:]
        indicators["RSI"] = {date.strftime('%Y-%m-%d'): int(value) for date, value in rsi_series.dropna().to_dict().items()}
        sto_series = StochasticOscillator(
            df['High'], df['Low'], df['Close'], window=14).stoch().iloc[-12:]
        # print(sto_series)
        indicators["Stochastic_Oscillator"] = {date.strftime('%Y-%m-%d'): int(value) for date, value in sto_series.dropna().to_dict().items()}

        macd = MACD(df['Close'])
        macd_series = macd.macd().iloc[-12:]
        # print(macd_series)
        indicators["MACD"] = {date.strftime('%Y-%m-%d'): int(value) for date, value in macd_series.to_dict().items()}
        macd_signal_series = macd.macd_signal().iloc[-12:]
        # print(macd_signal_series)
        indicators["MACD_Signal"] = {date.strftime('%Y-%m-%d'): int(value) for date, value in macd_signal_series.to_dict().items()}

        vwap_series = volume_weighted_average_price(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            volume=df['Volume'],
        ).iloc[-12:]
        indicators["vwap"] = {date.strftime('%Y-%m-%d'): int(value) for date, value in vwap_series.to_dict().items()}

        return {'stock_price': data.to_dict(orient='records'), 'indicators': indicators}
    except Exception as e:
        return f"Error fetching price data: {str(e)}"

def get_financial_metrics(ticker: str) -> Union[Dict, str]:
    """Fetches key financial ratios for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'pe_ratio': info.get('forwardPE'),
            'price_to_book': info.get('priceToBook'),
            'debt_to_equity': info.get('debtToEquity'),
            'profit_margins': info.get('profitMargins')
        }
    except Exception as e:
        return f"Error fetching ratios: {str(e)}"



def get_stock_summary(ticker: str) -> Dict:
    """Returns a compact summary of stock indicators, financials, recent prices, trend detection, and displays charts with plotly."""
    print(f"Generating charts for {ticker}")

    try: 
        
        price_data = get_stock_prices(ticker)
        indicators = price_data['indicators']
        full_prices = pd.DataFrame(price_data['stock_price'])

        full_prices.columns = [k if isinstance(k, str) else k[0] or k[1] for k in full_prices.columns]

        full_prices["Date"] = pd.to_datetime(full_prices["Date"])
        full_prices.sort_values("Date", inplace=True)
        full_prices.reset_index(drop=True, inplace=True)

        ema_9 = EMAIndicator(full_prices['Close'], window = 9).ema_indicator()
        ema_21 = EMAIndicator(full_prices['Close'], window = 21).ema_indicator()

        if ema_9.iloc[-2] < ema_21.iloc[-2] and ema_9.iloc[-1] > ema_21.iloc[-1]:
            crossover = "bullish_crossover"
        elif ema_9.iloc[-2] > ema_21.iloc[-2] and ema_9.iloc[-1] < ema_21.iloc[-1]:
            crossover = "bearish_crossover"
        else:
            crossover = "no_crossover"

        
        last_n = 21 
        recent_close = full_prices["Close"].tail(last_n).values.reshape(-1, 1)
        X = np.arange(len(recent_close)).reshape(-1, 1)
        model = LinearRegression().fit(X, recent_close)
        slope = model.coef_[0][0]

        if slope > 0.3:
            trend = "bullish"
        elif slope < -0.3:
            trend = "bearish"
        else:
            trend = "sideways"

        recent_prices = full_prices.tail(10).round(2)
        recent_price_records = recent_prices[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
        recent_price_records["Date"] = recent_price_records["Date"].dt.strftime('%Y-%m-%d')
        recent_price_records = recent_price_records.to_dict(orient="records")


        close = full_prices["Close"]
        summary_stats = {
            "current_price": round(close.iloc[-1], 2),
            "5_day_change_percent": round(100 * (close.iloc[-1] - close.iloc[-6]) / close.iloc[-6], 2),
            "52_week_high": round(close.max(), 2),
            "52_week_low": round(close.min(), 2),
            "average_volume": int(full_prices["Volume"].mean())
        }

        # --- Recent indicators (last known value per type) ---
        recent_indicators = {k: list(v.values())[-1] for k, v in indicators.items()}

        # --- Financial metrics ---
        metrics = get_financial_metrics(ticker)
        key_metrics = {
            "pe_ratio": metrics.get("pe_ratio"),
            "price_to_book": metrics.get("price_to_book"),
            "debt_to_equity": metrics.get("debt_to_equity"),
            "profit_margins": metrics.get("profit_margins"),
        }



        return {
            "ticker": ticker,
            "summary": summary_stats,
            "latest_indicators": recent_indicators,
            "financial_metrics": key_metrics,
            "recent_prices": recent_price_records,
            "trend_detection": {
                "linear_slope": round(float(slope), 4),
                "ema_9": round(ema_9.iloc[-1], 2),
                "ema_21": round(ema_21.iloc[-1], 2),
                "crossover": crossover,
                "trend": trend
            }
        }

    except Exception as e:
        return {"error": str(e)}


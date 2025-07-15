import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from typing import Dict, Any
import warnings
warnings.filterwarnings('ignore')

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


MARKET_CONFIG = {
    'US': {
        'timezone': 'US/Eastern',
        'currency_symbol': '$',
        'market_open_time': (9, 30),
        'market_close_time': (16, 0),
        'weekends': [5, 6],
        'suffix_patterns': ['', '.US'],
        'name': 'US Market'
    },
    'IN': {
        'timezone': 'Asia/Kolkata',
        'currency_symbol': '₹',
        'market_open_time': (9, 15),
        'market_close_time': (15, 30),
        'weekends': [5, 6],
        'suffix_patterns': ['.NS', '.BO'],
        'name': 'Indian Market'
    }
}


from dotenv import load_dotenv
import os 
load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")


class StopLossResponse(BaseModel):
  stop_loss: float = Field(...,description = "Calculated stop loss price")

class TargetPriceResponse(BaseModel):
  target_price: float = Field(...,description = "Calculated target price")

def detect_market(symbol: str) -> str:
    """Detect market type based on symbol suffix"""
    symbol = symbol.upper()
    if any(symbol.endswith(suffix) for suffix in MARKET_CONFIG['IN']['suffix_patterns']):
        return 'IN'
    return 'US'

def is_market_open(market_type: str = 'US') -> bool:
    """Check if the specified market is currently open"""
    config = MARKET_CONFIG[market_type]
    now = datetime.now(pytz.timezone(config['timezone']))
    
    # Check if it's a weekday
    if now.weekday() in config['weekends']:
        return False
    
    # Market hours
    market_open = now.replace(
        hour=config['market_open_time'][0], 
        minute=config['market_open_time'][1], 
        second=0, 
        microsecond=0
    )
    market_close = now.replace(
        hour=config['market_close_time'][0], 
        minute=config['market_close_time'][1], 
        second=0, 
        microsecond=0
    )
    
    return market_open <= now <= market_close

def calculate_technical_indicators(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate various technical indicators"""
    indicators = {}
    
    # Basic price metrics
    indicators['current_price'] = data['Close'].iloc[-1]
    indicators['previous_close'] = data['Close'].iloc[-2] if len(data) > 1 else data['Close'].iloc[-1]
    indicators['high_52w'] = data['High'].rolling(window=min(252, len(data))).max().iloc[-1]
    indicators['low_52w'] = data['Low'].rolling(window=min(252, len(data))).min().iloc[-1]
    
    # Moving averages
    indicators['sma_20'] = data['Close'].rolling(window=20).mean().iloc[-1]
    indicators['sma_50'] = data['Close'].rolling(window=50).mean().iloc[-1] if len(data) >= 50 else indicators['sma_20']
    indicators['ema_12'] = data['Close'].ewm(span=12).mean().iloc[-1]
    indicators['ema_26'] = data['Close'].ewm(span=26).mean().iloc[-1]
    
    # Volatility
    indicators['volatility_20d'] = data['Close'].pct_change().rolling(window=20).std().iloc[-1] * np.sqrt(252)
    
    # RSI calculation
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    indicators['rsi'] = 100 - (100 / (1 + rs)).iloc[-1]
    
    # MACD
    indicators['macd'] = indicators['ema_12'] - indicators['ema_26']
    indicators['macd_signal'] = data['Close'].ewm(span=12).mean().subtract(data['Close'].ewm(span=26).mean()).ewm(span=9).mean().iloc[-1]
    
    # Bollinger Bands
    bb_period = 20
    bb_std = 2
    sma_bb = data['Close'].rolling(window=bb_period).mean()
    std_bb = data['Close'].rolling(window=bb_period).std()
    indicators['bb_upper'] = (sma_bb + (std_bb * bb_std)).iloc[-1]
    indicators['bb_lower'] = (sma_bb - (std_bb * bb_std)).iloc[-1]
    indicators['bb_middle'] = sma_bb.iloc[-1]
    
    # Support and Resistance levels
    recent_highs = data['High'].rolling(window=20).max()
    recent_lows = data['Low'].rolling(window=20).min()
    indicators['resistance_level'] = recent_highs.iloc[-1]
    indicators['support_level'] = recent_lows.iloc[-1]
    
    # Average True Range (ATR)
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    tr = np.maximum(high_low, np.maximum(high_close, low_close))
    indicators['atr'] = tr.rolling(window=14).mean().iloc[-1]
    
    # Volume analysis
    indicators['avg_volume'] = data['Volume'].rolling(window=20).mean().iloc[-1]
    indicators['current_volume'] = data['Volume'].iloc[-1]
    indicators['volume_ratio'] = indicators['current_volume'] / indicators['avg_volume']
    
    # Price momentum
    indicators['price_change_1d'] = (indicators['current_price'] - indicators['previous_close']) / indicators['previous_close'] * 100
    indicators['price_change_5d'] = (data['Close'].iloc[-1] - data['Close'].iloc[-6]) / data['Close'].iloc[-6] * 100 if len(data) >= 6 else 0
    indicators['price_change_20d'] = (data['Close'].iloc[-1] - data['Close'].iloc[-21]) / data['Close'].iloc[-21] * 100 if len(data) >= 21 else 0
    
    return indicators

def format_currency(value: float, market_type: str) -> str:
    """Format currency based on market type"""
    currency_symbol = MARKET_CONFIG[market_type]['currency_symbol']
    return f"{currency_symbol}{value:.2f}"


def calculate_stop_loss_target(symbol: str, news_sentiment: float = 50) -> Dict[str, str]:
    """
    Calculate stop loss and target price for a given stock symbol based on technical indicators and news sentiment.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., 'AAPL', 'RELIANCE.NS')
        news_sentiment (int): News sentiment score from 1-100 (100 = very positive, 1 = very negative)
    
    Returns:
        Dict[str, str]: Dictionary containing target_price and stop_loss
    """
    
    # Detect market and check if open
    market_type = detect_market(symbol)
    
    if not is_market_open(market_type):
        return {
            "target_price": "Market is closed today",
            "stop_loss": "Market is closed today"
        }
    
    try:
        # Fetch stock data
        ticker = yf.Ticker(symbol)
        
        # Get different timeframes of data
        data_1d = ticker.history(period="1d", interval="1m")  # Intraday
        data_30d = ticker.history(period="30d", interval="1d")  # Daily
        data_90d = ticker.history(period="90d", interval="1d")  # Extended
        
        if len(data_30d) == 0:
            return {
                "target_price": "No data available for this symbol",
                "stop_loss": "No data available for this symbol"
            }
        
        # Calculate technical indicators
        indicators = calculate_technical_indicators(data_90d)
        
        # Get company info
        try:
            info = ticker.info
            company_name = info.get('longName', symbol)
            sector = info.get('sector', 'Unknown')
            beta = info.get('beta', 1.0)
        except:
            company_name = symbol
            sector = 'Unknown'
            beta = 1.0
        
        # Prepare technical analysis context
        technical_context = {
            'symbol': symbol,
            'company_name': company_name,
            'sector': sector,
            'market_type': market_type,
            'currency_symbol': MARKET_CONFIG[market_type]['currency_symbol'],
            'beta': beta,
            'news_sentiment': news_sentiment,
            **indicators
        }
        
        # Initialize LLM
        llm1 = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        llm1 = llm1.with_structured_output(StopLossResponse)
        llm2 = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        llm2 = llm2.with_structured_output(TargetPriceResponse)
        
        # Create stop loss calculation chain
        stop_loss_prompt = ChatPromptTemplate.from_template("""
        You are a professional stock analyst calculating stop loss for {symbol} ({company_name}) in {market_type} market.
        
        Technical Analysis Data:
        - Current Price: {currency_symbol}{current_price:.2f}
        - Previous Close: {currency_symbol}{previous_close:.2f}
        - 20-day SMA: {currency_symbol}{sma_20:.2f}
        - 50-day SMA: {currency_symbol}{sma_50:.2f}
        - RSI: {rsi:.2f}
        - ATR: {atr:.2f}
        - Volatility (20d): {volatility_20d:.4f}
        - Support Level: {currency_symbol}{support_level:.2f}
        - Resistance Level: {currency_symbol}{resistance_level:.2f}
        - Bollinger Lower Band: {currency_symbol}{bb_lower:.2f}
        - 1-day Price Change: {price_change_1d:.2f}%
        - 5-day Price Change: {price_change_5d:.2f}%
        - 20-day Price Change: {price_change_20d:.2f}%
        - Beta: {beta}
        - Volume Ratio: {volume_ratio:.2f}
        
        News Sentiment Score: {news_sentiment}/100 (Higher = More Positive)
        
        Calculate an appropriate stop loss level considering:
        1. Technical support levels
        2. ATR for volatility adjustment
        3. Recent price movements and trends
        4. Risk management (typically 2-5% below entry for normal volatility stocks)
        5. News sentiment impact on potential downside
        6. Market volatility and beta
        
        Provide ONLY the numerical stop loss price (without currency symbol) rounded to 2 decimal places.
        Consider that stop loss should be below current price and account for normal market fluctuations.
        """)
        
        # Create target price calculation chain
        target_price_prompt = ChatPromptTemplate.from_template("""
        You are a professional stock analyst calculating target price for {symbol} ({company_name}) in {market_type} market.
        
        Technical Analysis Data:
        - Current Price: {currency_symbol}{current_price:.2f}
        - Previous Close: {currency_symbol}{previous_close:.2f}
        - 20-day SMA: {currency_symbol}{sma_20:.2f}
        - 50-day SMA: {currency_symbol}{sma_50:.2f}
        - RSI: {rsi:.2f}
        - MACD: {macd:.4f}
        - MACD Signal: {macd_signal:.4f}
        - ATR: {atr:.2f}
        - Volatility (20d): {volatility_20d:.4f}
        - Support Level: {currency_symbol}{support_level:.2f}
        - Resistance Level: {currency_symbol}{resistance_level:.2f}
        - Bollinger Upper Band: {currency_symbol}{bb_upper:.2f}
        - 52-week High: {currency_symbol}{high_52w:.2f}
        - 52-week Low: {currency_symbol}{low_52w:.2f}
        - 1-day Price Change: {price_change_1d:.2f}%
        - 5-day Price Change: {price_change_5d:.2f}%
        - 20-day Price Change: {price_change_20d:.2f}%
        - Beta: {beta}
        - Volume Ratio: {volume_ratio:.2f}
        
        News Sentiment Score: {news_sentiment}/100 (Higher = More Positive)
        
        Calculate an appropriate target price considering:
        1. Technical resistance levels and breakout potential
        2. Moving average trends and momentum
        3. RSI levels (overbought/oversold conditions)
        4. MACD signals and momentum
        5. News sentiment impact on upside potential
        6. Risk-reward ratio (typically 1.5-3x the stop loss distance)
        7. Market volatility and beta
        8. Volume analysis for confirmation
        
        Provide ONLY the numerical target price (without currency symbol) rounded to 2 decimal places.
        Consider that target should be above current price and realistic based on technical analysis.
        """)
        
        # Create chains
        stop_loss_chain = stop_loss_prompt | llm1
        target_price_chain = target_price_prompt | llm2
        
        # Execute chains
        stop_loss_result = stop_loss_chain.invoke(technical_context)
        target_price_result = target_price_chain.invoke(technical_context)
        
        # Extract numerical values and format with currency
        try:
            stop_loss_value = stop_loss_result.stop_loss
            target_price_value = target_price_result.target_price
            
            return {
                "target_price": format_currency(target_price_value, market_type),
                "stop_loss": format_currency(stop_loss_value, market_type)
            }
        except ValueError:
            return {
                "target_price": "Unable to calculate - invalid data",
                "stop_loss": "Unable to calculate - invalid data"
            }
            
    except Exception as e:
        return {
            "target_price": f"Error: {str(e)}",
            "stop_loss": f"Error: {str(e)}"
        }

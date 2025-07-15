import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

# Market configuration
MARKET_CONFIG = {
    'US': {
        'timezone': 'US/Eastern',
        'currency_symbol': '$',
        'market_open_time': (9, 30),  # 9:30 AM
        'market_close_time': (16, 0),  # 4:00 PM
        'weekends': [5, 6],  # Saturday, Sunday
        'suffix_patterns': ['', '.US'],  # No suffix or .US
        'name': 'US Market'
    },
    'IN': {
        'timezone': 'Asia/Kolkata',
        'currency_symbol': '₹',
        'market_open_time': (9, 15),  # 9:15 AM
        'market_close_time': (15, 30),  # 3:30 PM
        'weekends': [5, 6],  # Saturday, Sunday
        'suffix_patterns': ['.NS', '.BO'],  # NSE (.NS) and BSE (.BO)
        'name': 'Indian Market'
    }
}

def detect_market(symbol):
    """Detect market type based on symbol suffix"""
    symbol = symbol.upper()
    
    # Check Indian market patterns
    if any(symbol.endswith(suffix) for suffix in MARKET_CONFIG['IN']['suffix_patterns']):
        return 'IN'
    
    # Check US market patterns or default to US
    return 'US'

def calculate_ema(data, span):
    """Calculate Exponential Moving Average"""
    return data.ewm(span=span, adjust=False).mean()

def calculate_linear_regression(y_values, days):
    """Calculate linear regression line and coefficient"""
    x_values = np.arange(len(y_values)).reshape(-1, 1)
    model = LinearRegression()
    model.fit(x_values, y_values)
    
    # Predict values for the line
    y_pred = model.predict(x_values)
    
    # Calculate R-squared
    r_squared = model.score(x_values, y_values)
    
    return y_pred, model.coef_[0], r_squared

def is_market_open(market_type='US'):
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

def get_trend_signal(current_price, ema_short, ema_long):
    """Determine trend signal based on EMA crossover"""
    if ema_short > ema_long and current_price > ema_short:
        return "Bullish", "green"
    elif ema_short < ema_long and current_price < ema_short:
        return "Bearish", "red"
    else:
        return "Sideways", "orange"

def format_currency(value, market_type='US'):
    """Format currency based on market type"""
    currency_symbol = MARKET_CONFIG[market_type]['currency_symbol']
    if market_type == 'IN':
        # Indian numbering system (lakhs, crores)
        if value >= 10000000:  # 1 crore
            return f"{currency_symbol}{value/10000000:.2f}Cr"
        elif value >= 100000:  # 1 lakh
            return f"{currency_symbol}{value/100000:.2f}L"
        else:
            return f"{currency_symbol}{value:.2f}"
    else:
        # US format
        return f"{currency_symbol}{value:.2f}"

def get_market_time_info(market_type='US'):
    """Get current market time information"""
    config = MARKET_CONFIG[market_type]
    now = datetime.now(pytz.timezone(config['timezone']))
    
    market_status = "Open" if is_market_open(market_type) else "Closed"
    
    if market_type == 'US':
        time_suffix = "ET"
    else:
        time_suffix = "IST"
    
    return {
        'current_time': now.strftime(f'%H:%M:%S {time_suffix}'),
        'current_date': now.strftime('%Y-%m-%d'),
        'market_status': market_status,
        'timezone': config['timezone'],
        'market_name': config['name']
    }

def stock_analysis_charts(symbol, save_html=False, filename_prefix=None):
    """
    Generate comprehensive stock analysis charts for AI agent as individual charts
    
    Parameters:
    symbol (str): Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'RELIANCE.NS', 'TCS.BO')
    save_html (bool): Whether to save charts as HTML files
    filename_prefix (str): Custom filename prefix for HTML output
    
    Returns:
    dict: Dictionary containing all chart figures and analysis summary
    """
    
    # Detect market type
    market_type = detect_market(symbol)
    config = MARKET_CONFIG[market_type]
    time_info = get_market_time_info(market_type)
    
    print(f"Fetching data for {symbol} ({config['name']})...")
    print(f"Market Status: {time_info['market_status']} | Time: {time_info['current_time']}")
    
    # Create ticker object
    ticker = yf.Ticker(symbol)
    
    # Get stock info
    try:
        info = ticker.info
        company_name = info.get('longName', symbol)
    except:
        company_name = symbol
    
    # Chart 1: Intraday data (if market open) or previous day
    if is_market_open(market_type):
        # Get intraday data for today
        intraday_data = ticker.history(period="1d", interval="1m")
        chart1_title = f"{company_name} ({symbol}) - Today's Intraday Price Movement"
        chart1_subtitle = f"Market Open | Last Updated: {time_info['current_time']}"
    else:
        # Get last trading day data
        intraday_data = ticker.history(period="1d", interval="1m")
        chart1_title = f"{company_name} ({symbol}) - Last Trading Day Price Movement"
        if len(intraday_data) > 0:
            last_trading_day = intraday_data.index[-1].strftime('%Y-%m-%d')
            chart1_subtitle = f"Market Closed | Last Trading Day: {last_trading_day}"
        else:
            chart1_subtitle = f"Market Closed | {time_info['current_time']}"
    
    # Charts 2-4: Historical data
    data_30d = ticker.history(period="30d", interval="1d")
    data_90d = ticker.history(period="90d", interval="1d")
    
    if len(data_30d) == 0 or len(data_90d) == 0:
        print(f"Error: No data available for {symbol}. Please check the symbol.")
        return None
    
    # Calculate EMAs
    data_30d['EMA_9'] = calculate_ema(data_30d['Close'], 9)
    data_30d['EMA_21'] = calculate_ema(data_30d['Close'], 21)
    
    data_90d['EMA_20'] = calculate_ema(data_90d['Close'], 20)
    data_90d['EMA_50'] = calculate_ema(data_90d['Close'], 50)
    
    # Calculate trend signal
    current_price = data_30d['Close'].iloc[-1]
    ema9_current = data_30d['EMA_9'].iloc[-1]
    ema21_current = data_30d['EMA_21'].iloc[-1]
    trend_signal, trend_color = get_trend_signal(current_price, ema9_current, ema21_current)
    
    # Calculate linear regression
    close_prices = data_30d['Close'].values
    lr_line, lr_coef, r_squared = calculate_linear_regression(close_prices, 30)
    
    # Create individual figures
    figures = {}
    
    # Chart 1: Intraday/Current Day Price Movement
    fig1 = go.Figure()
    
    if len(intraday_data) > 0:
        fig1.add_trace(
            go.Scatter(
                x=intraday_data.index,
                y=intraday_data['Close'],
                mode='lines',
                name='Price',
                line=dict(color='blue', width=2),
                hovertemplate=f'<b>Time</b>: %{{x}}<br><b>Price</b>: {format_currency(0, market_type).replace("0.00", "%{y:.2f}")}<extra></extra>'
            )
        )
        
        # Add high/low markers for intraday
        daily_high = intraday_data['High'].max()
        daily_low = intraday_data['Low'].min()
        
        fig1.add_hline(y=daily_high, line_dash="dash", line_color="green", 
                      annotation_text=f"Day High: {format_currency(daily_high, market_type)}")
        fig1.add_hline(y=daily_low, line_dash="dash", line_color="red", 
                      annotation_text=f"Day Low: {format_currency(daily_low, market_type)}")
    
    fig1.update_layout(
        title=dict(
            text=f"<b>{chart1_title}</b><br><span style='font-size:12px;'>{chart1_subtitle}</span>",
            x=0.5,
            font=dict(size=16)
        ),
        height=500,
        showlegend=True,
        hovermode='x unified',
        template='plotly_white',
        xaxis_title="Time",
        yaxis_title=f"Price ({config['currency_symbol']})"
    )
    
    figures['intraday'] = fig1
    
    # Chart 2: 30-Day Analysis with EMAs
    fig2 = go.Figure()
    
    fig2.add_trace(
        go.Scatter(
            x=data_30d.index,
            y=data_30d['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='black', width=2),
            hovertemplate=f'<b>Date</b>: %{{x}}<br><b>Price</b>: {format_currency(0, market_type).replace("0.00", "%{y:.2f}")}<extra></extra>'
        )
    )
    
    fig2.add_trace(
        go.Scatter(
            x=data_30d.index,
            y=data_30d['EMA_9'],
            mode='lines',
            name='EMA 9',
            line=dict(color='orange', width=1.5),
            hovertemplate=f'<b>Date</b>: %{{x}}<br><b>EMA 9</b>: {format_currency(0, market_type).replace("0.00", "%{y:.2f}")}<extra></extra>'
        )
    )
    
    fig2.add_trace(
        go.Scatter(
            x=data_30d.index,
            y=data_30d['EMA_21'],
            mode='lines',
            name='EMA 21',
            line=dict(color='purple', width=1.5),
            hovertemplate=f'<b>Date</b>: %{{x}}<br><b>EMA 21</b>: {format_currency(0, market_type).replace("0.00", "%{y:.2f}")}<extra></extra>'
        )
    )
    
    fig2.update_layout(
        title=dict(
            text=f"<b>{company_name} ({symbol}) - 30-Day Price Analysis with EMA Signals</b><br>"
                 f"<span style='font-size:12px;'>Current Trend: <span style='color:{trend_color}'>{trend_signal}</span> | {config['name']}</span>",
            x=0.5,
            font=dict(size=16)
        ),
        height=500,
        showlegend=True,
        hovermode='x unified',
        template='plotly_white',
        xaxis_title="Date",
        yaxis_title=f"Price ({config['currency_symbol']})"
    )
    
    figures['ema_analysis'] = fig2
    
    # Chart 3: Linear Regression Analysis
    fig3 = go.Figure()
    
    fig3.add_trace(
        go.Scatter(
            x=data_30d.index,
            y=data_30d['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='blue', width=2),
            hovertemplate=f'<b>Date</b>: %{{x}}<br><b>Price</b>: {format_currency(0, market_type).replace("0.00", "%{y:.2f}")}<extra></extra>'
        )
    )
    
    fig3.add_trace(
        go.Scatter(
            x=data_30d.index,
            y=lr_line,
            mode='lines',
            name=f'Linear Regression (R²={r_squared:.3f})',
            line=dict(color='red', width=2, dash='dash'),
            hovertemplate=f'<b>Date</b>: %{{x}}<br><b>Trend Line</b>: {format_currency(0, market_type).replace("0.00", "%{y:.2f}")}<extra></extra>'
        )
    )
    
    fig3.update_layout(
        title=dict(
            text=f"<b>{company_name} ({symbol}) - 30-Day Linear Regression Trend Analysis</b><br>"
                 f"<span style='font-size:12px;'>Regression Slope: {lr_coef:.4f} | R²: {r_squared:.3f} | {config['name']}</span>",
            x=0.5,
            font=dict(size=16)
        ),
        height=500,
        showlegend=True,
        hovermode='x unified',
        template='plotly_white',
        xaxis_title="Date",
        yaxis_title=f"Price ({config['currency_symbol']})"
    )
    
    figures['regression'] = fig3
    
    # Chart 4: 90-Day Long-term Analysis
    fig4 = go.Figure()
    
    fig4.add_trace(
        go.Scatter(
            x=data_90d.index,
            y=data_90d['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='black', width=2),
            hovertemplate=f'<b>Date</b>: %{{x}}<br><b>Price</b>: {format_currency(0, market_type).replace("0.00", "%{y:.2f}")}<extra></extra>'
        )
    )
    
    fig4.add_trace(
        go.Scatter(
            x=data_90d.index,
            y=data_90d['EMA_20'],
            mode='lines',
            name='EMA 20',
            line=dict(color='green', width=1.5),
            hovertemplate=f'<b>Date</b>: %{{x}}<br><b>EMA 20</b>: {format_currency(0, market_type).replace("0.00", "%{y:.2f}")}<extra></extra>'
        )
    )
    
    fig4.add_trace(
        go.Scatter(
            x=data_90d.index,
            y=data_90d['EMA_50'],
            mode='lines',
            name='EMA 50',
            line=dict(color='red', width=1.5),
            hovertemplate=f'<b>Date</b>: %{{x}}<br><b>EMA 50</b>: {format_currency(0, market_type).replace("0.00", "%{y:.2f}")}<extra></extra>'
        )
    )
    
    # Determine long-term trend
    ema20_current = data_90d['EMA_20'].iloc[-1]
    ema50_current = data_90d['EMA_50'].iloc[-1]
    long_term_trend = "Bullish" if ema20_current > ema50_current else "Bearish"
    long_term_color = "green" if long_term_trend == "Bullish" else "red"
    
    fig4.update_layout(
        title=dict(
            text=f"<b>{company_name} ({symbol}) - 90-Day Long-term Analysis with EMAs</b><br>"
                 f"<span style='font-size:12px;'>Long-term Trend: <span style='color:{long_term_color}'>{long_term_trend}</span> | {config['name']}</span>",
            x=0.5,
            font=dict(size=16)
        ),
        height=500,
        showlegend=True,
        hovermode='x unified',
        template='plotly_white',
        xaxis_title="Date",
        yaxis_title=f"Price ({config['currency_symbol']})"
    )
    
    figures['long_term'] = fig4
    
    # Calculate key metrics for summary
    price_change_30d = ((data_30d['Close'].iloc[-1] - data_30d['Close'].iloc[0]) / data_30d['Close'].iloc[0]) * 100
    price_change_90d = ((data_90d['Close'].iloc[-1] - data_90d['Close'].iloc[0]) / data_90d['Close'].iloc[0]) * 100
    
    
    # Save as HTML if requested
    if save_html:
        prefix = filename_prefix or f"{symbol.replace('.', '_')}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for chart_name, fig in figures.items():
            html_filename = f"{prefix}_{chart_name}.html"
            fig.write_html(html_filename)
            print(f"Chart saved as: {html_filename}")
    
    # Show all charts
    # for chart_name, fig in figures.items():
        # print(f"\nDisplaying {chart_name} chart...")
        # fig.show()
    
    json_figures = {name: fig.to_json() for name, fig in figures.items()}
    print(json_figures)

    return {
        'figures': json_figures,
        'analysis_summary': {
            'symbol': symbol,
            'company_name': company_name,
            'market_type': market_type,
            'market_name': config['name'],
            'current_price': current_price,
            'currency_symbol': config['currency_symbol'],
            'short_term_trend': trend_signal,
            'long_term_trend': long_term_trend,
            'performance_30d': price_change_30d,
            'performance_90d': price_change_90d,
            'regression_slope': lr_coef,
            'r_squared': r_squared,
            'market_status': time_info['market_status'],
            'current_time': time_info['current_time']
        }
    }


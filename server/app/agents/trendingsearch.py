from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_openai import OpenAI
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
import os
import re
from dotenv import load_dotenv
load_dotenv()

llm_search = OpenAI(temperature=0)
search = GoogleSerperAPIWrapper()
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")

tools = [
    Tool(
        name="Search",
        func=search.run,
        description="Search for current market information, trending stocks, and stock tickers"
    )
]

agent = initialize_agent(
    tools, 
    llm_search, 
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
    verbose=True, 
    max_iterations=5,
    handle_parsing_errors=True
)

enforced_prompt = """
Search for the most trending and actively traded stocks today. Look for:
1. Most active stocks by volume
2. Top gainers and losers
3. Trending stocks on social media
4. Stocks with high analyst interest

Find 10-15 stock ticker symbols (like AAPL, GOOGL, MSFT, TSLA, etc.) that are currently trending.
Return ONLY the ticker symbols in a comma-separated format: AAPL, GOOGL, MSFT, TSLA, NVDA, etc.

Do not include any explanations, just the ticker symbols.
"""


def extract_tickers(text):
    """Extract tickers from google search results"""
    ticker_pattern = r'\b[A-Z]{2,5}\b'
    tickers = re.findall(ticker_pattern, text)
    
    exclude_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BUT', 'WHAT', 'YOUR', 'WHEN', 'HIM', 'MY', 'HAS', 'BEEN', 'MORE', 'WHO', 'OIL', 'GAS', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY', 'ITS', 'DID', 'GET', 'MAY', 'SAY', 'SHE', 'USE', 'HOW', 'TOP', 'DAY', 'OUT', 'OFF', 'GET', 'END', 'WHY', 'LET', 'PUT', 'TOO', 'RUN', 'GOT', 'TRY', 'WIN', 'YES', 'BUY', 'SELL', 'HOLD', 'STOCK', 'STOCKS', 'MARKET', 'TRADING', 'PRICE', 'VOLUME', 'TODAY', 'WEEK', 'MONTH', 'YEAR', 'HIGH', 'LOW', 'CHANGE', 'PERCENT', 'GAIN', 'LOSS', 'SHARES', 'COMPANY', 'TECH', 'SECTOR', 'INDEX', 'FUND', 'TRADE', 'INVEST', 'MONEY', 'CASH', 'BANK', 'FINANCIAL', 'BUSINESS', 'NEWS', 'REPORT', 'EARNINGS', 'REVENUE', 'PROFIT', 'GROWTH', 'RATE', 'ANALYSIS', 'RECOMMENDATION', 'ANALYST', 'RESEARCH', 'UPGRADE', 'DOWNGRADE', 'TARGET', 'ESTIMATE', 'FORECAST', 'OUTLOOK', 'PERFORMANCE', 'RESULT', 'QUARTER', 'ANNUAL', 'MONTHLY', 'WEEKLY', 'DAILY', 'CURRENT', 'LATEST', 'RECENT', 'ACTIVE', 'POPULAR', 'TRENDING', 'VOLATILE', 'STABLE', 'RISING', 'FALLING', 'BULLISH', 'BEARISH', 'NEUTRAL', 'POSITIVE', 'NEGATIVE', 'STRONG', 'WEAK', 'BEST', 'WORST', 'MOST', 'LEAST', 'FIRST', 'LAST', 'NEXT', 'PREVIOUS', 'ABOVE', 'BELOW', 'BETWEEN', 'WITHIN', 'AROUND', 'OVER', 'UNDER', 'NEAR', 'FAR', 'CLOSE', 'OPEN', 'AFTER', 'BEFORE', 'DURING', 'WHILE', 'SINCE', 'UNTIL', 'FROM', 'WITH', 'WITHOUT', 'THROUGH', 'ACROSS', 'ALONG', 'AROUND', 'BEHIND', 'BEYOND', 'DURING', 'EXCEPT', 'INSIDE', 'OUTSIDE', 'TOWARD', 'WITHIN', 'AGAINST', 'BETWEEN', 'THROUGH', 'ACROSS', 'ALONG', 'AROUND', 'BEHIND', 'BEYOND', 'DURING', 'EXCEPT', 'INSIDE', 'OUTSIDE', 'TOWARD', 'WITHIN', 'AGAINST', 'BETWEEN'}
    
    
    filtered_tickers = [ticker for ticker in tickers if ticker not in exclude_words]
    unique_tickers = list(dict.fromkeys(filtered_tickers))  
    
    return unique_tickers[:15]

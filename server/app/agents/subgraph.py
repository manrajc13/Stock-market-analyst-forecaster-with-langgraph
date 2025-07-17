from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langgraph.graph.message import add_messages 
from typing import Dict, List, Annotated, TypedDict, Optional
from pydantic import Field, BaseModel
from langchain_openai import ChatOpenAI

FUNDAMENTAL_ANALYST_PROMPT = """
You are a senior fundamental analyst with expertise in equity research and quantitative analysis. You specialize in evaluating company performance for {company} using comprehensive data analysis including stock prices, technical indicators, financial metrics, and market sentiment.

Your task is to provide a detailed, data-driven fundamental analysis using ONLY the specific values provided below. For every metric, ratio, or indicator mentioned, you must:
1. State the exact numerical value
2. Explain what this specific value means in market context
3. Interpret the implications for investment decisions

**DATA SOURCES:**

1. **Stock Summary Data** — Current market performance and technical analysis:
   {{stock_summary}} // you will fetch this from get_stock_summary tool

2. **News Sentiment Analysis** — Market sentiment and thematic analysis:
   {{news_sentiment}} // you will fetch this from get_news_sentiment tool

---

**ANALYSIS REQUIREMENTS:**

Write a comprehensive, structured analysis under the following headings. For each section, use precise data points and explain their significance:

📈 **Price Performance Analysis**
- State the exact current price in {currency_symbol} and explain its position relative to recent trading
- Report the precise 5-day change percentage and interpret whether this indicates short-term momentum or consolidation
- Analyze the 52-week range positioning: calculate and state the exact percentage of where current price sits within the range (e.g., "trading at X% of its 52-week range")
- Evaluate average volume context: state the exact volume figure and explain if current trading activity suggests institutional interest or retail participation

📈 **Trend Analysis & Momentum**
- **Linear Trend**: Report the exact slope value and explain what this numerical trend indicates about price trajectory over the past 21 days
- **EMA Analysis**: State precise EMA-9 and EMA-21 values, calculate the exact spread between them, and explain the significance of this relationship
- **Crossover Signals**: Identify the specific crossover status and explain its technical implications
- **Trend Classification**: Confirm the trend direction and provide quantitative justification using the slope and EMA data

📊 **Technical Indicator Deep Dive**
- **RSI Analysis**: State the exact RSI value and explain its position within the 0-100 scale. Interpret momentum strength and potential reversal signals
- **Stochastic Oscillator**: Report the precise value and explain its overbought/oversold implications within the 0-100 range
- **MACD Analysis**: State exact MACD and MACD Signal values, calculate the difference, and explain the momentum implications of this relationship
- **VWAP Assessment**: Compare current price to exact VWAP value and explain what this spread indicates about institutional vs retail sentiment

📉 **Financial Valuation Metrics**
- **P/E Ratio**: State the exact P/E value and benchmark it against sector/market averages. Explain if this indicates overvaluation, undervaluation, or fair value
- **Price-to-Book**: Report the precise P/B ratio and explain what this reveals about market perception vs book value
- **Debt-to-Equity**: State the exact D/E ratio and interpret the company's leverage profile and financial risk
- **Profit Margins**: Report the precise margin percentage and explain the company's operational efficiency and competitive positioning

📰 **News Sentiment Integration**
- Summarize the overall sentiment classification (Positive/Negative/Neutral) with the exact sentiment score
- Identify specific themes from the news analysis and explain their potential impact on stock performance
- Correlate news sentiment with current technical indicators to assess if price action aligns with fundamental developments

📌 **Investment Recommendation & Risk Assessment**
Based on the quantitative analysis above, provide a definitive recommendation: **BUY**, **HOLD**, or **SELL**

**Justification Requirements:**
- Use at least 3 specific data points to support your recommendation
- Quantify the risk-reward profile using exact metrics
- Identify key price levels or metric thresholds that would change your recommendation
- Highlight any conflicting signals between technical and fundamental data
- Provide specific entry/exit criteria based on the analyzed metrics

**Critical Guidelines:**
- Use ONLY the exact values provided in the data
- If any metric is missing or unavailable, explicitly state "Data not provided"
- Avoid generic market commentary - focus on company-specific quantitative insights
- Explain the significance of each number in context
- Provide actionable insights based on precise data analysis
- Maintain professional, analytical tone throughout

---

**REMEMBER**: Every statement must be supported by specific numerical data from the provided inputs. Explain not just what the numbers are, but what they mean for investors and why they matter in the current market context.
"""

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
    
    if any(symbol.endswith(suffix) for suffix in MARKET_CONFIG['IN']['suffix_patterns']):
        return 'IN'
    
    return 'US'


class SubState(TypedDict):
  messages: Annotated[List, add_messages]
  stock: str


subgraph_builder = StateGraph(SubState)


from ..tools .news import News, get_news_sentiment
from ..tools .stocksummary import get_stock_summary

tools = [get_news_sentiment, get_stock_summary]

import os 
from dotenv import load_dotenv
load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(model = 'gpt-4o-mini', temperature = 0.1)
llm_with_tool = llm.bind_tools(tools)


def fundamental_analyst(state: SubState):
    currency_symbol = MARKET_CONFIG[detect_market(state['stock'])]
    messages = [
        SystemMessage(content=FUNDAMENTAL_ANALYST_PROMPT.format(company=state['stock'], currency_symbol = currency_symbol)),
    ]  + state['messages']
    return {
        'messages': llm_with_tool.invoke(messages)
    }

subgraph_builder.add_node('fundamental_analyst', fundamental_analyst)
subgraph_builder.add_edge(START, 'fundamental_analyst')
subgraph_builder.add_node(ToolNode(tools))
subgraph_builder.add_conditional_edges('fundamental_analyst', tools_condition)
subgraph_builder.add_edge('tools', 'fundamental_analyst')
subgraph_builder.add_edge('fundamental_analyst', END)

stock_analysis_graph = subgraph_builder.compile()

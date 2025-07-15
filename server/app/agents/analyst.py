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


def detect_market(symbol: str) -> str:
    """Detect market type based on symbol suffix"""
    symbol = symbol.upper()
    if any(symbol.endswith(suffix) for suffix in MARKET_CONFIG['IN']['suffix_patterns']):
        return 'IN'
    return 'US'



FUNDAMENTAL_ANALYST_PROMPT = """
You are a fundamental analyst specializing in evaluating company (whose symbol is {company}) performance based on stock prices, technical indicators, financial metrics and News.
Your task is to provide a comprehensive summary of the fundamental analysis for a given stock.

1. **Stock Summary** — gives:
   - Current price, 5-day % change, 52-week range, average volume
   - Technical indicators: RSI, Stochastic Oscillator, MACD, MACD Signal, VWAP
   - Financial metrics: P/E ratio, price-to-book, debt-to-equity, profit margin

   {stock_summary}

2. **News Sentiment** — summarizes current news articles and sentiment around the company

  {news_sentiment}

---

Using this data, write a short, structured analysis under the following headings:

📈 **Price Summary**
Summarize current price in {currency_symbol}, recent change %, and where the stock sits in its 52-week range. Mention volume if it's unusually high or low.

📈 **Trend Detection**
- Linear price trend slope over past 21 days
- EMA-9 vs EMA-21 crossover signal
- Final trend classification: Bullish, Bearish, or Sideways

📊 **Technical Indicators**
Interpret RSI (overbought/oversold), MACD crossover, and Stochastic Oscillator. Be specific — explain what each indicator implies about short-term movement.

📉 **Financial Metrics**
Assess if the stock is undervalued, overvalued, high-debt, or has strong profitability based on the metrics. Avoid generic interpretations.

📰 **News Sentiment**
Summarize sentiment as Positive, Negative, or Mixed. Mention key themes or concerns (e.g. innovation, leadership, legal risks).

📌 **Investment Recommendation**
Give a final call: **Buy**, **Hold**, or **Sell** — based only on the facts above. Justify your verdict clearly. Avoid vague language like “it depends.” Highlight any red flags or strong signals.

---

Only use information that was explicitly given. If a value is missing or unknown, say so directly. Keep it professional, concise, and investor-friendly.
"""

from langchain.pydantic_v1 import BaseModel, Field 
from typing import List, Dict, Optional, Any, TypedDict, Annotated


class Verdict(BaseModel):
  verdict: str = Field(..., description = "Final call: Buy, Hold, or Sell — based only on the facts above.")
  reasoning: str = Field(..., description = "Justify your verdict clearly. Avoid vague language like “it depends.” Highlight any red flags or strong signals.")

class Analyst_Output(BaseModel):
  price_summary : str = Field(..., description = "Summarize current price, recent change %, and where the stock sits in its 52-week range. Mention volume if it's unusually high or low.")
  trend_detection : str = Field(..., description = "Linear price trend slope over past 21 days, EMA-9 vs EMA-21 crossover signal, Final trend classification")
  technical_indicators : str = Field(..., description = "Interpret RSI (overbought/oversold), MACD crossover, and Stochastic Oscillator. Be specific — explain what each indicator implies about short-term movement.")
  financial_metrics : str = Field(..., description = "Assess if the stock is undervalued, overvalued, high-debt, or has strong profitability based on the metrics. Avoid generic interpretations.")
  news_sentiment : str = Field(..., description = "Summarize sentiment as Positive, Negative, or Mixed. Mention key themes or concerns (e.g. innovation, leadership, legal risks).")
  investment_recommendation : Verdict 


from langchain_openai import ChatOpenAI 
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
import json

import yfinance as yf 


from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages.base import BaseMessage


from ..tools .finance_calc import calculate_stop_loss_target
from ..tools .news import get_news_sentiment, News
from ..tools .stocksummary import get_stock_summary



from dotenv import load_dotenv
import os 
load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")



class State(TypedDict, total = False):
    messages: Annotated[List[BaseMessage], add_messages]
    stock: str
    sentiment: News
    stop_loss: float
    target_price: float
    stock_summary: Dict[str,Any]
    analysis: Analyst_Output
    trending_stocks: Dict[str, Any]





def router_node(state : State):
    last_msg = state["messages"][-1].content.lower()

    if "trending" in last_msg or "worth buying" in last_msg:
        return "recommend_trending_stocks"
    else:
        return "analyze_stock"


def get_trending_stocks(limit: int = 5):
  return [
      "AAPL", "RS", "MSFT", "GOOGL", "TSLA", "NVDA"
  ]

def recommend_trending_stocks_node(state : State):
    tickers = get_trending_stocks()[:5]
    data = {}
    for stock in tickers:
      dat = yf.Ticker(stock)
      opening_price = dat.history().iloc[-1]['Open']
      closing_price = dat.analyst_price_targets['current']
      points_change = closing_price - opening_price
      percentage_change = (points_change / opening_price) * 100

      data[stock] = {"points_change": round(points_change, 2), "percentage_change" : round(percentage_change, 2)}

    return {
        "messages": state["messages"] + [AIMessage(content=f"The trending stocks are \n\n{json.dumps(data, indent=2)}")],
        "trending_stocks": data 
    }




graph_builder = StateGraph(State)

def company_news(state : State):
  news_sentiment = get_news_sentiment(state['stock'])
  return {"sentiment": news_sentiment}

def stock_metrics_and_summary(state: State):
  stock_summary = get_stock_summary(state['stock'])
  return {"stock_summary": stock_summary}

def stop_loss_and_target_price(state: State):
  predictions = calculate_stop_loss_target(state['stock'], news_sentiment = state['sentiment'].sentiment_score)
  return {"stop_loss": predictions['stop_loss'], "target_price": predictions['target_price']}


llm_with_output = ChatOpenAI(model = 'gpt-4o-mini')
llm_with_output = llm_with_output.with_structured_output(Analyst_Output)



def finance_analyst(state : State):
  currency_symbol = MARKET_CONFIG[detect_market(state['stock'])]
  messages = [
        SystemMessage(content=FUNDAMENTAL_ANALYST_PROMPT.format(company=state['stock'], stock_summary = state['stock_summary'], news_sentiment = state['sentiment'], currency_symbol = currency_symbol)),
    ]  + state['messages']
  analysis_output = llm_with_output.invoke(messages)
  return {
        'analysis': analysis_output
    }


graph_builder.add_node(company_news, 'company_news')
graph_builder.add_node(stock_metrics_and_summary, 'stock_metrics_and_summary')
graph_builder.add_node(stop_loss_and_target_price, 'stop_loss_and_target_price')
graph_builder.add_node(finance_analyst, 'finance_analyst')

graph_builder.add_edge('company_news', 'stock_metrics_and_summary')
graph_builder.add_edge('stock_metrics_and_summary', 'stop_loss_and_target_price')
graph_builder.add_edge('stop_loss_and_target_price', 'finance_analyst')
graph_builder.add_edge('finance_analyst', END)




graph_builder.add_node("recommend_trending", recommend_trending_stocks_node)

graph_builder.add_conditional_edges(START,
                                router_node,
    {
    "analyze_stock": "company_news",
    "recommend_trending_stocks": "recommend_trending"
})
graph_builder.add_edge("recommend_trending", END)

analyst_graph = graph_builder.compile()


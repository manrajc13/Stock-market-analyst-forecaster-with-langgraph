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


from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langgraph.graph.message import add_messages 
from typing import Dict, List, Annotated, TypedDict, Optional, Any
import json
import yfinance as yf

from langgraph.graph import StateGraph, END, START
from langchain_core.messages.base import BaseMessage

from ..tools .news import News
from .trendingsearch import extract_tickers
from .subgraph import stock_analysis_graph, SubState
from .structuringnode import structuring_chain




def get_latest_news_sentiment_tool_message(state : SubState):
    """
    Extracts the most recent ToolMessage for the 'get_news_sentiment' tool from agent state['messages'].
    
    Args:
        state (dict): The agent state containing 'messages'.

    Returns:
        ToolMessage or None: The ToolMessage for the latest 'get_news_sentiment' tool call, if found.
    """
    last_tool_call_id = None

    for message in reversed(state.get('messages', [])):
        if isinstance(message, AIMessage):
            tool_calls = message.tool_calls
            if tool_calls:
                for tool_call in tool_calls:
                    if tool_call['name'] == 'get_news_sentiment':
                        last_tool_call_id = tool_call['id']
                        break
        if last_tool_call_id:
            break

    if last_tool_call_id:
        for message in state['messages']:
            if isinstance(message, ToolMessage) and message.tool_call_id == last_tool_call_id:
                return message.content

    return None 



class TopState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    stock: str
    news_sentiment: News
    analyst_output: str 
    trending_stocks: Dict[str,Any]



def router_node(state : TopState):
    last_msg = state["messages"][-1].content.lower()

    if "trending" in last_msg or "worth buying" in last_msg:
        return "recommend_trending_stocks"
    else:
        return "analyze_stock"


def get_trending_stocks(limit: int = 5):
    return extract_tickers()

def recommend_trending_stocks_node(state : TopState):
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

def structure_analyst_output(state: TopState):
    analyst_output = state['analyst_output']
    for i in range(3):
        try:
            result = structuring_chain(analyst_output)  
            return {
                "messages": [AIMessage(content=str(result))]
            }
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")  
            continue
    
    raise Exception("Could not structure the analyst output")


graph_builder = StateGraph(TopState)





def finance_analyst(state : TopState):
  state = stock_analysis_graph.invoke({"messages" : [HumanMessage(content = "Should I buy this stock?")], "stock": "AAPL"})
  return {
        'analyst_output': state['messages'][-1].content,
        'news_sentiment': get_latest_news_sentiment_tool_message(state)
    }



graph_builder.add_node(finance_analyst, 'finance_analyst')


graph_builder.add_node("recommend_trending", recommend_trending_stocks_node)

graph_builder.add_node("structure_analyst_output", structure_analyst_output)


graph_builder.add_conditional_edges(START,
                                router_node,
    {
    "analyze_stock": "finance_analyst",
    "recommend_trending_stocks": "recommend_trending"
})
graph_builder.add_edge('finance_analyst', 'structure_analyst_output')
graph_builder.add_edge('structure_analyst_output', END)
graph_builder.add_edge("recommend_trending", END)

TopGraph = graph_builder.compile()


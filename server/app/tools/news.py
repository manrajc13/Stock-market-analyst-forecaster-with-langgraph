from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing import Annotated, List, Dict, TypedDict
from langchain_core.tools import tool
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from typing import Dict, Any
import warnings
warnings.filterwarnings('ignore')

import os 
from dotenv import load_dotenv
load_dotenv()



def get_news(stock: str) -> list:
    """
    Fetch relevant news articles for a given stock ticker.

    Parameters:
    - stock (str): The stock ticker symbol.

    Returns:
    - list: A list of dictionaries containing title, summary, URL, and publication date of relevant news articles.
    """
    try:
        # Fetch the ticker object and retrieve its news
        ticker = yf.Ticker(stock)
        news = ticker.news

        if not news:
            print(f"No news found for {stock}.")
            return []

        # Filter news with contentType='STORY'
        relevant_news = [
            item for item in news if item.get('content', {}).get('contentType') == 'STORY'
        ]

        all_news = []
        for i, item in enumerate(relevant_news):
            try:
                content = item.get('content', {})
                current_news = {
                    'title': content.get('title'),
                    'summary': content.get('summary'),
                    'url': content.get('canonicalUrl', {}).get('url'),
                    'pubdate': content.get('pubDate', '').split('T')[0],
                }
                all_news.append(current_news)
            except Exception as e:
                print(f"Error processing news {i}: {e}")
                continue

        return all_news

    except Exception as e:
        print(f"An error occurred while fetching news for {stock}: {e}")
        return None

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq



# Step 2: Define the prompt template
from pydantic import BaseModel, Field
from typing import Dict, List


class News(BaseModel):
    news_rating: Dict[str, List[str]] = Field(..., description="Dictionary where each key is a news article title and each value is a list containing [sentiment, url]")
    overall_news_summary: str = Field(..., description="Overall news summary in 4-5 lines")
    overall_sentiment: str = Field(..., description="Classify the overall news analysis about the company and its stock into POSITIVE, NEGATIVE OR NEUTRAL")
    sentiment_score: int = Field(..., description="Overall sentiment score of the news collected from 1 to 100, higher being positive.")


llm = ChatGroq(model="deepseek-r1-distill-llama-70b", groq_api_key = os.getenv("groq_api_key_dev"))
llm_with_structure = llm.with_structured_output(News)

PROMPT = """
You are a senior financial analyst with 15+ years of experience in equity research and sentiment analysis. Your expertise lies in evaluating how news events impact stock prices and investor sentiment.

**TASK OVERVIEW:**
Analyze the provided news articles for {stock} and assess their collective impact on stock performance and investment attractiveness.

**DETAILED INSTRUCTIONS:**

**Step 1: Individual Article Analysis**
For each news article, determine sentiment using these criteria:
- **POSITIVE**: Revenue growth, profit increases, strategic partnerships, product launches, market expansion, positive analyst upgrades, regulatory approvals, cost reductions, dividend increases
- **NEGATIVE**: Revenue decline, losses, layoffs, legal issues, regulatory problems, competitor threats, downgrades, product recalls, management changes (negative context)
- **NEUTRAL**: Routine announcements, minor operational updates, mixed signals, or unclear impact

**Step 2: News Rating Dictionary**
Create a dictionary mapping each article title to [sentiment, url]. Ensure:
- Article titles are exact matches from the provided data
- Sentiment is exactly "POSITIVE", "NEGATIVE", or "NEUTRAL"
- URLs are complete and accurate

**Step 3: Overall Summary (4-5 lines)**
Synthesize the key themes and their market implications:
- Highlight the most significant news items affecting stock performance
- Identify trending patterns (growth trajectory, operational challenges, market positioning)
- Assess potential short-term and medium-term stock price impact
- Consider broader market context and sector-specific factors
- Recommend buying, selling or holding based on the sentiment of the news.

**Step 4: Overall Sentiment Classification**
Determine the aggregate sentiment based on:
- Weighted impact of each news item (major announcements > routine updates)
- Market materiality (earnings reports > press releases)
- Investor perception and likely market reaction
- Balance of positive vs negative developments

**Step 5: Sentiment Score (1-100)**
Assign a numerical score where:
- 1-25: Highly negative (major concerns, significant downside risk)
- 26-40: Negative (concerning developments, potential headwinds)
- 41-60: Neutral (mixed signals, no clear direction)
- 61-80: Positive (favorable developments, growth potential)
- 81-100: Highly positive (exceptional news, strong upside potential)

**IMPORTANT CONSIDERATIONS:**
- Prioritize news items that directly impact financial performance
- Consider the credibility and timing of news sources
- Factor in market sentiment and investor psychology
- Evaluate news within the context of current market conditions
- Focus on actionable insights for investment decisions

**News Articles for Analysis:**
{articles}

**CRITICAL REQUIREMENTS:**
- Analyze ALL provided articles thoroughly
- Ensure sentiment classifications are consistent and well-reasoned
- Provide specific examples from the news to support your overall assessment
- Consider both explicit information and implied market implications
- Maintain objectivity while acknowledging potential biases in news reporting
"""

prompt_template = ChatPromptTemplate.from_messages(
    [
        ('system', PROMPT),
        ('human', "I would like to analyze the news articles related to the stock {stock}.")
    ]
)

chain_news_sentiment = prompt_template | llm_with_structure

@tool
def get_news_sentiment(ticker: str) -> Dict:
    """Fetches sentiment about the company and its stock based on current financial news."""
    news = get_news(ticker)
    if not news:
        return {"error": "No news found"}

    for i in range(3):
      try:
        result = chain_news_sentiment.invoke(
            {
                "stock": ticker,
                "articles": news
            }
        )
        return result.dict()
      except Exception:
        continue
    raise Exception("Failed to get news sentiment")
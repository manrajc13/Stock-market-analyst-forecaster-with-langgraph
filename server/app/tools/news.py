import yfinance as yf 
import pandas as pd 

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.tools import tool


from langchain.pydantic_v1 import BaseModel, Field  

from typing import Dict, Optional, List 

class News(BaseModel):
    news_rating: Dict[str, List[str]] = Field(..., description="Dictionary of news rating along with the links")
    overall_news_summary: str = Field(..., description="Overall news summary")
    investment_recommendation: str = Field(..., description="POSITIVE or NEGATIVE or NEUTRAL")
    sentiment_score: int = Field(..., description="Overall sentiment score of the news collected from 1 to 100 , more being positive.")  


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
    

PROMPT = """
You are an expert financial analyst. I will provide you with a list of news articles related to a specific stock. Your tasks are as follows:

1. **Sentiment Analysis:**
   - For each news article, evaluate its sentiment as 'Positive', 'Negative', or 'Neutral'.
   - Present your evaluation in a dictionary format where each key is the article's title, and the corresponding value is the assessed sentiment.

2. **Comprehensive Summary and Investment Recommendation:**
   - After analyzing all the articles, provide a concise summary that encapsulates the overall sentiment and key points from the news.
   - Based on this summary, advise whether investing in the stock is advisable at this time, supporting your recommendation with reasons derived from the news analysis.

**News Articles:**

{articles}

**Output Format:**

1. **Sentiment Analysis Dictionary:**

   ```json
   {{
       "Article Title 1": ["Positive" , url for the news]
       "Article Title 2": ["Negative",  url for the news]
       "Article Title 3": "[Neutral", url for the news]
       ...
   }}
2. Summary: [Your summary here]
3. Investment Recommendation: [Your recommendation here]
"""


prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", PROMPT),
        ("human", "I would like to analyze the news articles related to the stock {stock}")
    ]
)


from dotenv import load_dotenv
import os 
load_dotenv()

llm = ChatGroq(model = 'llama-3.3-70b-versatile', groq_api_key = os.environ.get("groq_api_key_free"))

llm_with_structure = llm.with_structured_output(News)

chain_news_sentiment = prompt_template | llm_with_structure




def get_news_sentiment(ticker: str) -> Dict:
    """Fetches sentiment about the company based on current financial news."""

    news = get_news(ticker)
    result = chain_news_sentiment.invoke(
        {
            "stock": ticker,
            "articles": news
        }
    )
    return result


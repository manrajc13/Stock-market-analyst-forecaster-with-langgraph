from pydantic import BaseModel, Field

class InvestmentRecommendationAndRiskAssessment(BaseModel):
    call: str = Field(..., description="Final call to BUY,SELL or HOLD")
    justification: str = Field(..., description="Justification for the investment recommendation")
    risk_reward_profile: str = Field(..., description="Risk reward profile analysis")
    entry_exit_criteria: str = Field(..., description="Entry and exit criteria")
    conflicting_signals: str = Field(..., description="Analysis of conflicting signals")

class StockAnalysisOutput(BaseModel):
    """Structured output for stock analysis with main headings"""
    price_performance_analysis: str = Field(..., description="Price performance analysis section")
    trend_analysis_and_momentum: str = Field(..., description="Trend analysis and momentum section")
    technical_indicator_deep_dive: str = Field(..., description="Technical indicator deep dive section")
    financial_valuation_metrics: str = Field(..., description="Financial valuation metrics section")
    news_sentiment_integration: str = Field(..., description="News sentiment integration section")
    investment_recommendation_and_risk_assessment: InvestmentRecommendationAndRiskAssessment = Field(..., description="Investment recommendation and risk assessment with subheadings")



structure_prompt = """
        You are a financial data analyst tasked with restructuring stock analysis content into a precise, well-organized format.

        TASK: Extract and reorganize the following stock analysis into exactly 6 main sections with specific subsections as specified.

        REQUIREMENTS:
        1. Extract ALL relevant content from each section - do not summarize or truncate
        2. Maintain all numerical data, percentages, and specific metrics
        3. Preserve the analytical insights and interpretations
        4. If a section is missing from the source, write "Data not available in source analysis"
        5. Keep the professional financial analysis tone

        SOURCE ANALYSIS:
        {unstructured_analysis}

        REQUIRED OUTPUT STRUCTURE:

        **Section 1: Price Performance Analysis**
        - Extract: Current price, price changes, 52-week ranges, volume data, and all price-related metrics
        - Include: All specific numbers, percentages, and price movement interpretations

        **Section 2: Trend Analysis And Momentum**
        - Extract: Trend slopes, EMA values, crossover signals, momentum indicators
        - Include: All trend classifications, momentum strength assessments, and directional analysis

        **Section 3: Technical Indicator Deep Dive**
        - Extract: RSI, Stochastic, MACD, VWAP, and other technical indicators
        - Include: All indicator values, interpretations, and signal analysis

        **Section 4: Financial Valuation Metrics**
        - Extract: P/E ratios, P/B ratios, debt metrics, profit margins, and valuation assessments
        - Include: All financial ratios, comparisons, and valuation interpretations

        **Section 5: News Sentiment Integration**
        - Extract: Sentiment scores, sentiment classifications, news themes, and correlation analysis
        - Include: All sentiment-related data and market psychology insights

        **Section 6: Investment Recommendation & Risk Assessment**
        This section has 5 mandatory subsections:
        - **Call**: Extract the final call to BUY, SELL, or HOLD
        - **Justification**: Extract the detailed reasoning behind the investment recommendation
        - **Risk Reward Profile**: Extract risk levels, reward potential, and risk-reward analysis
        - **Entry/Exit Criteria**: Extract entry points, exit strategies, price targets, and stop-loss levels
        - **Conflicting Signals**: Extract any contradictory indicators and how to resolve them

        CRITICAL: Ensure each section contains substantial content. Do not leave any section empty or with minimal content.
  """




from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
import os 
from dotenv import load_dotenv

load_dotenv()
os.environ['groq_api_key_dev'] = os.getenv("groq_api_key_dev")


def structuring_chain(analysis: str):
  llm = ChatGroq(model = 'deepseek-r1-distill-llama-70b', groq_api_key = os.getenv("groq_api_key_dev"))
  structuring_llm = llm.with_structured_output(StockAnalysisOutput)
  prompt = PromptTemplate.from_template(structure_prompt)
  chain = prompt | structuring_llm 
  result = chain.invoke({"unstructured_analysis": analysis}) 
  return result.dict()
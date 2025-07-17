# Stock Market Forecasting and Sentiment Analysis

A comprehensive stock analysis platform that uses a single LangGraph agentic workflow to address user queries for market insights, real-time stock price movement charts, and news sentiment analysis.

## Overview

This application leverages a unified agentic workflow to provide:
- **Market Insights**: Comprehensive stock analysis with technical indicators and financial metrics
- **Real-time Charts**: Interactive stock price movement visualizations
- **News Sentiment**: Real-time news analysis with sentiment scoring for informed decision making

## Tech Stack
**model**: OpenAI GPT4.o mini, deepseek-r1-distill-llama-70b
**database**: PostgreSQL
**authentication**: JWT Tokens using OAuth
**Agentic Framework**: Langgraph, Langchain
**Tools**: SerperDev, YFinance
**Frontend**: Reactjs, TailwindCSS
**Backend**: Fastapi
## Technical Analysis Framework

Our system analyzes stocks using comprehensive financial metrics to classify market sentiment as **bullish**, **bearish**, or **sideways**:

### Price Performance Metrics
- **Current Price**: Latest closing price of the stock
- **5-Day Change**: Percentage change in price over the last 5 trading days
- **52-Week Range**: Highest and lowest stock prices in the last 52 weeks
- **Average Volume**: Daily trading volume indicating market interest

### Technical Indicators
- **RSI (Relative Strength Index)**: Measures momentum; values >70 indicate overbought conditions, <30 indicate oversold
- **Stochastic Oscillator**: Momentum indicator; >80 suggests overbought, <20 suggests oversold
- **MACD (Moving Average Convergence Divergence)**: Measures trend strength and momentum
- **VWAP (Volume Weighted Average Price)**: Shows average price based on volume for intraday trends

### Financial Health Metrics
- **P/E Ratio**: Price-to-earnings ratio for valuation assessment
- **Price-to-Book**: Market value relative to book value
- **Debt-to-Equity**: Financial leverage and risk indicator
- **Profit Margins**: Operational efficiency measurement

### Trend Detection
- **Linear Slope**: Price trajectory over time
- **EMA Analysis**: 9-day and 21-day exponential moving averages
- **Crossover Signals**: Moving average crossovers for trend confirmation
- **Trend Classification**: Bullish, bearish, or sideways market sentiment

## Installation & Setup

### Backend Setup

Navigate to the server directory:
```bash
cd server
```
Install Backend Dependencies
```bash
pip install -r requirments.txt
```
Setup .env file 
```bash
OPENAI_API_KEY=<your openai api key>
groq_api_key_dev=<your groq api key>
SERPER_API_KEY=<your serperdev api key>
```
Start server
```bash
uvicorn app.main: app -reload
```

### Frontend Setup

Navigate to the client directory:
```bash
cd client
```
Install Frontend Dependencies 
```bash
npm install
```
Start Web app
```bash
npm run dev
```



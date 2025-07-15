from fastapi import FastAPI, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from .database .db import create_user, get_user_by_email, delete_user_by_email
from .database .models import get_db
from .utils import hash_password, verify
from .auth import create_access_token, get_current_user, verify_access_token
from langchain_core.messages import HumanMessage


from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str 


from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = True, 
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

@app.post('/login')
def login(credentials: LoginRequest, response: Response, db: Session = Depends(get_db)):
    try:
        email = credentials.email
        password = credentials.password
        user = get_user_by_email(db, email)
        if user:
            response.status_code = status.HTTP_200_OK
            # authentication logic would go here 
            if not verify(password, user.password):
                response.status_code = status.HTTP_401_UNAUTHORIZED
                return {"detail": "Invalid Password"}
            
            access_token = create_access_token(data = {"user_id" : user.id})

            return {"message": "Login successful", "access_token": access_token}
        else:
            raise HTTPException(status_code=404, detail="User not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/register')
def register(credentials: RegisterRequest, db: Session = Depends(get_db)):
    try:
        email = credentials.email 
        name = credentials.name  
        password = credentials.password 
        user = get_user_by_email(db, email)
        if user:
            raise HTTPException(status_code=400, detail="Email already registered")
        user = create_user(db, email, name, password)
        return {"message": "User created successfully", "user_id": user.id}
    except Exception as e:  
        raise HTTPException(status_code=500, detail=str(e))


@app.delete('/user')
def delete_user(credentials: LoginRequest, response: Response, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = get_user_by_email(db, credentials.email)
    
    # 2. Ensure that the user is deleting their own account
    if not user or user.id != int(user_id.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this account")

    # 3. Confirm password
    if not verify(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    return delete_user_by_email(db, credentials.email)
    

import json


from .agents .analyst import analyst_graph
from .tools .chart_cache import stock_analysis_charts

class QueryRequest(BaseModel):
    query: str
    ticker: str

# main.py

# ... other imports and code ...

@app.post("/query")
def query(req: QueryRequest, request: Request, response: Response, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    # Invoke the analyst graph
    state = analyst_graph.invoke({
        "messages": [HumanMessage(content=req.query)],
        "stock": req.ticker
    })

    # Call the stock analysis charts function
    charts_data = stock_analysis_charts(req.ticker)
    
    # Check for errors from stock_analysis_charts
    if charts_data is None:
        # Handle case where stock data could not be fetched
        return {"error": "Stock data not available for this ticker."}
        
    # Get AI insights and format them
    aiInsights = state.get("analysis", {})
    
    # Ensure aiInsights is a dictionary for modification
    if hasattr(aiInsights, 'dict'):
        aiInsights = aiInsights.dict()
    
    aiInsights['targetPrice'] = state.get("stop_loss")
    aiInsights['stopLoss'] = state.get("stop_loss")

    # Combine all data into a single, cohesive JSON object

    json_figures = {}
    if 'figures' in charts_data and charts_data['figures']:
        for name, fig_str in charts_data['figures'].items():
            try:
                # This is the key change! Parse the JSON string back into a dictionary.
                json_figures[name] = json.loads(fig_str)
            except json.JSONDecodeError:
                # Handle cases where the string might not be valid JSON
                print(f"Error decoding JSON for figure: {name}")
                json_figures[name] = {} # Provide a fallback empty dictionary
    return {
        "response": state['messages'][-1].content,
        "figures": json_figures,  # Use the figures directly from the charts_data
        "analysis_summary": charts_data['analysis_summary'],  # Use the summary directly
        "trending_stocks": state.get('trending_stocks', {}),
        "aiInsights": aiInsights,
        "sentiment": state.get('sentiment', {})
    }


# const mockAnalysisData = {
#     aiInsights: {
#       price_summary:
#         "The current price of TCS.NS is ₹3222.7, which reflects a recent change of -5.54%. This price positions the stock closer to its 52-week low of ₹3203.03 than its high of ₹4502.65. The average volume over the past days has been notably high, indicating active trading.",
#       trend_detection:
#         "The linear price trend slope over the past 21 days is -7.7475, indicating a downward trend. The EMA-9 is currently at 3347.42, while the EMA-21 is at 3390.28, with no crossover signal evident. The final trend classification is Bearish.",
#       technical_indicators:
#         "The RSI is at 25, indicating that the stock is oversold and may be due for a short-term rebound. The MACD is -34 with the signal line at -15, showing a bearish momentum but potentially nearing a reversal. The Stochastic Oscillator is at 7, further confirming the oversold condition and the possibility of a short-term uptick.",
#       financial_metrics:
#         "The stock has a P/E ratio of 20.83, suggesting it is priced relatively in line with its earnings; however, the high debt-to-equity ratio of 9.807 indicates significant leverage. The profit margin of 19.02% is strong, but the price-to-book ratio of 12.31 suggests potential overvaluation, especially in the context of current economic uncertainty.",
#       news_sentiment:
#         "The overall sentiment from recent news is Mixed, with both negative reports concerning revenue performance and positive updates on new contracts and partnerships. Key themes include concerns over market trends and client spending, alongside new strategic partnerships that could enhance future growth.",
#       investment_recommendation: {
#         verdict: "HOLD",
#         reasoning:
#           "Given the current bearish trend, high debt levels, and mixed news sentiment, it is advisable to Hold rather than Buy. The oversold indicators suggest potential for a rebound in the short term, but without strong momentum or clearer positive developments, it would be prudent to wait for more favorable conditions before making a purchase.",
#       },
#       targetPrice: "$200",
#       stopLoss: "$175",
#     },
#     charts: [
#       {
#         id: 1,
#         title: "Intra day price movement",
#         type: "line",
#         data: {
#           x: Array.from({ length: 24 }, (_, i) => `${i}:00`),
#           y: Array.from({ length: 24 }, () => Math.random() * 20 + 180),
#           type: "scatter",
#           mode: "lines",
#           name: "Price",
#         },
#       },
#       {
#         id: 2,
#         title: "Medium term EMA analysis (30 days)",
#         type: "line",
#         data: {
#           x: Array.from({ length: 30 }, (_, i) => `Day ${i + 1}`),
#           y: Array.from({ length: 30 }, () => Math.random() * 25 + 175),
#           type: "scatter",
#           mode: "lines",
#           name: "EMA-30",
#         },
#       },
#       {
#         id: 3,
#         title: "30 day Regression analysis",
#         type: "scatter",
#         data: {
#           x: Array.from({ length: 30 }, (_, i) => i + 1),
#           y: Array.from({ length: 30 }, () => Math.random() * 30 + 170),
#           type: "scatter",
#           mode: "markers+lines",
#           name: "Regression",
#         },
#       },
#       {
#         id: 4,
#         title: "Long term EMA analysis (90 days)",
#         type: "line",
#         data: {
#           x: Array.from({ length: 90 }, (_, i) => `Day ${i + 1}`),
#           y: Array.from({ length: 90 }, () => Math.random() * 40 + 160),
#           type: "scatter",
#           mode: "lines",
#           name: "EMA-90",
#         },
#       },
#     ],
#     sentiment: {
#       overall_news_summary:
#         "The news articles related to TCS.NS have a mixed sentiment, with some articles reporting negative news such as weak quarterly results and uncertainty over US trade deals, while others report positive news such as new contract wins and expansion into new markets. Overall, the sentiment is neutral.",
#       investment_recommendation: "Neutral",
#       sentiment_score: 50,
#       news_rating: {
#         "Cognizant to invest $183 million for new India campus, add 8,000 jobs": [
#           "Neutral",
#           "https://finance.yahoo.com/news/cognizant-invest-183-million-india-100746786.html"
#         ],
#         "Danish retailer Salling Group selects TCS as strategic IT partner": [
#           "Positive",
#           "https://www.retail-insight-network.com/news/salling-group-tata-consultancy-services/"
#         ],
#         "India's TCS says none of its systems were compromised in M&S hack": [
#           "Positive",
#           "https://sg.finance.yahoo.com/news/indias-tcs-says-none-systems-140235343.html"
#         ],
#         "India's equity benchmarks inch lower as IT stocks offset gains in other sectors": [
#           "Negative",
#           "https://sg.finance.yahoo.com/news/indias-equity-benchmarks-likely-open-025034527.html"
#         ],
#         "India's equity benchmarks log weekly losses as IT stocks drag": [
#           "Negative",
#           "https://sg.finance.yahoo.com/news/indian-equity-benchmarks-may-open-023603649.html"
#         ],
#         "Indian IT major TCS secures new contract from Salling Group": [
#           "Positive",
#           "https://www.verdict.co.uk/indian-it-major-tcs-salling/"
#         ],
#         "TCS bolsters SDV development with new European hubs": [
#           "Positive",
#           "https://www.verdict.co.uk/tcs-bolsters-sdv-development-with-new-european-hubs/"
#         ],
#         "TCS launches new software-defined vehicle hubs in Europe": [
#           "Positive",
#           "https://www.just-auto.com/news/tcs-launches-new-software-defined-vehicle-hubs/"
#         ],
#         "TCS revenue falls short as tariffs cast shadow on client spending": [
#           "Negative",
#           "https://finance.yahoo.com/news/indias-tcs-misses-first-quarter-103427366.html"
#         ],
#         "Tata Consultancy Services carries out internal probe into M&S hack, FT reports": [
#           "Neutral",
#           "https://finance.yahoo.com/news/tata-consultancy-services-carries-internal-104427057.html"
#         ]
#       }
#     }
#   };
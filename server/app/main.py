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
    
    if not user or user.id != int(user_id.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this account")

    if not verify(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    return delete_user_by_email(db, credentials.email)
    

import json


from .agents .maingraph import TopGraph
from .tools .chart_cache import stock_analysis_charts

class QueryRequest(BaseModel):
    query: str
    ticker: str


@app.post("/query")
def query(req: QueryRequest, request: Request, response: Response, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    state = TopGraph.invoke({
        "messages": [HumanMessage(content=req.query)],
        "stock": req.ticker
    })

    charts_data = stock_analysis_charts(req.ticker)
    
    if charts_data is None:
        return {"error": "Stock data not available for this ticker."}
        
    aiInsights = state['messages'][-1].content 
    
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
        "figures": json_figures,  # Use the figures directly from the charts_data
        "analysis_summary": charts_data['analysis_summary'],  # Use the summary directly
        "trending_stocks": state.get('trending_stocks', {}),
        "aiInsights": eval(aiInsights),
        "sentiment": eval(state['news_sentiment'])
    }



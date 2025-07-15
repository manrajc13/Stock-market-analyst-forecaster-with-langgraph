from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta  
from . import models 
from ..utils import hash_password, verify

def create_user(db: Session, email_id: str, name: str, password: str):
    email = db.query(models.UserData).filter(models.UserData.email == email_id).first()
    if email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = models.UserData(name = name, email = email_id, password = hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email_id: str):
    user = db.query(models.UserData).filter(models.UserData.email == email_id).first()
    return user 

def delete_user_by_email(db: Session, email_id: str):
    user = db.query(models.UserData).filter(models.UserData.email == email_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": f"User with email {email_id} has been deleted successfully"}




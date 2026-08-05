from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette import status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from ..models import Users
from ..database import SessionLocal
from .auth import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db    # will execute the code up to this point, execute the queries in db, and then return the db session to the caller
    finally: 
        db.close()  # close the database connection every after a db request is made

db_dependency = Annotated[Session, Depends(get_db)]  # create a dependency for the db session
user_dependency = Annotated[dict, Depends(get_current_user)]  # create a dependency for the current user
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserVerification(BaseModel):
    current_password: str = Field(min_length=3, max_length=200)
    new_password: str = Field(min_length=3, max_length=200)


@router.get("/", status_code=status.HTTP_200_OK)
def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User Authentication Failed")
    
    # return {"username": user.get("username"), "id": user.get("id"), "role": user.get("role")}
    # return user
    return db.query(Users).filter(Users.id == user.get("id")).first()  # return the current user's information from the database


@router.put("/update-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(user: user_dependency, db: db_dependency, user_verification: UserVerification):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User Authentication Failed")
    
    user_model = db.query(Users).filter(Users.id == user.get("id")).first()
    if user_model is not None:
        if not bcrypt_context.verify(user_verification.current_password, user_model.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Error on Password Verification. Please check your password and try again.")

        user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)  # Hash the new password before storing it
        db.add(user_model)
        db.commit()
        return {"message": "Password changed successfully."}
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with the id {user.get('id')} is not found")


@router.put("/update-phone-number", status_code=status.HTTP_204_NO_CONTENT)
def update_phone_number(user: user_dependency, db: db_dependency, new_phone_number: str):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User Authentication Failed")
    
    user_model = db.query(Users).filter(Users.id == user.get("id")).first()
    if user_model is not None:
        user_model.phone_number = new_phone_number
        db.add(user_model)
        db.commit()
        return {"message": "Phone number updated successfully."}
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with the id {user.get('id')} is not found")
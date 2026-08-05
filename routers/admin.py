from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from starlette import status
from ..models import Todos, Users
from ..database import SessionLocal
from sqlalchemy.orm import Session
from .auth import get_current_user


router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db    # will execute the code up to this point, execute the queries in db, and then return the db session to the caller
    finally: 
        db.close()  # close the database connection every after a db request is made


db_dependency = Annotated[Session, Depends(get_db)]  # create a dependency for the db session
user_dependency = Annotated[dict, Depends(get_current_user)]  # create a dependency for the current user

@router.get("/todo", status_code=status.HTTP_200_OK)
def read_all(user: user_dependency, db: db_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User needs to be an admin to read all todo items by all users")
    return db.query(Todos).all()  # return all todos in the database


@router.get("/users/", status_code=status.HTTP_200_OK)
def get_all_users(user: user_dependency, db: db_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User needs to be an admin to read all users")
    return db.query(Users).all()  # return all users in the database


# Mix of Path and Query parameters to demonstrate the use of both in a single endpoint
@router.put("/users/update-role/{user_name}", status_code=status.HTTP_204_NO_CONTENT)
def update_user_role(user: user_dependency, db: db_dependency, user_name: str = Path(min_length=3), new_role: str = Query(min_length=3)):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User needs to be an admin to update a user's role")

    user_model = db.query(Users).filter(Users.username == user_name).first()  # get the user model from the database using the user_name
    if user_model is not None:
        user_model.role = new_role  # Update the user's role
        db.commit()
        return {"message": f"User with name {user_name} has been updated to role {new_role}."}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with the name {user_name} is not found")


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User needs to be an admin to delete a todo item")
    
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()   # get the todo model from the database using the todo_id
    if todo_model is not None:
        db.delete(todo_model)
        db.commit()
        return {"message": f"Todo with id {todo_id} has been deleted."}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Todo with the id {todo_id} is not found")


@router.delete("/users/{user_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user: user_dependency, db: db_dependency, user_name: str = Path(min_length=3)):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User needs to be an admin to delete a user")

    user_model = db.query(Users).filter(Users.username == user_name).first()  # get the user model from the database using the user_name
    if user_model is not None:
        db.delete(user_model)
        db.commit()
        return {"message": f"User with name {user_name} has been deleted."}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with the name {user_name} is not found")
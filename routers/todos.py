from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel, Field
from starlette import status
from sqlalchemy.orm import Session
from models import Todos
from database import SessionLocal
from .auth import get_current_user
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix="/todos",
    tags=["todos"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db    # will execute the code up to this point, execute the queries in db, and then return the db session to the caller
    finally: 
        db.close()  # close the database connection every after a db request is made


db_dependency = Annotated[Session, Depends(get_db)]  # create a dependency for the db session
user_dependency = Annotated[dict, Depends(get_current_user)]  # create a dependency for the current user

templates = Jinja2Templates(directory="templates")

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=200)
    priority: int = Field(gt=0, lt=6)
    complete: bool = Field(default=False)

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key="access_token")  # delete the access token cookie to log the user out
    return redirect_response

### Pages ###
@router.get("/todo-page")
def render_todo_page(request: Request, db: db_dependency):
    try:
        user = get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        todos = db.query(Todos).filter(Todos.owner_id == user.get("id")).all()

        return templates.TemplateResponse(request, "todos.html", context={"request": request, "todos": todos, "user": user})

    except Exception as e:
        print(f"Error rendering todo page: {e}")
        print("Redirecting to login page due to error.")
        return redirect_to_login()


@router.get("/add-todo-page")
def render_todo_page(request: Request):
    try:
        user = get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        return templates.TemplateResponse(request, "add-todo.html", context={"request": request, "user": user})

    except Exception as e:
        print(f"Error rendering 'add todo' page: {e}")
        print("Redirecting to login page due to error.")
        return redirect_to_login()


@router.get("/edit-todo-page/{todo_id}")
def render_edit_todo_page(request: Request, todo_id: int, db: db_dependency):
    try:
        user = get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        todo = db.query(Todos).filter(Todos.id == todo_id).first()

        return templates.TemplateResponse(request, "edit-todo.html", context={"request": request, "user": user, "todo": todo})

    except Exception as e:
        print(f"Error rendering 'edit todo' page: {e}")
        print("Redirecting to login page due to error.")
        return redirect_to_login()
        


### Endpoints ###
@router.get("/")
def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User Authentication Failed")
    return db.query(Todos).filter(Todos.owner_id == user.get("id")).all()  # return all todos that belong to the current user


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0),):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User Authentication Failed")

    todo_model = db.query(Todos).filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user.get("id")).first()   # get the todo model from the database using the todo_id and the current user's id
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Todo with the id {todo_id} is not found")


@router.post("/todo/", status_code=status.HTTP_201_CREATED)
def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User Authentication Failed")
    
    todo_model = Todos(**todo_request.model_dump(), owner_id=user.get("id"))  # create a new todo model using the request data and the current user's id   

    db.add(todo_model)
    db.commit()
    return {"message": "Todo created successfully."}


@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0), todo_request: TodoRequest = None):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User Authentication Failed")

    todo_model = db.query(Todos).filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user.get("id")).first()   # get the todo model from the database using the todo_id and the current user's id

    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Todo with the id {todo_id} is not found under the current user")
    
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()
    return {"message": "Todo updated successfully."}


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User Authentication Failed")

    todo_model = db.query(Todos).filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user.get("id")).first()   # get the todo model from the database using the todo_id and the current user's id

    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Todo with the id {todo_id} is not found under the current user")
    
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()
    return {"message": "Todo deleted successfully."}
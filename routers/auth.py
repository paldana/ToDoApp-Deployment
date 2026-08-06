from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from starlette import status
from sqlalchemy.orm import Session
from models import Users
from database import SessionLocal
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from settings import settings
from fastapi.templating import Jinja2Templates


## Authentication and User Management - secrets are loaded from `settings`

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3)
    email: str
    first_name: str = Field(min_length=3)
    last_name: str = Field(min_length=3)
    password: str = Field(min_length=3, max_length=200)
    role: str
    phone_number: str


class Token(BaseModel):
    access_token: str
    token_type: str
    

def get_db():
    db = SessionLocal()
    try:
        yield db    # will execute the code up to this point, execute the queries in db, and then return the db session to the caller
    finally: 
        db.close()  # close the database connection every after a db request is made


db_dependency = Annotated[Session, Depends(get_db)]  # create a dependency for the db session

templates = Jinja2Templates(directory="templates")

### Pages ###
@router.get("/login-page")
def render_login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", context={"request": request})

@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", context={"request": request})


### Endpoints ###
def authenticate_user(username: str, password: str, db: Session):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(user: CreateUserRequest, db: db_dependency):
    create_user_model = Users(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=bcrypt_context.hash(user.password),  # Hash the password before storing it
        role=user.role,
        is_active=True,
        phone_number=user.phone_number
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return {"message": "User created successfully."}



@router.post("/token", response_model = Token, status_code=status.HTTP_200_OK)
def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user_authenticated = authenticate_user(form_data.username, form_data.password, db)
    if not user_authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    token = create_access_token(username=user_authenticated.username, user_id=user_authenticated.id, role=user_authenticated.role, expires_delta=timedelta(minutes=20))

    return Token(access_token=token, token_type="bearer") 


def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta | None = None):
    to_encode = {"sub": username, "id": user_id, "role": role}
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# TODO: review what the annotated type is doing here. 
#  It seems to be a way to specify the type of the token parameter and also indicate that it should be obtained from the 
#  OAuth2PasswordBearer dependency. The Depends function is used to declare a dependency on the OAuth2PasswordBearer instance,
#  which will handle the extraction of the token from the request headers.
def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")

        if username is None or user_id is None or user_role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
        return {"username": username, "id": user_id, "role": user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")




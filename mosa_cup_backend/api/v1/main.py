import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import urllib.parse

from mosa_cup_backend.api.v1 import crud, models, schemas
from mosa_cup_backend.api.v1.database import LocalSession, engine


models.Base.metadata.create_all(engine)

api_router = APIRouter()

def get_database():
    database = LocalSession()
    try:
        yield database
    finally:
        database.close()

def get_current_user(access_token: str=Depends(OAuth2PasswordBearer("/api/v1/signin")), database: Session=Depends(get_database)) -> models.User:
    try:
        data = jwt.decode(access_token, os.getenv("SECRET_KEY"), "HS256")
        username = data.get("sub")
        if not username:
            raise HTTPException(status.HTTP_400_BAD_REQUEST)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    user = crud.read_user(database, username)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    
    return user

@api_router.post("/signup")
def signup(request: schemas.Signup, _request: Request, database: Session=Depends(get_database)):
    if (not request.username) or (not request.password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    user = crud.read_user(database, request.username)
    if user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    crud.create_user(database, request)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, "./signin")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

@api_router.post("/signin", response_model=schemas.Token)
def signin(request: OAuth2PasswordRequestForm=Depends(), database: Session=Depends(get_database)) -> schemas.Token:
    if (not request.username) or (not request.password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    user = crud.read_user(database, request.username)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    if not CryptContext(["bcrypt"]).verify(request.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    token = schemas.Token(
        access_token=jwt.encode({"sub": request.username}, os.getenv("SECRET_KEY"), "HS256")
    )

    return token

@api_router.get("/me", response_model=schemas.User)
def get_me(current_user: models.User=Depends(get_current_user)) -> schemas.User:
    return current_user

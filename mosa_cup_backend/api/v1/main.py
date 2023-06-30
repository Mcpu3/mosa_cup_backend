import os
from typing import List

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

def _get_database():
    database = LocalSession()
    try:
        yield database
    finally:
        database.close()

def _get_current_user(access_token: str=Depends(OAuth2PasswordBearer("/api/v1/signin")), database: Session=Depends(_get_database)) -> models.User:
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
def signup(request: schemas.Signup, _request: Request, database: Session=Depends(_get_database)):
    if (not request.username) or (not request.password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    user = crud.create_user(database, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_201_CREATED

@api_router.post("/signin", response_model=schemas.Token)
def signin(request: OAuth2PasswordRequestForm=Depends(), database: Session=Depends(_get_database)) -> schemas.Token:
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
def get_me(current_user: models.User=Depends(_get_current_user)) -> schemas.User:
    return current_user

@api_router.post("/me/update_password")
def update_password(request: schemas.Password, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    user = crud.update_password(database, current_user.username, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_201_CREATED

@api_router.post("/me/update_display_name")
def update_display_name(request: schemas.DisplayName, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    user = crud.update_display_name(database, current_user.username, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_201_CREATED

@api_router.post("/me/update_line_id")
def update_line_id(request: schemas.LineId, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    user = crud.update_line_id(database, current_user.username, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_201_CREATED

@api_router.get("/boards", response_model=List[schemas.BoardWithSubboards])
def get_boards(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.BoardWithSubboards]:
    _boards = crud.read_boards(database, current_user.username)
    if not _boards:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    boards = []
    for _board in _boards:
        board = schemas.Board.from_orm(_board)
        members = [crud.read_user(database, username) for username in _board.members]
        subboards = crud.read_subboards(database, _board.board_uuid)
        board = schemas.BoardWithSubboards.from_orm(
            board_uuid=_board.board_uuid,
            board_id=_board.board_id,
            board_name=_board.board_name,
            members=members,
            subboards=subboards
        )
        boards.append(board)

    return boards

@api_router.get("/board/{board_uuid}", response_model=schemas.BoardWithSubboards)
def get_board(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> schemas.BoardWithSubboards:
    _board = crud.read_board(database,board_uuid)
    if not _board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    board = schemas.BoardWithSubboards(_board)
    subboards = crud.read_subboards(database, _board.board_uuid)
    board.subboards = subboards

    return board

@api_router.post("/board")
def post_board(request: schemas.NewBoard, _request:Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    if (not request.board_id) or (not request.board_name):
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    board = crud.create_board(database, current_user.username, request)
    if not board:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, f"./board/{board.board_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

@api_router.get("/board/{board_uuid}/subboards",response_model=list[schemas.SubboardWithBoard])
def get_subboards(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.SubboardWithBoard]:
    _subboards = crud.read_subboards(database,board_uuid)
    if not _subboards:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    subboards = []
    for _subboard in _subboards:
        subboard = schemas.SubboardWithBoard(_subboard)
        board = crud.read_board(database, _subboard.board_uuid)
        subboard.board = board
        subboards.append(subboard)

    return subboards

@api_router.get("/board/{board_uuid}/subboards/{subboard_uuid}",response_model = schemas.SubboardWithBoard)
def get_subboard(board_uuid: str, subboard_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> schemas.SubboardWithBoard:
    _subboard = crud.read_subboard(database, board_uuid, subboard_uuid)
    if not _subboard:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    subboard = schemas.SubboardWithBoard(_subboard)
    board = crud.read_board(database, _subboard.board_uuid)
    subboard.board = board

    return subboard

@api_router.post("/board/{board_uuid}/subboard")
def post_board(request: schemas.NewSubboard, _request:Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    if not request.subboard_name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    subboard = crud.create_subboard(database, request)
    if not subboard:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, f"./{subboard.subboard_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

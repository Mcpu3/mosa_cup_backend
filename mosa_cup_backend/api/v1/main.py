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
    user = crud.read_user(database, username=username)
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
    user = crud.read_user(database, username=request.username)
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
    user = crud.update_password(database, current_user.user_uuid, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_201_CREATED

@api_router.post("/me/update_display_name")
def update_display_name(request: schemas.DisplayName, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    user = crud.update_display_name(database, current_user.user_uuid, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_201_CREATED

@api_router.post("/me/update_line_id")
def update_line_id(request: schemas.LineId, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    user = crud.update_line_id(database, current_user.user_uuid, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_201_CREATED

@api_router.delete("/me")
def delete_me(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    user = crud.delete_user(database, current_user.user_uuid)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_200_OK

@api_router.get("/boards", response_model=List[schemas.BoardWithSubboards])
def get_boards(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.BoardWithSubboards]:
    boards = crud.read_boards(database, current_user.user_uuid)
    if not boards:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return boards

@api_router.get("/board/{board_uuid}", response_model=schemas.BoardWithSubboards)
def get_board(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> schemas.BoardWithSubboards:
    board = crud.read_board(database, board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    return board

@api_router.post("/board")
def post_board(request: schemas.NewBoard, _request: Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    if (not request.board_id) or (not request.board_name):
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    board = crud.create_board(database, current_user.user_uuid, request)
    if not board:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, f"./board/{board.board_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

@api_router.delete("/board/{board_uuid}")
def delete_board(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    board = crud.delete_board(database, board_uuid)
    if not board:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_200_OK

@api_router.get("/my_boards", response_model=List[schemas.MyBoard])
def get_my_boards(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.MyBoard]:
    my_boards = crud.read_my_boards(database, current_user.user_uuid)
    if not my_boards:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return my_boards

@api_router.post("/update_my_boards")
def update_my_boards(request: schemas.NewMyBoards, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    user = crud.update_my_boards(database, current_user.user_uuid, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_201_CREATED

@api_router.get("/board/{board_uuid}/subboards",response_model=List[schemas.SubboardWithBoard])
def get_subboards(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.SubboardWithBoard]:
    subboards = crud.read_subboards(database, board_uuid)
    if not subboards:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return subboards

@api_router.get("/board/{board_uuid}/subboards/{subboard_uuid}", response_model = schemas.SubboardWithBoard)
def get_subboard(board_uuid: str, subboard_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> schemas.SubboardWithBoard:
    subboard = crud.read_subboard(database, board_uuid, subboard_uuid)
    if not subboard:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    return subboard

@api_router.post("/board/{board_uuid}/subboard")
def post_board(board_uuid: str, request: schemas.NewSubboard, _request: Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    if not request.subboard_name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    subboard = crud.create_subboard(database, board_uuid, request)
    if not subboard:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, f"./subboard/{subboard.subboard_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

@api_router.delete("/board/{board_uuid}/subboard/{subboard_uuid}")
def delete_board(board_uuid: str, subboard_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    subboard = crud.delete_subboard(database, board_uuid, subboard_uuid)
    if not subboard:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_200_OK

@api_router.get("/board/{board_uuid}/my_subboards", response_model=List[schemas.MySubboard])
def get_my_subboards(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.MySubboard]:
    my_subboards = crud.read_my_subboards(database, current_user.user_uuid, board_uuid)
    if not my_subboards:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return my_subboards

@api_router.post("/board/{board_uuid}/update_my_subboards")
def update_my_subboards(board_uuid: str, request: schemas.NewMySubboards, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    user = crud.update_my_subboards(database, current_user.user_uuid, board_uuid, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_201_CREATED

@api_router.get("/api/v1/board/{board_uuid}/messages", response_model=List[schemas.Message])
def get_messages(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.Message]:
    messages = crud.read_messages(database, board_uuid)
    if not messages:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return messages

@api_router.post("/api/v1/board/{board_uuid}/message")
def post_messages(board_uuid: str, request: schemas.NewMessage, _request: Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    message = crud.create_message(database, board_uuid, request)
    if not message:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, f"./message/{message.message_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

@api_router.delete("/api/v1/board/{board_uuid}/message/{message_uuid}")
def delete_message(board_uuid: str, message_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    message = crud.delete_message(database, board_uuid, message_uuid)
    if not message:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_200_OK

@api_router.get("/api/v1/board/{board_uuid}/my_messages", response_model=List[schemas.Message])
def get_my_messages(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.Message]:
    my_messages = crud.read_my_messages(database, current_user.user_uuid, board_uuid)
    if not my_messages:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return my_messages

@api_router.get("/api/v1/direct_messages", response_model=List[schemas.DirectMessage])
def get_direct_messages(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.DirectMessage]:
    direct_messages = crud.read_direct_messages(database, current_user.user_uuid)
    if not direct_messages:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return direct_messages

@api_router.post("/api/v1/direct_message")
def post_direct_message(request: schemas.NewDirectMessage, _request: Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    direct_message = crud.create_direct_message(database, current_user.user_uuid, request)
    if not direct_message:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, f"./direct_message/{direct_message.direct_message_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

@api_router.delete("/api/v1/direct_message/{direct_message_uuid}")
def delete_direct_message(direct_message_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    direct_message = crud.delete_direct_message(database, direct_message_uuid)
    if not direct_message:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return direct_message

@api_router.get("/api/v1/my_direct_messages", response_model=List[schemas.DirectMessage])
def get_my_direct_messages(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.DirectMessage]:
    my_direct_messages = crud.read_my_direct_messages(database, current_user.user_uuid)
    if not my_direct_messages:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return my_direct_messages

@api_router.get("/board/{board_uuid}/forms",response_model=schemas.Forms)
def get_board_forms(board_uuid: str,database: Session=Depends(get_database),current_user: models.User=Depends(get_current_user)):
    board_forms = crud.read_board_forms(database,board_uuid)
    if not board_forms:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return board_forms

@api_router.post("/board/{board_uuid}/form")
def post_board_form(board_uuid: str,request: schemas.NewForm,_request:Request,database: Session=Depends(get_database),current_user: models.User=Depends(get_current_user)):
    if (not request.title) or (not request.questions):
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    form = crud.create_board_form(database,board_uuid,request)
    if not form:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    for _question in request.questions:
        question = crud.create_question(database,form.form_uuid,_question)
    
    response = {
        "Location": urllib.parse.urljoin(_request.url._url,f"./board/{board_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

@api_router.get("/baord/{board_uuid}/subboard/{subboard_uuid}/forms")
def get_subboard_forms(board_uuid: str,subboard_uuid: str,database: Session=Depends(get_database),current_user: models.User=Depends(get_current_user)):
    subboard_forms = crud.read_subboard_forms(database,board_uuid,subboard_uuid)
    if not subboard_forms:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return subboard_forms

@api_router.post("/board/{board_uuid}/subboard/{subboard_uuid}/form")
def post_subboard_form(board_uuid: str,subboard_uuid: str,request: schemas.NewForm,_request:Request,database: Session=Depends(get_database),current_user: models.User=Depends(get_current_user)):
    if (not request.title) or (not request.questions):
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    subboard_form = crud.create_subboard_form(database,board_uuid,subboard_uuid,request)
    if not subboard_form:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    for _question in request.questions:
        question = crud.create_question(database,subboard_form.form_uuid,_question)
    
    response = {
        "Location": urllib.parse.urljoin(_request.url._url,f"./board/{board_uuid}/subboard/{subboard_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)
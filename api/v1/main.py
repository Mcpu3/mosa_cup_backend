from contextlib import contextmanager
import os
from typing import List
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, MessageEvent, TextMessage, TextSendMessage
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from api.v1 import crud, models, schemas
from api.v1.database import LocalSession, engine
from api.v1.LINEbot import create_rich_menu


models.Base.metadata.create_all(engine)

api_router = APIRouter()

CHANNEL_SECRET_KEY = os.getenv("CHANNEL_SECRET_KEY")
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(CHANNEL_SECRET_KEY)

rich_menu_id = line_bot_api.create_rich_menu(rich_menu=create_rich_menu.create_rich_menu())
with open("./api/v1/LINEbot/menu_image.jpg", "rb") as f:
    line_bot_api.set_rich_menu_image(rich_menu_id, "image/jpeg", f)
line_bot_api.set_default_rich_menu(rich_menu_id=rich_menu_id)

def _get_database():
    database = LocalSession()
    try:
        yield database
    finally:
        database.close()

@contextmanager
def _get_database_with_contextmanager():
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

@api_router.post("/callback")
async def callback(request: Request, x_line_signature=Header()):
    body = await request.body()
    try:
        webhook_handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_200_OK

@webhook_handler.add(FollowEvent)
def handle_follow_event(event: FollowEvent):
    with _get_database_with_contextmanager() as database:
        line_user = crud.create_line_user(database, event.source.user_id)
    if line_user:
        signup_url = f"https://orange-sand-0f913e000.3.azurestaticapps.net/paticipant/signup?line_user_uuid={line_user.line_user_uuid}"
        line_bot_api.push_message(
            event.source.user_id,
            TextSendMessage(f"{signup_url} からサインアップしてね!")
        )

@api_router.post("/signup")
def signup(request: schemas.Signup, _request: Request, database: Session=Depends(_get_database)):
    user = crud.create_user(database, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_201_CREATED

@api_router.post("/signin", response_model=schemas.Token)
def signin(request: OAuth2PasswordRequestForm=Depends(), database: Session=Depends(_get_database)) -> schemas.Token:
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

@api_router.get("/board/{board_uuid}/messages", response_model=List[schemas.Message])
def get_messages(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.Message]:
    messages = crud.read_messages(database, board_uuid)
    if not messages:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return messages

@api_router.post("/board/{board_uuid}/message")
def post_message(board_uuid: str, request: schemas.NewMessage, _request: Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    message = crud.create_message(database, board_uuid, request)
    if not message:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    if not message.scheduled_send_time:
        post_message_from_line_bot(message)
        _ = crud.update_message_send_time(database, board_uuid, message.message_uuid)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, f"./message/{message.message_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

def post_message_from_line_bot(message: schemas.Message) -> None:
    line_user_ids = []
    for subboard in message.subboards:
        for member in subboard.members:
            line_user_ids.append(member.line_user.user_id)
    line_user_ids = list(set(line_user_ids))

    line_bot_api.multicast(line_user_ids, TextSendMessage(message.body))

@api_router.delete("/board/{board_uuid}/message/{message_uuid}")
def delete_message(board_uuid: str, message_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    message = crud.delete_message(database, board_uuid, message_uuid)
    if not message:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_200_OK

@api_router.get("/board/{board_uuid}/my_messages", response_model=List[schemas.Message])
def get_my_messages(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.Message]:
    my_messages = crud.read_my_messages(database, current_user.user_uuid, board_uuid)
    if not my_messages:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return my_messages

@api_router.get("/direct_messages", response_model=List[schemas.DirectMessage])
def get_direct_messages(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.DirectMessage]:
    direct_messages = crud.read_direct_messages(database, current_user.user_uuid)
    if not direct_messages:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return direct_messages

@api_router.post("/direct_message")
def post_direct_message(request: schemas.NewDirectMessage, _request: Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    direct_message = crud.create_direct_message(database, current_user.user_uuid, request)
    if not direct_message:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_201_CREATED

@api_router.delete("/direct_message/{direct_message_uuid}")
def delete_direct_message(direct_message_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    direct_message = crud.delete_direct_message(database, direct_message_uuid)
    if not direct_message:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    if not direct_message.scheduled_send_time:
        post_direct_message_from_line_bot(direct_message)
    
    return status.HTTP_200_OK

def post_direct_message_from_line_bot(direct_message: schemas.DirectMessage) -> None:
    line_bot_api.push_message(direct_message.send_to.line_user.user_id, TextSendMessage(direct_message.body))

@api_router.get("/my_direct_messages", response_model=List[schemas.DirectMessage])
def get_my_direct_messages(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.DirectMessage]:
    my_direct_messages = crud.read_my_direct_messages(database, current_user.user_uuid)
    if not my_direct_messages:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return my_direct_messages

@api_router.get("/board/{board_uuid}/forms", response_model=List[schemas.Form])
def get_forms(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.Form]:
    forms = crud.read_forms(database, board_uuid)
    if not forms:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return forms

@api_router.post("/board/{board_uuid}/form")
def post_form(board_uuid: str, request: schemas.NewForm, _request: Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    form = crud.create_form(database, board_uuid, request)
    if not form:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, f"./form/{form.form_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

@api_router.delete("/board/{board_uuid}/form/{form_uuid}")
def delete_form(board_uuid: str, form_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    form = crud.delete_form(database, board_uuid, form_uuid)
    if not form:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_200_OK

@api_router.get("/board/{board_uuid}/form/{form_uuid}/my_form_responses", response_model=List[schemas.FormResponse])
def get_my_form_responses(board_uuid: str, form_uuid, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.FormResponse]:
    my_form_responses = crud.read_my_form_responses(database, current_user.user_uuid, form_uuid)
    if not my_form_responses:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    
    return my_form_responses

@api_router.post("/board/{board_uuid}/form/{form_uuid}/my_form_response")
def post_my_form_response(board_uuid: str, form_uuid: str, request: schemas.NewMyFormResponse, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    my_form_response = crud.create_my_form_response(database, current_user.user_uuid, form_uuid, request)
    if not my_form_response:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return status.HTTP_201_CREATED

@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message_event(event: MessageEvent):
    received_message = event.message.text
    if received_message == "サインイン":
        signin_url = "https://orange-sand-0f913e000.3.azurestaticapps.net/paticipant/signin"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(f"{signin_url} からサインインしてね!")
        )
    elif received_message == "ロール変更":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='手順に従って変更を行ってください')
        )
    elif received_message == "ボード一覧":
        message = ""
        with _get_database_with_contextmanager() as database:
            user = crud.read_user(database, user_uuid="91c3243d-8708-4a46-86ef-ada6f1d7e522")
            my_boards = crud.read_my_boards(database, user.user_uuid)
            for my_board in my_boards:
                message += f"{my_board.board_id}: {my_board.board_name}\n"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
            )
    elif received_message == "DM":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='DMはこちらから送信してください')
        ) 
    elif event.message.text.startswith("ボードに入る"):
        new_my_board_uuid = event.message.text.split()[1]
        with _get_database_with_contextmanager() as database:
            user = crud.read_user(line_user_id=event.source.user_id)
            if user:
                my_boards = crud.read_my_boards(database, user.user_uuid)
                new_my_board_uuids = [my_board.board_uuid for my_board in my_boards]
                new_my_board_uuids.append(new_my_board_uuid)
                new_my_boards = schemas.NewMyBoards(
                    new_my_board_uuids=new_my_board_uuids
                )
                user = crud.update_my_boards(database, user.user_uuid, new_my_boards)
    else:
        #ボード参加かもしれないから、crudでボード検索して合致したらurl、それ以外はこれって感じがいいかも
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='操作はメニューから行ってください')
        )
    

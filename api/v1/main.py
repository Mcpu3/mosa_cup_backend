from contextlib import contextmanager
import copy
import json
import os
from typing import List, Tuple
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FlexSendMessage, FollowEvent, MessageAction, MessageEvent, RichMenu, RichMenuArea, RichMenuBounds, RichMenuSize, TextMessage, TextSendMessage
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from api.v1 import crud, models, schemas
from api.v1.database import LocalSession, engine


models.Base.metadata.create_all(engine)

api_router = APIRouter()

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

def init_line_bot_api() -> Tuple[LineBotApi, WebhookHandler]:
    CHANNEL_SECRET_KEY = os.getenv("CHANNEL_SECRET_KEY")
    CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")

    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
    web_hook_handler = WebhookHandler(CHANNEL_SECRET_KEY)

    rich_menu_id = line_bot_api.create_rich_menu(
        RichMenu(
            size=RichMenuSize(width=2500, height=1686),
            selected=True,
            name="リッチメニュー",
            chat_bar_text="メニュー",
            areas=[
                RichMenuArea(
                    bounds=RichMenuBounds(x=0, y=0, width=1250, height=843),
                    action=MessageAction(label="サインアップ", text="サインアップ")
                ),
                RichMenuArea(
                    bounds=RichMenuBounds(x=0, y=843, width=1250, height=843),
                    action=MessageAction(label="ボード設定", text="ボード設定")
                ),
                RichMenuArea(
                    bounds=RichMenuBounds(x=1250, y=843, width=1250, height=843),
                    action=MessageAction(label="サブボード設定", text="サブボード設定")
                ),
                RichMenuArea(
                    bounds=RichMenuBounds(x=1250, y=0, width=1250, height=843),
                    action=MessageAction(label="DM", text="DM")
                )
            ]
        )
    )
    with open("./api/v1/assets/rich_menu.png", "rb") as f:
        line_bot_api.set_rich_menu_image(rich_menu_id, "image/png", f)
        line_bot_api.set_default_rich_menu(rich_menu_id)

    return line_bot_api, web_hook_handler

line_bot_api, web_hook_handler = init_line_bot_api()

@api_router.post("/callback", tags=["LINE"])
async def callback(request: Request, x_line_signature=Header()):
    body = await request.body()
    try:
        web_hook_handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_200_OK

@web_hook_handler.add(FollowEvent)
def handle_follow_event(event: FollowEvent):
    with _get_database_with_contextmanager() as database:
        line_user = crud.read_line_user(database, event.source.user_id)
        if not line_user:
            line_user = crud.create_line_user(database, event.source.user_id)
        if line_user:
            user = crud.read_user(database, line_user_id=event.source.user_id)
            if user:
                line_bot_api.push_message(
                    event.source.user_id,
                    TextSendMessage(f"{user.display_name if user.display_name else user.username}さんでサインインしました。")
                )
            else:
                signup_url = f"https://orange-sand-0f913e000.3.azurestaticapps.net/paticipant/signup?line_user_uuid={line_user.line_user_uuid}"
                line_bot_api.push_message(
                    event.source.user_id,
                    TextSendMessage(f"{signup_url} でサインアップします。")
                )

@api_router.post("/signup", tags=["users"])
def signup(request: schemas.Signup, database: Session=Depends(_get_database)):
    user = crud.create_user(database, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_201_CREATED

@api_router.post("/signin", response_model=schemas.Token, tags=["users"])
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

@api_router.get("/me", response_model=schemas.User, tags=["users"])
def get_me(current_user: models.User=Depends(_get_current_user)) -> schemas.User:
    return current_user

@api_router.post("/me/update_password", tags=["users"])
def update_password(request: schemas.Password, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    user = crud.update_password(database, current_user.username, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_201_CREATED

@api_router.post("/me/update_display_name", tags=["users"])
def update_display_name(request: schemas.DisplayName, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    user = crud.update_display_name(database, current_user.username, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_201_CREATED

@api_router.delete("/me", tags=["users"])
def delete_me(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    user = crud.delete_user(database, current_user.username)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_200_OK

@api_router.get("/boards", response_model=List[schemas.BoardWithSubboards], tags=["boards"])
def get_boards(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.BoardWithSubboards]:
    boards = crud.read_boards(database, current_user.username)
    if not boards:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return boards

@api_router.get("/board/{board_uuid}", response_model=schemas.BoardWithSubboards, tags=["boards"])
def get_board(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> schemas.BoardWithSubboards:
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    return board

@api_router.post("/board", tags=["boards"])
def post_board(request: schemas.NewBoard, _request: Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    board = crud.create_board(database, current_user.username, request)
    if not board:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, f"./board/{board.board_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

@api_router.delete("/board/{board_uuid}", tags=["boards"])
def delete_board(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    board = crud.delete_board(database, board_uuid)
    if not board:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_200_OK

@api_router.get("/my_boards", response_model=List[schemas.MyBoardWithSubboards], tags=["boards"])
def get_my_boards(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.MyBoardWithSubboards]:
    my_boards = crud.read_my_boards(database, current_user.username)
    if not my_boards:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return my_boards

@api_router.post("/update_my_boards", tags=["boards"])
def update_my_boards(request: schemas.NewMyBoards, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    user = crud.update_my_boards(database, current_user.username, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_201_CREATED

@api_router.get("/board/{board_uuid}/subboards",response_model=List[schemas.SubboardWithBoard], tags=["subboards"])
def get_subboards(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.SubboardWithBoard]:
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    subboards = crud.read_subboards(database, board_uuid)
    if not subboards:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return subboards

@api_router.get("/board/{board_uuid}/subboards/{subboard_uuid}", response_model = schemas.SubboardWithBoard, tags=["subboards"])
def get_subboard(board_uuid: str, subboard_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> schemas.SubboardWithBoard:
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    subboard = crud.read_subboard(database, board_uuid, subboard_uuid)
    if not subboard:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    return subboard

@api_router.post("/board/{board_uuid}/subboard", tags=["subboards"])
def post_subboard(board_uuid: str, request: schemas.NewSubboard, _request: Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    subboard = crud.create_subboard(database, board_uuid, request)
    if not subboard:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, f"./subboard/{subboard.subboard_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

@api_router.delete("/board/{board_uuid}/subboard/{subboard_uuid}", tags=["subboards"])
def delete_subboard(board_uuid: str, subboard_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    subboard = crud.read_subboard(database, board_uuid, subboard_uuid)
    if not subboard:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    subboard = crud.delete_subboard(database, board_uuid, subboard_uuid)
    if not subboard:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_200_OK

@api_router.get("/board/{board_uuid}/available_subboards", response_model=List[schemas.MySubboardWithBoard], tags=["subboards"])
def get_available_subboards(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.MySubboardWithBoard]:
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if current_user not in board.members:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    available_subboards = crud.read_subboards(database, board_uuid)
    if not available_subboards:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return available_subboards

@api_router.get("/board/{board_uuid}/my_subboards", response_model=List[schemas.MySubboardWithBoard], tags=["subboards"])
def get_my_subboards(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.MySubboardWithBoard]:
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if current_user not in board.members:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    my_subboards = crud.read_my_subboards(database, current_user.username, board_uuid)
    if not my_subboards:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return my_subboards

@api_router.post("/board/{board_uuid}/update_my_subboards", tags=["subboards"])
def update_my_subboards(board_uuid: str, request: schemas.NewMySubboards, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if current_user not in board.members:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    user = crud.update_my_subboards(database, current_user.username, board_uuid, request)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_201_CREATED

@api_router.get("/board/{board_uuid}/messages", response_model=List[schemas.Message], tags=["messages"])
def get_messages(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.Message]:
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    messages = crud.read_messages(database, board_uuid)
    if not messages:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return messages

@api_router.post("/board/{board_uuid}/message", tags=["messages"])
def post_message(board_uuid: str, request: schemas.NewMessage, _request: Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
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
            if member.line_user:
                line_user_ids.append(member.line_user.user_id)
    line_user_ids = list(set(line_user_ids))

    if line_user_ids:
        with open("./api/v1/assets/flex_messages/message.json") as f:
            flex_message = json.load(f)
        flex_message["body"]["contents"][0]["text"] = message.board.board_name
        flex_message["body"]["contents"][1]["contents"][0]["contents"][0]["text"] = ", ".join([subboard.subboard_name for subboard in message.subboards])
        flex_message["body"]["contents"][1]["contents"][1]["contents"][0]["text"] = message.body
        line_bot_api.multicast(line_user_ids, FlexSendMessage(message.body, flex_message))

@api_router.delete("/board/{board_uuid}/message/{message_uuid}", tags=["messages"])
def delete_message(board_uuid: str, message_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    message = crud.read_message(database, board_uuid, message_uuid)
    if not message:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if message.board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    message = crud.delete_message(database, board_uuid, message_uuid)
    if not message:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_200_OK

@api_router.get("/board/{board_uuid}/my_messages", response_model=List[schemas.Message], tags=["messages"])
def get_my_messages(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.Message]:
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if current_user not in board.members:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    my_messages = crud.read_my_messages(database, current_user.username, board_uuid)
    if not my_messages:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return my_messages

@api_router.get("/direct_messages", response_model=List[schemas.DirectMessage], tags=["direct_messages"])
def get_direct_messages(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.DirectMessage]:
    direct_messages = crud.read_direct_messages(database, current_user.username)
    if not direct_messages:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return direct_messages

@api_router.post("/direct_message", tags=["direct_messages"])
def post_direct_message(request: schemas.NewDirectMessage, _request: Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    direct_message = crud.create_direct_message(database, current_user.username, request)
    if not direct_message:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    if not direct_message.scheduled_send_time:
        post_direct_message_from_line_bot(direct_message)
        _ = crud.update_direct_message_send_time(database, direct_message.direct_message_uuid)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, f"./direct_message/{direct_message.direct_message_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

def post_direct_message_from_line_bot(direct_message: schemas.DirectMessage) -> None:
    if direct_message.send_to.line_user:
        with open("./api/v1/assets/flex_messages/direct_message.json") as f:
            flex_message = json.load(f)
        flex_message["body"]["contents"][0]["text"] = direct_message.send_from.display_name if direct_message.send_from.display_name else direct_message.send_from.username
        flex_message["body"]["contents"][1]["contents"][0]["contents"][0]["text"] = direct_message.body
        line_bot_api.push_message(
            direct_message.send_to.line_user.user_id,
            FlexSendMessage(direct_message.body, flex_message)
        )

@api_router.delete("/direct_message/{direct_message_uuid}", tags=["direct_messages"])
def delete_direct_message(direct_message_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    direct_message = crud.read_direct_message(database, direct_message_uuid)
    if not direct_message:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if direct_message.send_from != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    direct_message = crud.delete_direct_message(database, direct_message_uuid)
    if not direct_message:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_200_OK

@api_router.get("/my_direct_messages", response_model=List[schemas.DirectMessage], tags=["direct_messages"])
def get_my_direct_messages(current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.DirectMessage]:
    my_direct_messages = crud.read_my_direct_messages(database, current_user.username)
    if not my_direct_messages:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return my_direct_messages

@api_router.get("/board/{board_uuid}/forms", response_model=List[schemas.Form], tags=["forms"])
def get_forms(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.Form]:
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    forms = crud.read_forms(database, board_uuid)
    if not forms:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return forms

@api_router.post("/board/{board_uuid}/form", tags=["forms"])
def post_form(board_uuid: str, request: schemas.NewForm, _request: Request, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    form = crud.create_form(database, board_uuid, request)
    if not form:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    response = {
        "Location": urllib.parse.urljoin(_request.url._url, f"./form/{form.form_uuid}")
    }

    return JSONResponse(response, status.HTTP_201_CREATED)

@api_router.delete("/board/{board_uuid}/form/{form_uuid}", tags=["forms"])
def delete_form(board_uuid: str, form_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if board.administrator != current_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    form = crud.read_form(database, board_uuid, form_uuid)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    form = crud.delete_form(database, board_uuid, form_uuid)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    return status.HTTP_200_OK

@api_router.get("/board/{board_uuid}/my_forms", response_model=List[schemas.MyForm], tags=["forms"])
def get_my_forms(board_uuid: str, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.MyForm]:
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if current_user not in board.members:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    my_forms = crud.read_my_forms(database, current_user.username, board_uuid)
    if not my_forms:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return my_forms

@api_router.get("/board/{board_uuid}/form/{form_uuid}/my_form_responses", response_model=List[schemas.FormResponse], tags=["forms"])
def get_my_form_responses(board_uuid: str, form_uuid, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)) -> List[schemas.FormResponse]:
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if current_user not in board.members:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    form = crud.read_form(database, board_uuid, form_uuid)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    my_form_responses = crud.read_my_form_responses(database, current_user.username, form_uuid)
    if not my_form_responses:
        raise HTTPException(status.HTTP_204_NO_CONTENT)

    return my_form_responses

@api_router.post("/board/{board_uuid}/form/{form_uuid}/my_form_response", tags=["forms"])
def post_my_form_response(board_uuid: str, form_uuid: str, request: schemas.NewMyFormResponse, current_user: models.User=Depends(_get_current_user), database: Session=Depends(_get_database)):
    board = crud.read_board(database, board_uuid=board_uuid)
    if not board:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if current_user not in board.members:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    form = crud.read_form(database, board_uuid, form_uuid)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    my_form_response = crud.create_my_form_response(database, current_user.username, form_uuid, request)
    if not my_form_response:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return status.HTTP_201_CREATED

@web_hook_handler.add(MessageEvent, message=TextMessage)
def handle_message_event(event: MessageEvent):
    with _get_database_with_contextmanager() as database:
        if event.message.text == "サインアップ":
            line_user = crud.read_line_user(database, event.source.user_id)
            if not line_user:
                line_user = crud.create_line_user(database, event.source.user_id)
            if line_user:
                user = crud.read_user(database, line_user_id=event.source.user_id)
                if user:
                    line_bot_api.push_message(
                        event.source.user_id,
                        TextSendMessage(f"{user.display_name if user.display_name else user.username}さんでサインインしました。")
                    )
                else:
                    signup_url = f"https://orange-sand-0f913e000.3.azurestaticapps.net/paticipant/signup?line_user_uuid={line_user.line_user_uuid}"
                    line_bot_api.push_message(
                        event.source.user_id,
                        TextSendMessage(f"{signup_url} でサインアップします。")
                    )
        elif event.message.text == "ボード設定":
            user = crud.read_user(database, line_user_id=event.source.user_id)
            if user:
                line_message_context = crud.read_line_message_context(database, user.line_user_uuid)
                if not line_message_context:
                    line_message_context = crud.create_line_message_context(database, user.line_user_uuid, "ボード設定")
                else:
                    line_message_context = crud.update_line_message_context(database, user.line_user_uuid, "ボード設定")
                if line_message_context:
                    line_bot_api.push_message(
                        event.source.user_id,
                        TextSendMessage("1: 入っているボードを表示する\n2: ボードに入る/ボードから出る")
                    )
        elif event.message.text == "サブボード設定":
            user = crud.read_user(database, line_user_id=event.source.user_id)
            if user:
                line_message_context = crud.read_line_message_context(database, user.line_user_uuid)
                if not line_message_context:
                    line_message_context = crud.create_line_message_context(database, user.line_user_uuid, "サブボード設定")
                else:
                    line_message_context = crud.update_line_message_context(database, user.line_user_uuid, "サブボード設定")
                if line_message_context:
                    line_bot_api.push_message(
                        event.source.user_id,
                        TextSendMessage("ボードID:")
                    )
        else:
            user = crud.read_user(database, line_user_id=event.source.user_id)
            if user:
                line_message_context = crud.read_line_message_context(database, user.line_user_uuid)
                if line_message_context:
                    if line_message_context.message_context == "ボード設定":
                        if event.message.text == "1":
                            line_message_context = crud.update_line_message_context(database, user.line_user_uuid, None)
                            if line_message_context:
                                with open("./api/v1/assets/flex_messages/boards.json") as f:
                                    flex_message = json.load(f)
                                if len(user.my_boards) > 0:
                                    for _ in range(len(user.my_boards) - 1):
                                        flex_message["body"]["contents"][1]["contents"].append(copy.deepcopy(flex_message["body"]["contents"][1]["contents"][0]))
                                    for i, my_board in enumerate(user.my_boards):
                                        flex_message["body"]["contents"][1]["contents"][i]["contents"][0]["text"] = my_board.board_id
                                        flex_message["body"]["contents"][1]["contents"][i]["contents"][1]["text"] = my_board.board_name
                                else:
                                    flex_message["body"]["contents"][1]["contents"][0]["contents"][0]["text"] = "入っているボードはありません"
                                    flex_message["body"]["contents"][1]["contents"][0]["contents"][1]["text"] = "入っているボードはありません"
                                line_bot_api.push_message(
                                    event.source.user_id,
                                    FlexSendMessage("入っているボード", flex_message)
                                )
                        elif event.message.text == "2":
                            line_message_context = crud.update_line_message_context(database, user.line_user_uuid, "ボードに入る/ボードから出る")
                            if line_message_context:
                                line_bot_api.push_message(
                                    event.source.user_id,
                                    TextSendMessage("ボードID:")
                                )
                    elif line_message_context.message_context == "ボードに入る/ボードから出る":
                        line_message_context = crud.update_line_message_context(database, user.line_user_uuid, None)
                        if line_message_context:
                            board = crud.read_board(database, board_id=event.message.text)
                            if board:
                                my_boards = crud.read_my_boards(database, user.username)
                                new_my_board_ids = [my_board.board_id for my_board in my_boards]
                                if board.board_id not in new_my_board_ids:
                                    new_my_board_ids.append(board.board_id)
                                    user = crud.update_my_boards(database, user.username, schemas.NewMyBoards(new_my_board_ids=new_my_board_ids))
                                    if user:
                                        line_bot_api.push_message(
                                            event.source.user_id,
                                            TextSendMessage(f'ボード "{board.board_name}" に入りました。')
                                        )
                                else:
                                    new_my_board_ids.remove(board.board_id)
                                    user = crud.update_my_boards(database, user.username, schemas.NewMyBoards(new_my_board_ids=new_my_board_ids))
                                    if user:
                                        line_bot_api.push_message(
                                            event.source.user_id,
                                            TextSendMessage(f'ボード "{board.board_name}" から出ました。')
                                        )
                    elif line_message_context.message_context == "サブボード設定":
                        line_message_context = crud.update_line_message_context(database, user.line_user_uuid, None)
                        if line_message_context:
                            board = crud.read_board(database, board_id=event.message.text)
                            if board:
                                my_boards = crud.read_my_boards(database, user.username)
                                if board.board_id in [my_board.board_id for my_board in my_boards]:
                                    update_my_subboards_url = f"https://orange-sand-0f913e000.3.azurestaticapps.net/paticipant/boardregistration/{board.board_uuid}"
                                    line_bot_api.push_message(
                                        event.source.user_id,
                                        TextSendMessage(f'{update_my_subboards_url} でサブボードに入る/サブボードから出ることができます。')
                                    )

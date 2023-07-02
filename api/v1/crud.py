from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from passlib.context import CryptContext
from sqlalchemy import and_
from sqlalchemy.orm import Session

from api.v1 import models, schemas


def create_line_user(database: Session, user_id: str) -> models.LINEUser:
    line_user_uuid = str(uuid4())
    created_at = datetime.now()
    line_user = models.LINEUser(
        line_user_uuid=line_user_uuid,
        user_id=user_id,
        created_at=created_at
    )
    database.add(line_user)
    database.commit()
    database.refresh(line_user)

    return line_user

def read_user(database: Session, user_uuid: Optional[str]=None, username: Optional[str]=None, line_user_id: Optional[str]=None) -> Optional[models.User]:
    user = None
    if user_uuid:
        user = read_user_by_uuid(database, user_uuid)
    if username:
        user = read_user_by_username(database, username)
    if line_user_id:
        user = read_user_by_line_user_id(database, line_user_id)

    return user

def read_user_by_uuid(database: Session, user_uuid: str) -> Optional[models.User]:
    return database.query(models.User).filter(and_(models.User.user_uuid == user_uuid, models.User.deleted == False)).first()

def read_user_by_username(database: Session, username: str) -> Optional[models.User]:
    return database.query(models.User).filter(and_(models.User.username == username, models.User.deleted == False)).first()

def read_user_by_line_user_id(database: Session, line_user_id: str) -> Optional[models.User]:
    return database.query(models.User).filter(and_(models.User.line_user.has(user_id=line_user_id), models.User.deleted == False)).first()

def create_user(database: Session, signup: schemas.Signup) -> Optional[models.User]:
    user_uuid = str(uuid4())
    hashed_password = CryptContext(["bcrypt"]).hash(signup.password)
    created_at = datetime.now()
    user = models.User(
        user_uuid=user_uuid,
        username=signup.username,
        hashed_password=hashed_password,
        created_at=created_at
    )
    if signup.line_user_uuid:
        user.line_user_uuid = signup.line_user_uuid
    database.add(user)
    database.commit()
    database.refresh(user)

    return user

def update_password(database: Session, user_uuid: str, password: schemas.Password) -> Optional[models.User]:
    user = read_user(database, user_uuid=user_uuid)
    if user:
        hashed_password = CryptContext(["bcrypt"]).hash(password.new_password)
        updated_at = datetime.now()
        user.hashed_password = hashed_password
        user.updated_at = updated_at
        database.commit()
        database.refresh(user)

    return user

def update_display_name(database: Session, user_uuid: str, display_name: schemas.DisplayName) -> Optional[models.User]:
    user = read_user(database, user_uuid=user_uuid)
    if user:
        updated_at = datetime.now()
        user.display_name = display_name.new_display_name
        user.updated_at = updated_at
        database.commit()
        database.refresh(user)

    return user

def delete_user(database: Session, user_uuid: str) -> Optional[models.User]:
    user = read_user(database, user_uuid=user_uuid)
    if user:
        updated_at = datetime.now()
        user.updated_at = updated_at
        user.deleted = True
        database.commit()
        database.refresh(user)

    return user

def read_boards(database: Session, user_uuid: str) -> List[models.Board]:
    return database.query(models.Board).filter(and_(models.Board.administrator_uuid == user_uuid, models.Board.deleted == False)).all()

def read_board(database: Session, board_uuid: str) -> models.Board:
    return database.query(models.Board).filter(and_(models.Board.board_uuid == board_uuid, models.Board.deleted == False)).first()

def create_board(database: Session, user_uuid: str, new_board: schemas.NewBoard) -> models.Board:
    board_uuid = str(uuid4())
    created_at = datetime.now()
    board = models.Board(
        board_uuid=board_uuid,
        board_id=new_board.board_id,
        board_name=new_board.board_name,
        administrator_uuid=user_uuid,
        created_at=created_at
    )
    database.add(board)
    database.commit()
    database.refresh(board)

    return board

def delete_board(database: Session, board_uuid: str) -> Optional[models.Board]:
    board = read_board(database, board_uuid)
    if board:
        updated_at = datetime.now()
        board.updated_at = updated_at
        board.deleted = True
        for subboard in board.subboards:
            subboard.updated_at = updated_at
            subboard.deleted = True
        database.commit()
        database.refresh(board)

    return board

def read_my_boards(database: Session, user_uuid: str) -> List[models.Board]:
    return database.query(models.Board).filter(and_(models.Board.members.any(user_uuid=user_uuid), models.Board.deleted == False)).all()

def update_my_boards(database: Session, user_uuid: str, new_my_boards: schemas.NewMyBoards) -> Optional[schemas.User]:
    user = read_user(database, user_uuid=user_uuid)
    if user:
        user.my_boards.clear()
        for new_my_board_uuid in new_my_boards.new_my_board_uuids:
            board = read_board(database, new_my_board_uuid)
            if board:
                user.my_boards.append(board)
        database.commit()
        database.refresh(user)

    return user

def read_subboards(database: Session, board_uuid: str) -> List[models.Subboard]:
    return database.query(models.Subboard).filter(and_(models.Subboard.board_uuid == board_uuid, models.Subboard.deleted == False)).all()

def read_subboard(database: Session, board_uuid: str, subboard_uuid: str) -> Optional[models.Subboard]:
    return database.query(models.Subboard).filter(and_(models.Subboard.board_uuid == board_uuid, models.Subboard.subboard_uuid == subboard_uuid, models.Subboard.deleted == False)).first()

def create_subboard(database: Session, board_uuid: str, new_subboard: schemas.NewSubboard) -> Optional[models.Subboard]:
    subboard_uuid = str(uuid4())
    created_at = datetime.now()
    subboard = models.Subboard(
        subboard_uuid=subboard_uuid,
        subboard_name=new_subboard.subboard_name,
        board_uuid=board_uuid,
        created_at=created_at
    )
    database.add(subboard)
    database.commit()
    database.refresh(subboard)

    return subboard

def delete_subboard(database: Session, board_uuid: str, subboard_uuid: str) -> Optional[models.Subboard]:
    subboard = read_subboard(database, board_uuid, subboard_uuid)
    if subboard:
        updated_at = datetime.now()
        subboard.updated_at = updated_at
        subboard.deleted = True
        database.commit()
        database.refresh(subboard)

    return subboard

def read_my_subboards(database: Session, user_uuid: str, board_uuid: str) -> List[models.Subboard]:
    return database.query(models.Subboard).filter(and_(models.Subboard.board_uuid == board_uuid, models.Subboard.members.any(user_uuid=user_uuid), models.Subboard.deleted == False)).all()

def update_my_subboards(database: Session, user_uuid: str, board_uuid: str, new_my_subboards: schemas.NewMySubboards) -> Optional[schemas.User]:
    user = read_user(database, user_uuid=user_uuid)
    if user:
        user.my_subboards = [my_subboard for my_subboard in user.my_subboards if my_subboard.board_uuid != board_uuid]
        for new_my_subboard_uuid in new_my_subboards.new_my_subboard_uuids:
            subboard = read_subboard(database, board_uuid, new_my_subboard_uuid)
            if subboard:
                user.my_subboards.append(subboard)
        database.commit()
        database.refresh(user)

    return user

def read_messages(database: Session, board_uuid: str) -> List[models.Message]:
    return database.query(models.Message).filter(and_(models.Message.board_uuid == board_uuid, models.Message.deleted == False)).all()

def read_message(database: Session, board_uuid: str, message_uuid: str) -> Optional[models.Message]:
    return database.query(models.Message).filter(and_(models.Message.message_uuid == message_uuid, models.Message.board_uuid == board_uuid, models.Message.deleted == False)).first()

def create_message(database: Session, board_uuid: str, new_message: schemas.NewMessage) -> Optional[models.Message]:
    message_uuid = str(uuid4())
    created_at = datetime.now()
    message = models.Message(
        message_uuid=message_uuid,
        board_uuid=board_uuid,
        body=new_message.body,
        scheduled_send_time=new_message.scheduled_send_time,
        created_at=created_at
    )
    for subboard_uuid in new_message.subboard_uuids:
        subboard = read_subboard(database, board_uuid, subboard_uuid)
        message.subboards.append(subboard)
    database.add(message)
    database.commit()
    database.refresh(message)

    return message

def update_message_send_time(database: Session, board_uuid: str, message_uuid: str) -> models.Message:
    message = read_message(database, board_uuid, message_uuid)
    if message:
        send_time = datetime.now()
        updated_at = datetime.now()
        message.send_time = send_time
        message.updated_at = updated_at
        database.commit()
        database.refresh(message)

    return message

def delete_message(database: Session, board_uuid: str, message_uuid: str) -> models.Message:
    message = read_message(database, board_uuid, message_uuid)
    if message:
        updated_at = datetime.now()
        message.updated_at = updated_at
        message.deleted = True
        database.commit()
        database.refresh(message)

    return message

def read_my_messages(database: Session, user_uuid: str, board_uuid: str) -> List[models.Message]:
    query = database.query(models.Message).filter(and_(models.Message.board_uuid == board_uuid, models.Message.deleted == False))
    my_subboards = read_my_subboards(database, user_uuid, board_uuid)
    messages = query.filter(models.Message.subboards.any(models.Subboard.subboard_uuid.in_([my_subboard.subboard_uuid for my_subboard in my_subboards]))).all()

    return messages

def read_direct_messages(database: Session, user_uuid: str) -> List[models.DirectMessage]:
    return database.query(models.DirectMessage).filter(and_(models.DirectMessage.send_from.has(user_uuid=user_uuid), models.DirectMessage.deleted == False)).all()

def read_direct_message(database: Session, direct_message_uuid: str) -> Optional[models.DirectMessage]:
    return database.query(models.DirectMessage).filter(and_(models.DirectMessage.direct_message_uuid == direct_message_uuid, models.Message.deleted == False)).first()

def create_direct_message(database: Session, user_uuid: str, new_direct_message: schemas.NewDirectMessage) -> Optional[models.DirectMessage]:
    direct_messages = []
    for send_to_uuid in new_direct_message.send_to_uuids:
        direct_message_uuid = str(uuid4())
        created_at = datetime.now()
        direct_message = models.DirectMessage(
            direct_message_uuid=direct_message_uuid,
            send_from_uuid=user_uuid,
            send_to_uuid=send_to_uuid,
            body=new_direct_message.body,
            scheduled_send_time=new_direct_message.scheduled_send_time,
            created_at=created_at
        )
        database.add(direct_message)
        database.commit()
        database.refresh(direct_message)
        direct_messages.append(direct_message)

    return direct_messages

def update_direct_message_send_time(database: Session, direct_message_uuid: str) -> models.DirectMessage:
    direct_message = read_direct_message(database, direct_message_uuid)
    if direct_message:
        send_time = datetime.now()
        updated_at = datetime.now()
        direct_message.send_time = send_time
        direct_message.updated_at = updated_at
        database.commit()
        database.refresh(direct_message)

    return direct_message

def delete_direct_message(database: Session, message_uuid: str) -> models.DirectMessage:
    direct_message = read_direct_message(database, message_uuid)
    if direct_message:
        updated_at = datetime.now()
        direct_message.updated_at = updated_at
        direct_message.deleted = True
        database.commit()
        database.refresh(direct_message)

    return direct_message

def read_my_direct_messages(database: Session, user_uuid: str) -> List[models.DirectMessage]:
    return database.query(models.DirectMessage).filter(and_(models.DirectMessage.send_to_uuid == user_uuid, models.DirectMessage.deleted == False)).all()

def read_forms(database: Session, board_uuid: str) -> List[models.Form]:
    return database.query(models.Form).filter(and_(models.Form.board_uuid == board_uuid, models.Form.deleted == False)).all()

def read_form(database: Session, board_uuid: str, form_uuid: str) -> Optional[models.Form]:
    return database.query(models.Form).filter(and_(models.Form.form_uuid == form_uuid, models.Form.board_uuid == board_uuid, models.Form.deleted == False)).first()

def create_form(database: Session, board_uuid: str, new_form: schemas.NewForm) -> Optional[models.Form]:
    form_uuid = str(uuid4())
    created_at = datetime.now()
    form = models.Form(
        form_uuid=form_uuid,
        board_uuid=board_uuid,
        title=new_form.title,
        scheduled_send_time=new_form.scheduled_send_time,
        created_at=created_at
    )
    for subboard_uuid in new_form.subboard_uuids:
        subboard = read_subboard(database, board_uuid, subboard_uuid)
        form.subboards.append(subboard)
    database.add(form)
    database.commit()
    database.refresh(form)
    if form:
        for new_form_question in new_form.form_questions:
            form_question = create_form_question(database, form.form_uuid, new_form_question)
            if form_question:
                form.form_questions.append(form_question)
        database.add(form)
        database.commit()
        database.refresh(form)

    return form

def delete_form(database: Session, board_uuid: str, form_uuid: str) -> models.Form:
    form = read_form(database, board_uuid, form_uuid)
    if form:
        updated_at = datetime.now()
        form.updated_at = updated_at
        form.deleted = True
        for form_question in form.form_questions:
            form_question.updated_at = updated_at
            form_question.deleted = True
        database.commit()
        database.refresh(form)

    return form

def create_form_question(database: Session, form_uuid: str, new_form_question: schemas.FormYesNoQuestion) -> Optional[models.FormYesNoQuestion]:
    form_question_uuid = str(uuid4())
    created_at = datetime.now()
    form_question = models.FormYesNoQuestion(
        form_question_uuid=form_question_uuid,
        form_uuid=form_uuid,
        title=new_form_question.title,
        yes=new_form_question.yes,
        no=new_form_question.no,
        created_at=created_at
    )
    database.add(form_question)
    database.commit()
    database.refresh(form_question)

    return form_question

def read_my_form_responses(database: Session, user_uuid: str, form_uuid: str) -> List[models.FormResponse]:
    return database.query(models.FormResponse).filter(and_(models.FormResponse.form_uuid == form_uuid, models.FormResponse.respondent_uuid == user_uuid, models.FormResponse.deleted == False)).all()

def create_my_form_response(database: Session, user_uuid: str, form_uuid: str, new_my_form_response: schemas.NewMyFormResponse) -> Optional[models.FormResponse]:
    form_response_uuid = str(uuid4())
    created_at = datetime.now()
    form_response = models.FormResponse(
        form_response_uuid=form_response_uuid,
        respondent_uuid=user_uuid,
        form_uuid=form_uuid,
        created_at=created_at
    )
    if form_response:
        for new_form_question_response in new_my_form_response.form_question_responses:
            form_question_response = create_form_question_response(database, form_response.form_response_uuid, new_form_question_response)
            if form_question_response:
                form_response.form_question_responses.append(form_question_response)
        database.add(form_response)
        database.commit()
        database.refresh(form_response)

    return form_response

def create_form_question_response(database: Session, form_response_uuid: str, new_form_question_response: schemas.FormYesNoQuestionResponse) -> Optional[models.FormYesNoQuestionResponse]:
    form_question_response_uuid = str(uuid4())
    created_at = datetime.now()
    form_question_response = models.FormYesNoQuestion(
        form_question_response_uuid=form_question_response_uuid,
        form_response_uuid=form_response_uuid,
        form_question_uuid=new_form_question_response.form_question_uuid,
        yes=new_form_question_response.yes,
        no=new_form_question_response.no,
        created_at=created_at
    )
    database.add(form_question_response)
    database.commit()
    database.refresh(form_question_response)

    return form_question_response

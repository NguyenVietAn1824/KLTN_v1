from __future__ import annotations

import uuid

import bcrypt
from aqi_agent.api.helpers.exception_handler import ExceptionHandler
from aqi_agent.shared.utils import get_resources
from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import JSONResponse
from logger import get_logger
from pg.controller.schemas import User as UserSchema
from pg.controller.schemas import UserAuthentication as UserAuthSchema
from pydantic import BaseModel
from pydantic import Field

auth_router = APIRouter()
logger = get_logger(__name__)


class RegisterInput(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=6)
    full_name: str | None = None


class LoginInput(BaseModel):
    email: str
    password: str


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        return False


@auth_router.post('/auth/register')
async def register(request: Request, inputs: RegisterInput) -> JSONResponse:
    exception_handler = ExceptionHandler(logger=logger.bind(), service_name=__name__)
    try:
        resources = get_resources(request)
        with resources.sql_database.get_session() as session:
            existing = resources.sql_database.get_users(
                session, filter={'email': inputs.email},
            )
            if existing:
                return exception_handler.handle_bad_request(
                    message='Email already registered',
                    extra={'email': inputs.email},
                )

            user_id = str(uuid.uuid4())
            user = UserSchema(
                id=user_id,
                email=inputs.email,
                full_name=inputs.full_name,
                role='user',
            )
            resources.sql_database.insert_user(session, user)

            auth = UserAuthSchema(
                id=str(uuid.uuid4()),
                user_id=user_id,
                username=inputs.email,
                password=_hash_password(inputs.password),
            )
            resources.sql_database.insert_user_authentication(session, auth)

        return exception_handler.handle_success({'email': inputs.email, 'full_name': inputs.full_name})
    except Exception as e:
        return exception_handler.handle_exception(e=f'register failed: {e!s}', extra={})


@auth_router.post('/auth/login')
async def login(request: Request, inputs: LoginInput) -> JSONResponse:
    exception_handler = ExceptionHandler(logger=logger.bind(), service_name=__name__)
    try:
        resources = get_resources(request)
        with resources.sql_database.get_session() as session:
            users = resources.sql_database.get_users(
                session, filter={'email': inputs.email},
            )
            user = users[0] if users else None
            if not user:
                return exception_handler.handle_unauthorized_error(
                    message='Invalid credentials', extra={'email': inputs.email},
                )

            auths = resources.sql_database.get_user_authentications(
                session, filter={'user_id': user.id},
            )
            auth = auths[0] if auths else None
            if not auth or not _verify_password(inputs.password, auth.password):
                return exception_handler.handle_unauthorized_error(
                    message='Invalid credentials', extra={'email': inputs.email},
                )

        return exception_handler.handle_success({
            'email': user.email,
            'full_name': user.full_name,
        })
    except Exception as e:
        return exception_handler.handle_exception(e=f'login failed: {e!s}', extra={})

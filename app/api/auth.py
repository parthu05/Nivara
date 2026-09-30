from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.models import AuthToken, ChatSession, SessionLocal, UserAccount
from app.helplines import helpline_for_country, normalize_country

router = APIRouter(prefix="/api/auth", tags=["auth"])
_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_TOKEN_LIFETIME = timedelta(days=30)


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=10, max_length=128)
    country: str = Field(min_length=2, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _EMAIL.fullmatch(normalized):
            raise ValueError("Enter a valid email address.")
        return normalized

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        normalized = normalize_country(value)
        if not normalized:
            raise ValueError("Enter your country.")
        return normalized


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _EMAIL.fullmatch(normalized):
            raise ValueError("Enter a valid email address.")
        return normalized


def _password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = stored_hash.split("$", maxsplit=2)
        if algorithm != "scrypt":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _issue_token(db, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    db.add(
        AuthToken(
            token_hash=_token_hash(token),
            user_id=user_id,
            expires_at=datetime.utcnow() + _TOKEN_LIFETIME,
        )
    )
    return token


def _auth_response(user: UserAccount, token: str) -> dict:
    return {
        "token": token,
        "email": user.email,
        "country": user.country,
        "helpline": helpline_for_country(user.country),
    }


@router.post("/register", status_code=201)
def register(payload: RegisterRequest) -> dict:
    try:
        with SessionLocal() as db:
            existing = db.scalar(
                select(UserAccount).where(UserAccount.email == payload.email)
            )
            if existing:
                raise HTTPException(status_code=409, detail="An account already uses that email.")

            session_id = uuid.uuid4().hex
            user = UserAccount(
                email=payload.email,
                password_hash=_password_hash(payload.password),
                country=payload.country,
                session_id=session_id,
            )
            db.add(user)
            db.flush()
            db.add(ChatSession(id=session_id, profile_summary=""))
            token = _issue_token(db, user.id)
            db.commit()
            return _auth_response(user, token)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="An account already uses that email.") from exc


@router.post("/login")
def login(payload: LoginRequest) -> dict:
    with SessionLocal() as db:
        user = db.scalar(select(UserAccount).where(UserAccount.email == payload.email))
        if user is None or not _verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        token = _issue_token(db, user.id)
        db.commit()
        return _auth_response(user, token)


def get_current_user(authorization: str | None = Header(default=None)) -> UserAccount:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Sign in to continue.")

    with SessionLocal() as db:
        stored_token = db.get(AuthToken, _token_hash(token))
        if stored_token is None:
            raise HTTPException(status_code=401, detail="Your session has expired. Sign in again.")
        if stored_token.expires_at <= datetime.utcnow():
            db.delete(stored_token)
            db.commit()
            raise HTTPException(status_code=401, detail="Your session has expired. Sign in again.")
        user = db.get(UserAccount, stored_token.user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="Sign in to continue.")
        return user


@router.get("/me")
def current_user(user: UserAccount = Depends(get_current_user)) -> dict:
    return {"email": user.email, "country": user.country, "helpline": helpline_for_country(user.country)}


@router.post("/logout")
def logout(
    user: UserAccount = Depends(get_current_user),
    authorization: str = Header(),
) -> dict:
    del user
    token = authorization.removeprefix("Bearer ").strip()
    with SessionLocal() as db:
        stored_token = db.get(AuthToken, _token_hash(token))
        if stored_token is not None:
            db.delete(stored_token)
            db.commit()
    return {"ok": True}
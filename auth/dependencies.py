from fastapi import Header, HTTPException, status

from services.db import db


async def is_authorized(authorization: str = Header()) -> dict:
    if authorization is None or 'Bearer ' not in authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    token = authorization.replace('Bearer ', '')
    if not (await db.check_session(token)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

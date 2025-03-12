from fastapi import APIRouter, Depends, Header

from services.db import db
from auth.dependencies import is_authorized
from schemas import auth


router = APIRouter(prefix='/auth')


@router.get('/user/', dependencies=[Depends(is_authorized)])
async def get_current_user_info(authorization: str = Header()):
    """Возвращает роль, id пользователя"""
    role, uid = await db.get_user_info_by_token(authorization.replace('Bearer ', ''))
    return {'status': True, 'role': role, 'uid': uid}


@router.get('/users/{user_id}/', dependencies=[Depends(is_authorized)])
async def get_user():
    """Возвращает данные пользователя"""
    return (await db.get_user())


@router.get('/clients/{uid}/', dependencies=[Depends(is_authorized)])
async def get_client_code(uid: int):
    """Возвращает код клиента"""
    return (await db.get_client_info(uid))


@router.post('/clients/')
async def registrate_client(client: auth.CreateClient):
    """Регистрация покупателя"""
    res = await db.create_client(client)
    return res


@router.get('/sellers/{seller_id}/', dependencies=[Depends(is_authorized)])
async def get_seller_info_by_id(seller_id: int):
    """Возвращает название продавца по id"""
    return (await db.get_seller_info_by_id(seller_id))


@router.post('/sellers/')
async def registrate_seller(seller: auth.CreateSeller):
    """Регистрация продавца"""
    res = await db.create_seller(seller)
    return res


@router.get('/points/', dependencies=[Depends(is_authorized)])
async def get_points():
    """Возвращает активные пункты выдачи"""
    return (await db.get_points())


@router.post('/points/')
async def registrate_seller(point: auth.CreatePoint):
    """Регистрация пункта выдачи"""
    res = await db.create_point(point)
    return res


@router.post('/session/')
async def new_session(form: auth.Login):
    """Проверка логина и пароля и создание сессии"""
    res = await db.create_session(form)
    return res


@router.delete('/session/')
async def delete_session(authorization: str = Header()):
    """Удаляет сессию"""
    await db.delete_session(authorization.replace('Bearer ', ''))
    return {'status': True}

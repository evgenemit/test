from fastapi import APIRouter, Depends, Query, Path, Header

from services.db import db
from auth.dependencies import is_authorized
from schemas import orders


router = APIRouter(prefix='/orders')


@router.post('/', dependencies=[Depends(is_authorized)])
async def create_order(order: orders.Order):
    """Создает заказ"""
    # TODO: only client
    await db.create_order(order)
    return {'status': True}


@router.get('/', dependencies=[Depends(is_authorized)])
async def get_orders(uid: int, role: str):
    """Возвращает заказы пользователя"""
    res = await db.get_orders(role, uid)
    return res


@router.get('/{order_id}/', dependencies=[Depends(is_authorized)])
async def get_order(order_id: int = Path(), role: str = Query()):
    """Возвращает заказ"""
    res = await db.get_order(order_id, role)
    return res


@router.delete('/{order_id}/', dependencies=[Depends(is_authorized)])
async def cancle_order(order_id: int = Path(), role: str = Query()):
    """Отменяет заказ"""
    res = await db.cancle_order(order_id, role)
    return res


@router.put('/{order_id}/', dependencies=[Depends(is_authorized)])
async def update_status(order_id: int, status: int = 1):
    """Обновляет статус заказа"""
    res = await db.update_order_status(order_id, status)
    return res

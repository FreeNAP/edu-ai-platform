"""订单模块（契约第4节）：我的订单/模拟支付/取消。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Course, Enrollment, Order, User
from ..serializers import order_out
from ..services.notify import notify
from ..utils import ok

router = APIRouter(prefix="/api/orders", tags=["订单"])


def mark_order_paid(db: Session, order: Order) -> None:
    """订单支付成功：标记已支付、自动报名课程、通知下单人（不 commit）。"""
    order.status = "paid"
    order.paid_at = datetime.now()
    course = db.get(Course, order.course_id)
    title = course.title if course else "课程"
    notify(
        db, order.user_id, "order", "订单支付成功",
        f"订单 {order.order_no} 已支付 ¥{order.amount:g}，已为你开通《{title}》，快去学习吧。",
    )
    enrolled = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == order.user_id,
            Enrollment.course_id == order.course_id,
        )
        .first()
    )
    if enrolled is None:
        db.add(Enrollment(user_id=order.user_id, course_id=order.course_id))
        if course is not None:
            course.students_count = (course.students_count or 0) + 1


@router.get("")
def my_orders(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return ok([order_out(o) for o in orders])


def _my_pending_order(db: Session, user: User, order_id: int) -> Order:
    order = db.get(Order, order_id)
    if order is None or order.user_id != user.id:
        raise HTTPException(404, "订单不存在")
    return order


@router.post("/{order_id}/pay")
def pay_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = _my_pending_order(db, user, order_id)
    if order.status == "paid":
        raise HTTPException(400, "订单已支付")
    if order.status == "cancelled":
        raise HTTPException(400, "订单已取消，无法支付")
    course = db.get(Course, order.course_id)
    if course is None or course.status != "on":
        raise HTTPException(400, "课程已下架，无法支付")
    mark_order_paid(db, order)
    db.commit()
    db.refresh(order)
    return ok(order_out(order))


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = _my_pending_order(db, user, order_id)
    if order.status == "paid":
        raise HTTPException(400, "已支付订单不能取消")
    if order.status == "cancelled":
        return ok(order_out(order))
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return ok(order_out(order))

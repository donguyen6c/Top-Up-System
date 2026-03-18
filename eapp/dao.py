from datetime import datetime

from sqlalchemy.exc import IntegrityError
from eapp.models import Category, Product, User, Receipt, ReceiptDetails, Discount, Card
import hashlib
from eapp import app, db
import cloudinary.uploader
from flask_login import current_user
from sqlalchemy import func

from eapp.utils import stats_cart


def load_categories():
    return Category.query.all()

def load_products(cate_id=None, kw=None, page=1):
    query = Product.query

    if kw:
        query = query.filter(Product.name.contains(kw))

    if cate_id:
        query = query.filter(Product.category_id.__eq__(cate_id))

    return query.all()

def count_products():
    return Product.query.count()

def get_user_by_id(id):
    return User.query.get(id)

def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(User.username==username,
                             User.password==password).first()

def add_user(name, username, password, avatar):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = User(name=name.strip(), username=username.strip(), password=password)
    if avatar:
        res = cloudinary.uploader.upload(avatar)
        u.avatar = res.get("secure_url")

    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Exception('Username đã tồn tại!')


def count_product_by_cate():
    return (db.session.query(Category.id, Category.name, func.count(Card.id))
            .join(Product, Product.category_id == Category.id)
            .join(Card, Card.product_id == Product.id)
            .filter(Card.is_sold == False)
            .group_by(Category.id).all())

def add_receipt(cart, discount_code=None):
    if not cart:
        raise Exception("Giỏ hàng đang trống!")

    stats = stats_cart(cart)
    total_amount = stats['total_amount']
    final_amount = total_amount
    discount_id = None

    if discount_code:
        discount_result = check_and_apply_discount(discount_code, cart)
        if discount_result['success']:
            final_amount = total_amount - discount_result['discount_amount']
            discount_id = discount_result['discount_id']
        else:
            raise Exception(discount_result['message'])

    r = Receipt(
        user_id=current_user.id,
        total_amount=total_amount,
        final_amount=final_amount,
        discount_id=discount_id
    )
    db.session.add(r)

    for c in cart.values():
        d = ReceiptDetails(
            quantity=c['quantity'],
            unit_price=c['price'],
            product_id=c['id'],
            receipt=r
        )
        db.session.add(d)

        available_cards = Card.query.filter(
            Card.product_id == c['id'],
            Card.is_sold == False
        ).limit(c['quantity']).all()

        if len(available_cards) < c['quantity']:
            db.session.rollback()
            raise Exception(f"Sản phẩm '{c['name']}' chỉ còn {len(available_cards)} thẻ trong kho. Vui lòng giảm số lượng!")

        for card in available_cards:
            card.is_sold = True
            card.sold_receipt = r
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise Exception("Có lỗi xảy ra trong quá trình ghi nhận đơn hàng!")


def check_and_apply_discount(code_input, cart):
    if not cart:
        return {"success": False, "message": "Giỏ hàng trống!"}

    discount = Discount.query.filter_by(code=code_input).first()
    if not discount:
        return {"success": False, "message": "Mã giảm giá không tồn tại!"}

    if discount.end_date < datetime.now():
        return {"success": False, "message": "Mã giảm giá đã hết hạn!"}

    eligible_items = []
    for item in cart.values():
        if discount.applied_card_type is None or item.get('card_type') == discount.applied_card_type.value:
            for _ in range(item['quantity']):
                eligible_items.append(item['price'])

    if len(eligible_items) < discount.min_quantity:
        return {"success": False, "message": f"Cần mua ít nhất {discount.min_quantity} thẻ hợp lệ để áp dụng mã!"}

    eligible_items.sort(reverse=True)

    warning_msg = ""
    if discount.max_quantity and len(eligible_items) > discount.max_quantity:
        applied_items = eligible_items[:discount.max_quantity]
        warning_msg = f"Lưu ý: Mã chỉ giảm giá cho {discount.max_quantity} thẻ có mệnh giá cao nhất. Các thẻ còn lại tính giá gốc."
    else:
        applied_items = eligible_items

    if discount.discount_type.value == 1:
        discount_amount = sum(applied_items) * (discount.value / 100)
    else:
        discount_amount = discount.value

    return {
        "success": True,
        "discount_amount": discount_amount,
        "message": warning_msg if warning_msg else "Áp dụng mã thành công!",
        "discount_id": discount.id
    }
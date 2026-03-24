import re
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from eapp.models import Category, Product, User, Receipt, ReceiptDetails, Discount, Card, DiscountType, Banner
import hashlib
from eapp import app, db, utils
import cloudinary.uploader
from flask_login import current_user
from sqlalchemy import func

from eapp.utils import stats_cart


def load_categories():
    return Category.query.all()

def load_banners():
    return Banner.query.filter(Banner.active == True).all()

def load_discounts():
    return Discount.query.filter(Discount.active == True).all()

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

def add_user(name, username, password, avatar, email):
    if not name: raise ValueError("Thiếu trường name")
    if not username: raise ValueError("Thiếu trường username")
    if not email: raise ValueError("Thiếu trường email")
    if not password: raise ValueError("Thiếu trường password")

    if len(username) < 5:
        raise ValueError("Username phải ít nhất có 5 kí tự")
    if len(password) < 8:
        raise ValueError("Mật khẩu phải có ít nhất 8 kí tự")
    if not re.search(r'[0-9]', password):
        raise ValueError("Mật khẩu phải chứa ít nhất một chữ số")
    if not re.search(r'[a-z]', password):
        raise ValueError("Mật khẩu phải chứa ít nhất một chữ thường")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Mật khẩu phải chứa ít nhất một chữ hoa")
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValueError("Email không hợp lệ")
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = User(name=name.strip(), username=username.strip(), password=password, email=email)
    if avatar:
        res = cloudinary.uploader.upload(avatar)
        u.avatar = res.get("secure_url")

    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Exception('Username hoặc email đã tồn tại!')


def count_product_by_cate():
    return (db.session.query(Category.id, Category.name, func.count(Card.id))
            .join(Product, Product.category_id == Category.id)
            .join(Card, Card.product_id == Product.id)
            .filter(Card.is_sold == False)
            .group_by(Category.id).all())

def add_receipt(user_id, cart, discount_code=None):
    if not cart:
        raise Exception("Giỏ hàng đang trống!")

    stats = stats_cart(cart)
    total_amount = stats['total_amount']
    final_amount = total_amount
    discount_id = None

    if discount_code:
        discount_result = check_discount(discount_code, cart)
        if discount_result['success']:
            final_amount = total_amount - discount_result['discount_amount']
            discount_id = discount_result['discount_id']
        else:
            raise Exception(discount_result['message'])

    r = Receipt(
        user_id=user_id,
        total_amount=total_amount,
        final_amount=final_amount,
        discount_id=discount_id
    )
    db.session.add(r)

    for c in cart.values():
        buy_qty = c['quantity']
        product_id = c['id']

        d = ReceiptDetails(
            quantity=buy_qty,
            unit_price=c['price'],
            product_id=product_id,
            receipt=r
        )
        db.session.add(d)

        product = Product.query.get(product_id)
        if not product:
            db.session.rollback()
            raise Exception(f"Sản phẩm '{c['name']}' không tồn tại trong hệ thống!")

        available_cards = Card.query.filter(
            Card.product_id == product_id,
            Card.is_sold == False
        ).limit(buy_qty).all()

        if len(available_cards) < buy_qty:
            db.session.rollback()
            raise Exception(f"Sản phẩm '{c['name']}' chỉ còn {len(available_cards)} thẻ. Vui lòng giảm số lượng!")

        for card in available_cards:
            card.is_sold = True
            card.sold_receipt = r

        product.inventory -= buy_qty

    if discount_id:
        discount_obj = Discount.query.get(discount_id)
        if discount_obj:
            discount_obj.used_count += 1

    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi thanh toán: {str(e)}")
        raise Exception("Có lỗi xảy ra trong quá trình ghi nhận đơn hàng!")


def check_discount(code, cart):
    fail_res = {'success': False, 'discount_amount': 0, 'message': "", 'discount_id': None}

    if not cart:
        fail_res['message'] = "Giỏ hàng rỗng!"
        return fail_res

    discount = Discount.query.filter(Discount.code == code, Discount.active == True).first()
    if not discount:
        fail_res['message'] = "Mã giảm giá không tồn tại!"
        return fail_res

    if discount.usage_limit is not None:
        if discount.used_count >= discount.usage_limit:
            fail_res['message'] = f"Mã này đã hết lượt sử dụng (Giới hạn: {discount.usage_limit} lần)!"
            return fail_res

    now = datetime.now()
    if now < discount.start_date or now > discount.end_date:
        fail_res['message'] = "Mã giảm giá đã hết hạn!"
        return fail_res

    stats = utils.stats_cart(cart)
    applicable_qty = 0
    applicable_amount = 0

    if discount.applied_card_type:
        target_type = discount.applied_card_type.value if hasattr(discount.applied_card_type, 'value') else str(
            discount.applied_card_type)
        target_type = str(target_type).lower()

        if 'phone' in target_type:
            target_type = 'phone'
        elif 'game' in target_type:
            target_type = 'game'

        if target_type == 'game':
            applicable_qty = stats.get('game_quantity', 0)
            applicable_amount = sum([c['price'] * c['quantity'] for c in cart.values() if c.get('card_type') == 'game'])
        elif target_type == 'phone':
            applicable_qty = stats.get('phone_quantity', 0)
            applicable_amount = sum(
                [c['price'] * c['quantity'] for c in cart.values() if c.get('card_type') == 'phone'])

        if applicable_qty == 0:
            fail_res['message'] = f"Mã này chỉ áp dụng cho thẻ {target_type.upper()}!"
            return fail_res
    else:
        applicable_qty = stats.get('total_quantity', 0)
        applicable_amount = stats.get('total_amount', 0)

    if applicable_qty < discount.min_quantity:
        fail_res['message'] = f"Cần mua ít nhất {discount.min_quantity} thẻ để áp dụng mã!"
        return fail_res

    if discount.max_quantity and applicable_qty > discount.max_quantity:
        fail_res['message'] = f"Mã này chỉ áp dụng khi mua tối đa {discount.max_quantity} thẻ!"
        return fail_res

    if discount.discount_type == DiscountType.PERCENTAGE:
        discount_amount = applicable_amount * (discount.value / 100)
    else:
        discount_amount = discount.value

    discount_amount = min(discount_amount, applicable_amount)

    return {
        'success': True,
        'discount_amount': discount_amount,
        'message': "Áp dụng mã giảm giá thành công!",
        'discount_id': discount.id
    }

def get_receipts_by_user(user_id):
    return Receipt.query.filter(Receipt.user_id == user_id).order_by(Receipt.created_date.desc()).all()

def get_cards_by_user(user_id):
    return (Card.query.join(Receipt, Card.receipt_id == Receipt.id).
            filter(Receipt.user_id == user_id, Card.is_sold == True)
            .order_by(Receipt.created_date.desc()).all())

def revenue_by_product():
    return (db.session.query(Product.id, Product.name, func.sum(ReceiptDetails.unit_price * ReceiptDetails.quantity))
            .join(ReceiptDetails, ReceiptDetails.product_id == Product.id)
            .group_by(Product.id, Product.name).all())

def revenue_by_time(period="month"):
    return ((db.session.query(func.extract('month', Receipt.created_date), func.sum(Receipt.final_amount))
            .group_by(func.extract('month', Receipt.created_date)))
            .order_by(func.extract('month', Receipt.created_date)).all())

def update_profile(user_id, name, email, avatar_file=None):
    user = User.query.get(user_id)
    if not user:
        raise Exception("Tài khoản không tồn tại!")

    existing_user = User.query.filter(User.email == email, User.id != user_id).first()
    if existing_user:
        raise Exception("Email này đã được sử dụng bởi một tài khoản khác!")

    user.name = name
    user.email = email

    if avatar_file:
        try:
            res = cloudinary.uploader.upload(avatar_file)
            user.avatar = res['secure_url']
        except Exception as e:
            raise Exception(f"Lỗi khi tải ảnh lên: {str(e)}")

    db.session.commit()
    return True
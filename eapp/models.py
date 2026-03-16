from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Float, Enum, DateTime
from sqlalchemy.orm import relationship
from eapp import db, app
from flask_login import UserMixin
from enum import Enum as PyEnum
from datetime import datetime


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    active = Column(Boolean, default=True)


class UserRole(PyEnum):
    USER = 1
    ADMIN = 2


class DiscountType(PyEnum):
    PERCENTAGE = 1
    FIXED_AMOUNT = 2


class CardType(PyEnum):
    PHONE = 'phone'
    GAME = 'game'


class User(BaseModel, UserMixin):
    name = Column(String(50), nullable=False)
    avatar = Column(String(255), default='https://res.cloudinary.com/default_avatar.jpg')
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    user_role = Column(Enum(UserRole), default=UserRole.USER)

    receipts = relationship('Receipt', backref='user', lazy=True)


class Category(BaseModel):
    name = Column(String(50), unique=True, nullable=False)
    card_type = Column(Enum(CardType), default=CardType.PHONE, nullable=False)

    products = relationship('Product', backref='category', lazy=True)


class Product(BaseModel):
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, default=0)  #
    image = Column(String(255), nullable=True)

    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)

    cards = relationship('Card', backref='product', lazy=True)
    details = relationship('ReceiptDetails', backref='product', lazy=True)


class Card(BaseModel):
    serial_number = Column(String(100), nullable=False, unique=True)
    pin_code = Column(String(100), nullable=False, unique=True)
    expiry_date = Column(DateTime, nullable=False)
    is_sold = Column(Boolean, default=False)

    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    receipt_id = Column(Integer, ForeignKey('receipt.id'), nullable=True)


class Discount(BaseModel):
    code = Column(String(20), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    discount_type = Column(Enum(DiscountType), default=DiscountType.PERCENTAGE)
    value = Column(Float, nullable=False)

    applied_card_type = Column(Enum(CardType), nullable=True)

    start_date = Column(DateTime, default=datetime.now)
    end_date = Column(DateTime, nullable=False)

    min_quantity = Column(Integer, default=1)
    max_quantity = Column(Integer, nullable=True)

    receipts = relationship('Receipt', backref='discount_applied', lazy=True)


class Receipt(BaseModel):
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now)
    total_amount = Column(Float, default=0)
    final_amount = Column(Float, default=0)

    discount_id = Column(Integer, ForeignKey(Discount.id), nullable=True)

    details = relationship('ReceiptDetails', backref='receipt', lazy=True)
    cards_sold = relationship('Card', backref='sold_receipt', lazy=True)


class ReceiptDetails(BaseModel):
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0)

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        import hashlib
        import random
        import uuid
        from datetime import datetime, timedelta

        admin = User(name='Admin', username='admin',
                     password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                     user_role=UserRole.ADMIN)

        test_user = User(name='Khách hàng', username='user',
                         password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                         user_role=UserRole.USER)

        db.session.add_all([admin, test_user])
        db.session.commit()

        cat_viettel = Category(name='Viettel', card_type=CardType.PHONE)
        cat_mobi = Category(name='Mobifone', card_type=CardType.PHONE)
        cat_vina = Category(name='Vinaphone', card_type=CardType.PHONE)
        cat_garena = Category(name='Garena', card_type=CardType.GAME)
        cat_zing = Category(name='Zing', card_type=CardType.GAME)

        db.session.add_all([cat_viettel, cat_mobi, cat_vina, cat_garena, cat_zing])
        db.session.commit()

        products_data = [
            {"name": "Thẻ Viettel 10k", "price": 10000, "cat": cat_viettel},
            {"name": "Thẻ Viettel 20k", "price": 20000, "cat": cat_viettel},
            {"name": "Thẻ Viettel 50k", "price": 50000, "cat": cat_viettel},
            {"name": "Thẻ Viettel 100k", "price": 100000, "cat": cat_viettel},
            {"name": "Thẻ Viettel 500k", "price": 500000, "cat": cat_viettel},

            {"name": "Thẻ Mobifone 50k", "price": 50000, "cat": cat_mobi},
            {"name": "Thẻ Mobifone 100k", "price": 100000, "cat": cat_mobi},
            {"name": "Thẻ Vinaphone 50k", "price": 50000, "cat": cat_vina},
            {"name": "Thẻ Vinaphone 100k", "price": 100000, "cat": cat_vina},

            {"name": "Thẻ Garena 20k", "price": 20000, "cat": cat_garena},
            {"name": "Thẻ Garena 50k", "price": 50000, "cat": cat_garena},
            {"name": "Thẻ Garena 100k", "price": 100000, "cat": cat_garena},
            {"name": "Thẻ Garena 200k", "price": 200000, "cat": cat_garena},
            {"name": "Thẻ Garena 500k", "price": 500000, "cat": cat_garena},

            {"name": "Thẻ Zing 20k", "price": 20000, "cat": cat_zing},
            {"name": "Thẻ Zing 50k", "price": 50000, "cat": cat_zing},
            {"name": "Thẻ Zing 100k", "price": 100000, "cat": cat_zing},
        ]

        product_objs = []
        for p in products_data:
            pro = Product(name=p["name"], price=p["price"], category_id=p["cat"].id)
            db.session.add(pro)
            product_objs.append(pro)

        db.session.commit()

        expiry_date_future = datetime.now() + timedelta(days=365)

        for pro in product_objs:
            for i in range(5):
                serial = f"{pro.category.name[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"
                pin = f"PIN{uuid.uuid4().hex[:12].upper()}"

                card = Card(
                    serial_number=serial,
                    pin_code=pin,
                    expiry_date=expiry_date_future,
                    is_sold=False,
                    product_id=pro.id
                )
                db.session.add(card)

        db.session.commit()

        discount1 = Discount(
            code="GGS1",
            description="Giảm 20% thẻ Game. Mua ít nhất 2, tối đa 5.",
            discount_type=DiscountType.PERCENTAGE,
            value=20,
            applied_card_type=CardType.GAME,
            end_date=datetime.now() + timedelta(days=30),
            min_quantity=2,
            max_quantity=5
        )

        discount2 = Discount(
            code="PHONE10",
            description="Giảm 10% thẻ Điện thoại. Mua ít nhất 1, tối đa 3.",
            discount_type=DiscountType.PERCENTAGE,
            value=10,
            applied_card_type=CardType.PHONE,
            end_date=datetime.now() + timedelta(days=30),
            min_quantity=1,
            max_quantity=3
        )

        db.session.add_all([discount1, discount2])
        db.session.commit()

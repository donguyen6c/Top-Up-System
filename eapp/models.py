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

    email = Column(String(100), nullable=False, unique=True)

    password = Column(String(50), nullable=False)
    user_role = Column(Enum(UserRole), default=UserRole.USER)

    receipts = relationship('Receipt', backref='user', lazy=True)


class Category(BaseModel):
    name = Column(String(50), unique=True, nullable=False)
    card_type = Column(Enum(CardType), default=CardType.PHONE, nullable=False)
    image = Column(String(255), nullable=True)
    products = relationship('Product', backref='category', lazy=True)

    def __str__(self):
        return self.name


class Product(BaseModel):
    name = Column(String(255), nullable=False)
    price = Column(Float, default=0)
    inventory = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    cards = relationship('Card', backref='product', lazy=True)
    details = relationship('ReceiptDetails', backref='product', lazy=True)

    def __str__(self):
        return self.name


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
    usage_limit = db.Column(db.Integer, default=1)
    used_count = db.Column(db.Integer, default=0)
    receipts = relationship('Receipt', backref='discount_applied', lazy=True)

    def __str__(self):
        return self.code


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

class Banner(BaseModel):
    title = Column(String(100))
    image_url = Column(String(255), nullable=False)

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        import hashlib
        import random
        import uuid
        from datetime import datetime, timedelta

        admin = User(name='Admin', username='admin',
                     email='donguyen6c@gmail.com',
                     password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                     user_role=UserRole.ADMIN ,avatar='https://res.cloudinary.com/dfgicbdji/image/upload/v1773807215/user-icon-flat-isolated-on-white-background-user-symbol-vector-illustration_tjibsq.jpg')

        test_user = User(name='Khách hàng', username='user',
                         email='doly2301a@gmail.com',
                         password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                         user_role=UserRole.USER ,avatar='https://res.cloudinary.com/dfgicbdji/image/upload/v1773821619/vector-flat-illustration-grayscale-avatar-260nw-2628520697_j4ch5h.jpg')

        db.session.add_all([admin, test_user])
        db.session.commit()

        cat_viettel = Category(name='Viettel', card_type=CardType.PHONE,
                               image='https://res.cloudinary.com/dfgicbdji/image/upload/v1773654323/viettel_lu78eq.png')
        cat_mobi = Category(name='Mobifone', card_type=CardType.PHONE,
                            image='https://res.cloudinary.com/dfgicbdji/image/upload/v1773654323/mobi_hlcgr2.png')
        cat_vina = Category(name='Vinaphone', card_type=CardType.PHONE,
                            image='https://res.cloudinary.com/dfgicbdji/image/upload/v1773654323/vina_icazwc.png')

        cat_garena = Category(name='Garena', card_type=CardType.GAME,
                              image='https://res.cloudinary.com/dfgicbdji/image/upload/v1773654323/garena_jr4pg1.png')
        cat_zing = Category(name='Zing', card_type=CardType.GAME,
                            image='https://res.cloudinary.com/dfgicbdji/image/upload/v1773654323/zing_gkfb9w.png')

        db.session.add_all([cat_viettel, cat_mobi, cat_vina, cat_garena, cat_zing])
        db.session.commit()

        products_data = [
            {"name": "Thẻ Viettel 10k", "price": 10000, "cat": cat_viettel},
            {"name": "Thẻ Viettel 20k", "price": 20000, "cat": cat_viettel},
            {"name": "Thẻ Viettel 50k", "price": 50000, "cat": cat_viettel},
            {"name": "Thẻ Viettel 100k", "price": 100000, "cat": cat_viettel},
            {"name": "Thẻ Viettel 200k", "price": 200000, "cat": cat_viettel},
            {"name": "Thẻ Viettel 500k", "price": 500000, "cat": cat_viettel},
            {"name": "Thẻ Viettel 1000k", "price": 1000000, "cat": cat_viettel},
            {"name": "Thẻ Viettel 2000k", "price": 2000000, "cat": cat_viettel},

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
            pro = Product(name=p["name"], price=p["price"], category_id=p["cat"].id, inventory=random.randint(5, 20))
            db.session.add(pro)
            product_objs.append(pro)

        db.session.commit()

        expiry_date_future = datetime.now() + timedelta(days=365)
        for pro in product_objs:
            for i in range(pro.inventory):
                serial = f"{pro.category.name[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"
                pin = f"PIN{uuid.uuid4().hex[:12].upper()}"
                card = Card(serial_number=serial, pin_code=pin, expiry_date=expiry_date_future,
                            is_sold=False, product_id=pro.id)
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

        banner1 = Banner(
            title="GGS1",
            image_url="https://res.cloudinary.com/dfgicbdji/image/upload/v1774192206/GAME_kk4hfj.png"
        )

        banner2 = Banner(
            title="PHONE10",
            image_url="https://res.cloudinary.com/dfgicbdji/image/upload/v1774192067/Promotional_Banner_for_Exclusive_PHONE10_Offer_enbyur.png"
        )

        db.session.add_all([banner1, banner2])
        db.session.commit()

        db.session.add_all([discount1, discount2])
        db.session.commit()
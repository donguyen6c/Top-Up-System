import pytest
from unicodedata import category

from eapp import dao, db
from eapp.models import User, Category, Product, Card, Receipt, ReceiptDetails
from datetime import datetime, timedelta
from .base import test_app, test_session

@pytest.fixture
def sample_receipt(test_session):
    u = User(name="buyer", username="testbuyer", password="Abc@1234", email="buyer@gmail.com", avatar=None)
    test_session.add(u)
    test_session.commit()

    cate = Category(name="testcategory")
    test_session.add(cate)
    test_session.commit()

    p = Product(name="garena", price=50000, inventory=3, category_id=cate.id)
    test_session.add(p)
    test_session.commit()

    for i in range(3):
        c = Card(serial_number=f"SERI-{i}", pin_code=f"PIN-{i}",
                 expiry_date=datetime.now() + timedelta(days=30),
                 product_id=p.id, is_sold=False)
        test_session.add(c)

    test_session.commit()
    return {"user_id": u.id, "product_id": p.id, "product_name": p.name}

def test_receipt_empty(test_session, sample_receipt):
    with pytest.raises(Exception, match="Giỏ hàng đang trống!"):
        dao.add_receipt(user_id=sample_receipt["user_id"], cart={})

def test_add_receipt_out_of_stock(test_session, sample_receipt):
    cart =  {
        "1" :{
            "id": sample_receipt["product_id"],
            "name": sample_receipt["product_name"],
            "price": 50000,
            "quantity": 4
        }
    }
    with pytest.raises(Exception, match=f"Sản phẩm '{sample_receipt["product_name"]}' chỉ còn .* thẻ. Vui lòng giảm số lượng!"):
        dao.add_receipt(user_id=sample_receipt["user_id"], cart=cart)

def test_receipt_success(test_session, sample_receipt):
    cart = {
        "1": {
            "id": sample_receipt["product_id"],
            "name": sample_receipt["product_name"],
            "price": 50000,
            "quantity": 3
        }
    }

    success_receipt = dao.add_receipt(user_id=sample_receipt["user_id"], cart=cart)
    assert success_receipt["user_id"] == sample_receipt["user_id"]
    assert success_receipt is True

    receipt = Receipt.query.filter_by(user_id=sample_receipt["user_id"]).first()
    assert receipt.total_amount == 150000

    cards = Card.query.filter_by(receipt_id=receipt.id).all()

    assert len(cards) == 3
    assert all(c.is_sold is True for c in cards)

def test_receipt_history_details(test_session, sample_receipt):
    cart ={"1": {"id": sample_receipt["product_id"], "name": sample_receipt["product_name"],
                 "price": 50000, "quantity": 3}}
    dao.add_receipt(user_id=sample_receipt["user_id"], cart=cart)

    history = dao.get_receipts_by_user(sample_receipt["user_id"])
    assert len(history) == 5

    actual_receipt = history[0]
    assert len (actual_receipt.details) == 3
    assert actual_receipt.details[0].total_amount == 150000

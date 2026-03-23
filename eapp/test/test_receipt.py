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
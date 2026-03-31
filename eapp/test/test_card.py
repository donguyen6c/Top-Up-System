from eapp.models import Card, User, Category, Product, Receipt # Thêm import Receipt
from eapp.dao import get_cards_by_user
from .base import test_app, test_session
import pytest
from datetime import datetime, timedelta

@pytest.fixture
def sample_card(test_session):
    u = User(name="Khách Hàng", username="khachhang1", password="123", email="khach@gmail.com")
    test_session.add(u)
    test_session.commit()

    cate = Category(name="Viễn thông")
    test_session.add(cate)
    test_session.commit()

    p = Product(name="Viettel 50k", price=50000, inventory=10, category_id=cate.id)
    test_session.add(p)
    test_session.commit()

    r = Receipt(user_id=u.id, total_amount=150000, created_date=datetime.now())
    test_session.add(r)
    test_session.commit()

    c1 = Card(serial_number="VIE-1", pin_code="PIN1", expiry_date=datetime(2027, 3, 24), is_sold=True, product_id=p.id, receipt_id=r.id)
    c2 = Card(serial_number="VIE-2", pin_code="PIN2", expiry_date=datetime(2027, 3, 24), is_sold=True, product_id=p.id, receipt_id=r.id)
    c3 = Card(serial_number="VIE-3", pin_code="PIN3", expiry_date=datetime(2027, 3, 24), is_sold=True, product_id=p.id, receipt_id=r.id)

    test_session.add_all([c1, c2, c3])
    test_session.commit()

    return u.id

def test_get_cards_success_count(test_session, sample_card):
    result_cards = get_cards_by_user(user_id=sample_card)

    assert len(result_cards) == 3
from eapp.models import Card, User, Category, Product
from eapp.dao import get_cards_by_user
from .base import test_app, test_session
import pytest
from datetime import datetime, timedelta

@pytest.fixture
def sample_card(test_session):
    u = User(name="Khách Hàng", username="khachhang1", password="123", email="khach@gmail.com")
    test_session.add(u)

    cate = Category(name="Viễn thông")
    test_session.add(cate)
    test_session.commit()

    p = Product(name="Viettel 50k", price=50000, inventory=10, category_id=cate.id)
    test_session.add(p)
    test_session.commit()

    c1 = Card(serial_number="VIE-E131BE93", pin_code="PINDEFF90...", expiry_date=datetime(2027, 3, 24), is_sold=False,
              product_id=p.id)
    c2 = Card(serial_number="VIE-1896261D", pin_code="PINEF1882...", expiry_date=datetime(2027, 3, 24), is_sold=False,
              product_id=p.id)
    c3 = Card(serial_number="VIE-FCC6BC76", pin_code="PIND2ACED...", expiry_date=datetime(2027, 3, 24), is_sold=False,
              product_id=p.id)

    test_session.add_all([c1, c2, c3])
    test_session.commit()

    result_cards = get_cards_by_user(user_id=u.id)

    assert len(result_cards) == 0
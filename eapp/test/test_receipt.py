import pytest
from datetime import datetime, timedelta
from eapp import dao
from eapp.models import User, Category, Product, Card, Receipt


@pytest.fixture
def sample_cards(test_session):
    u1 = User(name="User A", username="usera", password="123", email="a@gmail.com")
    u2 = User(name="User B", username="userb", password="123", email="b@gmail.com")
    test_session.add_all([u1, u2])
    test_session.commit()

    cate = Category(name="Viễn thông")
    test_session.add(cate)
    test_session.commit()

    p = Product(name="Viettel 50k", price=50000, inventory=10, category_id=cate.id)
    test_session.add(p)
    test_session.commit()

    r1_old = Receipt(user_id=u1.id, total_amount=50000, created_date=datetime.now() - timedelta(days=5))
    r2_new = Receipt(user_id=u1.id, total_amount=100000, created_date=datetime.now() - timedelta(days=1))

    r3_other = Receipt(user_id=u2.id, total_amount=50000, created_date=datetime.now())

    test_session.add_all([r1_old, r2_new, r3_other])
    test_session.commit()

    c1 = Card(serial_number="OLD-A1", pin_code="PIN1", expiry_date=datetime.now() + timedelta(days=365), is_sold=True,
              product_id=p.id, receipt_id=r1_old.id)
    c2 = Card(serial_number="NEW-A1", pin_code="PIN2", expiry_date=datetime.now() + timedelta(days=365), is_sold=True,
              product_id=p.id, receipt_id=r2_new.id)
    c3 = Card(serial_number="NEW-A2", pin_code="PIN3", expiry_date=datetime.now() + timedelta(days=365), is_sold=True,
              product_id=p.id, receipt_id=r2_new.id)
    c4 = Card(serial_number="OTHER-B1", pin_code="PIN4", expiry_date=datetime.now() + timedelta(days=365), is_sold=True,
              product_id=p.id, receipt_id=r3_other.id)
    c5 = Card(serial_number="UNSOLD-1", pin_code="PIN5", expiry_date=datetime.now() + timedelta(days=365),
              is_sold=False, product_id=p.id)

    test_session.add_all([c1, c2, c3, c4, c5])
    test_session.commit()

    return {"user_a_id": u1.id, "user_b_id": u2.id}

def test_get_cards_empty_when_unsold(test_session, sample_cards):
    u3 = User(name="User C", username="userc", password="123", email="c@gmail.com")
    test_session.add(u3)
    test_session.commit()

    cards = dao.get_cards_by_user(u3.id)

    assert cards == []


def test_get_cards_success_count(test_session, sample_cards):
    cards = dao.get_cards_by_user(sample_cards["user_a_id"])

    assert len(cards) == 3

def test_get_cards_isolation(test_session, sample_cards):
    cards = dao.get_cards_by_user(sample_cards["user_b_id"])

    assert len(cards) == 1
    assert cards[0].serial_number == "OTHER-B1"


def test_get_cards_order_desc(test_session, sample_cards):
    cards = dao.get_cards_by_user(sample_cards["user_a_id"])

    assert len(cards) == 3

    assert "NEW" in cards[0].serial_number
    assert "NEW" in cards[1].serial_number
    assert cards[2].serial_number == "OLD-A1"
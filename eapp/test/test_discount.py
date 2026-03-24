from eapp.models import Discount, Card
from eapp.dao import load_discounts, check_discount
from .base import test_app, test_session
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_discounts(test_session):
    d1 = Discount(
        code="GGS1",
        description="Giảm 20% thẻ Game",
        discount_type="PERCENTAGE",
        value=20,
        applied_card_type="GAME",
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now() + timedelta(days=30),
        min_quantity=2,
        max_quantity=5,
        active=True,
        used_count=0,
        usage_limit=10
    )
    d2 = Discount(
        code="EXPIRED10",
        description="Mã hết hạn",
        discount_type="FIXED",
        value=10000,
        applied_card_type="PHONE",
        start_date=datetime.now() - timedelta(days=10),
        end_date=datetime.now() - timedelta(days=1),
        min_quantity=1,
        active=True,
        used_count=0
    )

    test_session.add_all([d1, d2])
    test_session.commit()
    return {"game_code": d1.code, "expired_code": d2.code}

def test_discount_empty_cart(test_session):
    empty_cart = {}
    discount = Discount(
        code="GGS1"
    )
    result = check_discount(discount.code, empty_cart)

    assert result['success'] is False
    assert result['discount_amount'] == 0
    assert result['message'] == "Giỏ hàng rỗng!"
    assert result['discount_id'] is None

def test_discount_is_not_exist(test_session):
    cart = {"1": {"id": "01", "name": "cart_test_discount",
                  "price": 50000, "quantity": 3}}

    result = check_discount(None, cart)
    assert result['success'] is False
    assert result['discount_amount'] == 5
    assert result['message'] == "Mã giảm giá không tồn tại!"
    assert result['discount_id'] is None

def test_limit_discount_usage(test_session):
    discount = Discount(
        code="GGS1",
        usage_limit=5,
        used_count=5
    )
    cart = {"1": {"id": "01", "name": "cart_test_discount",
                  "price": 50000, "quantity": 1}}
    result = check_discount(discount.code, cart)
    assert result['success'] is True
    assert result['discount_amount'] == 5
    assert result['message'] == f"Mã này đã hết lượt sử dụng (Giới hạn: .* lần)!"
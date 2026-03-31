import pytest
from datetime import datetime, timedelta
from wtforms.validators import ValidationError
from flask_login import login_user
from eapp import db
from eapp.models import Discount, Card, User, UserRole, DiscountType, CardType, Receipt
from eapp.dao import check_discount
from eapp.admin import DiscountView
from .base import test_app, test_session, test_client

@pytest.fixture
def mock_users(test_session):
    admin = User(name="Admin", username="admin_test", email="admin@test.com", password="123", user_role=UserRole.ADMIN)
    user = User(name="User", username="user_test", email="user@test.com", password="123", user_role=UserRole.USER)
    test_session.add_all([admin, user])
    test_session.commit()
    return {'admin': admin, 'user': user}


@pytest.fixture
def sample_discounts(test_session):
    d1 = Discount(
        code="GGS1",
        description="Giảm 20% thẻ Game",
        discount_type=DiscountType.PERCENTAGE,
        value=20,
        applied_card_type=CardType.GAME,
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now() + timedelta(days=30),
        min_quantity=1,
        active=True,
        used_count=0,
        usage_limit=10
    )
    d2 = Discount(
        code="EXPIRED10",
        description="Mã hết hạn",
        discount_type=DiscountType.FIXED_AMOUNT,
        value=10000,
        start_date=datetime.now() - timedelta(days=10),
        end_date=datetime.now() - timedelta(days=1),
        min_quantity=1,
        active=True,
        used_count=0
    )
    test_session.add_all([d1, d2])
    test_session.commit()
    return {"game_code": d1.code, "expired_code": d2.code}

def test_security_admin_access_discount(test_client, mock_users):
    res_guest = test_client.get('/admin/discount/')
    assert res_guest.status_code in [302, 401, 403]

    with test_client.application.test_request_context():
        login_user(mock_users['user'])
        res_user_delete = test_client.post('/admin/discount/delete/', data={'id': '1'})
        assert res_user_delete.status_code in [302, 401, 403]

def test_validate_create_discount(test_session):
    admin_view = DiscountView(Discount, test_session)

    bad_time = Discount(start_date=datetime.now(), end_date=datetime.now() - timedelta(days=5))
    with pytest.raises(ValidationError, match="sau ngày bắt đầu"):
        admin_view.on_model_change(form=None, model=bad_time, is_created=True)

    bad_value = Discount(
        discount_type=DiscountType.PERCENTAGE, value=60,
        start_date=datetime.now(), end_date=datetime.now() + timedelta(days=5)
    )
    with pytest.raises(ValidationError, match="không được vượt quá 50%"):
        admin_view.on_model_change(form=None, model=bad_value, is_created=True)

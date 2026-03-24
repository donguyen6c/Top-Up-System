from .base import test_app, test_session,mock_cloudinary
import pytest
from ..models import User
from ..dao import add_user
import hashlib
import re

def test_register_success(test_session):
    add_user(name="abc", username="tester", password="aBc@1234", avatar=None, email="test@gmail.com")
    u = User.query.filter_by(username="tester").first()

    assert u is not None
    assert u.name == "abc"
    assert u.password == hashlib.md5("aBc@1234".encode("utf-8")).hexdigest()

def test_exsiting_username(test_session):
    add_user(name="abc", username="demodemo", password="aBc@1234", avatar=None, email="test@gmail.com")
    with pytest.raises(Exception):
        add_user(name="hoang", username="demodemo", password="aBc@1234", avatar=None, email="test@gmail.com")

def test_avatar(test_session, mock_cloudinary):
    add_user(name="abc", username="avataruser", password="aBc@1234",
             avatar="test", email="avatar@test.com")

    u = User.query.filter(User.name.__eq__('abc')).first()
    assert u.avatar == "https://fake-image.com"

@pytest.mark.parametrize("name, username, password, email, msg", [
    (None, "tester", "aBc@1234", "test@gmail.com", ""),
    ("abc", "test", "aBc@1234", "test@gmail.com", "Username phải ít nhất có 5 kí tự"),
    ("abc", "tester", "aBc@1234", None, "Thiếu trường email"),
    ("abc", "tester", "aBc@12", "test@gmail.com", "Mật khẩu phải có ít nhất 8 kí tự"),
    ("abc", "tester", "test@Test", "test@gmail.com", "Mật khẩu phải chứa ít nhất một chữ số"),
    ("abc", "tester", "test@1111", "test@gmail.com", "Mật khẩu phải chứa ít nhất một chữ hoa"),
    ("abc", "tester", "TTTT111@", "test@gmail.com", "Mật khẩu phải chứa ít nhất một chữ thường"),
    ("abc", "tester", "aBc@1234", "test.com" , "Email không hợp lệ"),
    ("abc", "tester", "aBc@1234", "test@com", "Email không hợp lệ"),
    ("abc", "tester", "aBc@1234", "test@", "Email không hợp lệ"),
    ("abc", "tester", "aBc@1234", "@gmail.com", "Email không hợp lệ"),
])
def test_input_validations(test_session, name, username, password, email, msg):
    with pytest.raises((ValueError, AttributeError, TypeError), match=re.escape(msg) if msg else None):
        add_user(name=name, username=username, password=password, avatar=None, email=email)
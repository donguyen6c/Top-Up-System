from eapp.models import Product
from eapp.dao import load_products
from .base import test_app, test_session
import pytest

@pytest.fixture
def sample_products(test_session):
    p1 = Product(name="Thẻ Viettel 10k", price=10000, inventory=6, category_id=1)
    p2 = Product(name="Thẻ Mobifone 50k", price=50000, inventory=5, category_id=2)
    p3 = Product(name="Thẻ Vinaphone 100k", price=100000, inventory=15, category_id=3)
    p4 = Product(name="Thẻ Garena 500k", price=500000, inventory=12, category_id=4)
    p5 = Product(name="Thẻ Zing 200k", price=200000, inventory=7, category_id=5)

    test_session.add_all([p1, p2, p3, p4, p5])
    test_session.commit()
    return [p1, p2, p3, p4, p5]

def test_all(sample_products):
    actual_products = load_products()
    assert len(actual_products) == len(sample_products)

def test_keywords(sample_products):
    actual_products = load_products(kw="Zing")
    assert len(actual_products) == 1
    assert all("Zing" in p.name for p in actual_products)

def test_category(sample_products):
    actual_products = load_products(cate_id=1)
    assert len(actual_products) == 1
    assert all(p.category_id == 1 for p in actual_products)
    assert ("Zing" in p.name for p in actual_products)

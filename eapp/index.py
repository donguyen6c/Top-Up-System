from flask import render_template, request, redirect, jsonify, session
from flask_login import login_user, logout_user, current_user

from eapp import app, login, dao, utils
from eapp.dao import add_user
from eapp.models import CardType, Product
import traceback
import re

from eapp.observers import PaymentSubject, EmailNotificationObserver


@app.route('/')
def index():
    categories = dao.load_categories()
    products = dao.load_products()

    phone_categories = [c for c in categories if c.card_type == CardType.PHONE]
    game_categories = [c for c in categories if c.card_type == CardType.GAME]

    return render_template('index.html',
                           phone_categories=phone_categories,
                           game_categories=game_categories,
                           products=products)

@app.route('/login')
def login_view():
    return render_template('login.html')

@app.route('/login', methods=['post'])
def login_process():
    username = request.form.get('username')
    password = request.form.get('password')

    user = dao.auth_user(username=username, password=password)
    if user:
        login_user(user=user)

    next = request.args.get('next')
    return redirect(next if next else '/')

@app.route('/register')
def register_view():
    return render_template('register.html')

@app.route('/register', methods=['post'])
def register_process():
    data = request.form

    password = data.get('password')
    confirm = data.get('confirm')
    if password != confirm:
        err_msg = 'Mật khẩu không khớp!'
        return render_template('register.html', err_msg=err_msg)

    email = data.get('email')
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

    if not email or not re.match(email_regex, email):
        err_msg = 'Email không đúng định dạng!'
        return render_template('register.html', err_msg=err_msg)
    try:
        add_user(name=data.get('name'), username=data.get('username'), password=password, avatar=request.files.get('avatar'), email=data.get('email'))
        return redirect('/login')
    except Exception as ex:
        return render_template('register.html', err_msg=str(ex))

@app.route('/logout')
def logout_process():
    logout_user()
    return redirect('/login')

@app.route('/cart')
def cart_view():
    cart = session.get('cart', {})

    cart_stats = utils.stats_cart(cart)

    return render_template('cart.html', cart_stats=cart_stats)

@app.route('/api/carts', methods=['post'])
def add_to_cart():
    cart = session.get('cart')
    if not cart:
        cart = {}

    data = request.json
    product_id = str(data.get('id'))
    name = data.get('name')
    price = float(data.get('price'))
    card_type = data.get('card_type')
    added_qty = int(data.get('quantity', 1))

    def get_tier_limit(p):
        if p <= 30000: return 10
        elif p <= 300000: return 5
        else: return 3

    current_tier_limit = get_tier_limit(price)

    qty_in_same_tier = 0
    for item in cart.values():
        if get_tier_limit(item['price']) == current_tier_limit:
            if item['id'] != product_id:
                qty_in_same_tier += item['quantity']

    current_product_qty = cart[product_id]['quantity'] if product_id in cart else 0
    new_product_qty = current_product_qty + added_qty
    new_total_tier_qty = qty_in_same_tier + new_product_qty

    if new_total_tier_qty > current_tier_limit:
        return jsonify({
            "status": "error",
            "message": f"Hệ thống chỉ cho phép mua tối đa {current_tier_limit} thẻ thuộc mệnh giá {price:,.0f}đ/đơn. Giỏ hàng của bạn đang có {qty_in_same_tier + current_product_qty} thẻ nhóm này!"
        }), 400

    product = Product.query.get(product_id)
    if not product or new_product_qty > product.inventory:
        return jsonify({
            "status": "error",
            "message": f"Kho chỉ còn {product.inventory if product else 0} mã thẻ loại này!"
        }), 400

    if product_id in cart:
        cart[product_id]["quantity"] += added_qty
    else:
        cart[product_id] = {
            "id": product_id,
            "name": name,
            "price": price,
            "card_type": card_type,
            "quantity": added_qty
        }

    session['cart'] = cart

    stats = utils.stats_cart(cart)
    return jsonify({
        "status": "success",
        "message": f"Đã thêm vào giỏ! (Nhóm này đang có {new_total_tier_qty}/{current_tier_limit} thẻ)",
        "total_quantity": stats.get('total_quantity', 0)
    })


@app.route('/api/carts/<id>', methods=['put'])
def update_to_cart(id):
    cart = session.get('cart')

    if cart and id in cart:
        new_qty = int(request.json.get("quantity"))
        price = cart[id]['price']

        def get_tier_limit(p):
            if p <= 30000:
                return 10
            elif p <= 300000:
                return 5
            else:
                return 3

        current_tier_limit = get_tier_limit(price)

        qty_in_same_tier = 0
        for item in cart.values():
            if get_tier_limit(item['price']) == current_tier_limit:
                if item['id'] != id:
                    qty_in_same_tier += item['quantity']

        if (qty_in_same_tier + new_qty) > current_tier_limit:
            return jsonify({
                "status": "error",
                "message": f"Hệ thống chỉ cho phép mua tối đa {current_tier_limit} thẻ nhóm giá {price:,.0f}đ/đơn!"
            }), 400

        product = Product.query.get(id)
        if not product or new_qty > product.inventory:
            return jsonify({
                "status": "error",
                "message": f"Kho chỉ còn {product.inventory if product else 0} mã thẻ!"
            }), 400

        cart[id]["quantity"] = new_qty
        session['cart'] = cart

        stats = utils.stats_cart(cart)
        return jsonify({
            "status": "success",
            "total_quantity": stats['total_quantity'],
            "total_amount": stats['total_amount']
        })

    return jsonify({"status": "error", "message": "Sản phẩm không tồn tại trong giỏ"}), 404

@app.route('/api/carts/<id>', methods=['delete'])
def delete_to_cart(id):
    cart = session.get('cart')

    if cart and id in cart:
        del cart[id]
        session['cart'] = cart

    stats = utils.stats_cart(cart)
    return jsonify({
        "status": "success",
        "total_quantity": stats['total_quantity'],
        "total_amount": stats['total_amount']
    })

@app.route('/checkout')
def checkout_view():
    if not current_user.is_authenticated:
        return redirect('/login?next=/checkout')

    cart = session.get('cart', {})

    if not cart:
        return redirect('/cart')

    session.pop('discount_code', None)
    session.pop('discount_amount', None)

    cart_stats = utils.stats_cart(cart)
    return render_template('checkout.html', cart_stats=cart_stats)

@app.route('/api/apply-discount', methods=['POST'])
def apply_discount_api():
    if not current_user.is_authenticated:
        return jsonify({"status": "error", "message": "Bạn chưa đăng nhập!"}), 401

    code = request.json.get('code')
    cart = session.get('cart', {})

    res = dao.check_discount(code, cart)

    if res['success']:
        session['discount_code'] = code
        session['discount_amount'] = res['discount_amount']
        return jsonify({
            "status": "success",
            "message": res['message'],
            "discount_amount": res['discount_amount']
        })
    else:
        session.pop('discount_code', None)
        session.pop('discount_amount', None)
        return jsonify({
            "status": "error",
            "message": res['message'],
            "discount_amount": 0
        }), 400

payment_subject = PaymentSubject()
payment_subject.attach(EmailNotificationObserver())


@app.route('/api/pay', methods=['POST'])
def pay_process():
    if not current_user.is_authenticated:
        return jsonify({"status": "error", "message": "Bạn chưa đăng nhập!"}), 401

    cart = session.get('cart')
    if not cart:
        return jsonify({"status": "error", "message": "Giỏ hàng của bạn đang trống!"}), 400

    data = request.json
    payment_method = data.get('payment_method', 'momo')

    stats = utils.stats_cart(cart)
    total_amount = stats.get('total_amount', 0)
    discount_amount = session.get('discount_amount', 0)
    discount_code = session.get('discount_code')

    final_amount = total_amount - discount_amount
    if final_amount < 0: final_amount = 0

    try:
        dao.add_receipt(
            user_id=current_user.id,
            cart=cart,
            discount_code=discount_code
        )

        payment_subject.notify(
            user_id=current_user.id,
            cart=cart,
            final_amount=final_amount,
            payment_method=payment_method
        )

        session.pop('cart', None)
        session.pop('discount_code', None)
        session.pop('discount_amount', None)

        return jsonify({"status": "success", "message": "Thanh toán thành công! Mã giao dịch đã được gửi vào Email."})

    except Exception as ex:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(ex)}), 500


@app.route('/history')
def history_view():
    if not current_user.is_authenticated:
        return redirect('/login?next=/history')

    receipts = dao.get_receipts_by_user(current_user.id)

    return render_template('history.html', receipts=receipts)


@app.route('/inventory')
def inventory_view():
    if not current_user.is_authenticated:
        return redirect('/login?next=/inventory')

    cards = dao.get_cards_by_user(current_user.id)

    return render_template('inventory.html', cards=cards)

@app.context_processor
def common_response():
    cart = session.get('cart', {})
    cart_stats = utils.stats_cart(cart)
    return {
        'cart_stats': cart_stats
    }

@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)

if __name__ == '__main__':
    app.run(debug=True)
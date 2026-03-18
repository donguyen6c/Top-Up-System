from flask import render_template, request, redirect, jsonify, session
from flask_login import login_user, logout_user

from eapp import app, login, dao, utils
from eapp.dao import add_user
from eapp.models import CardType, Product
import re


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

@app.route('/api/carts', methods=['post'])
def add_to_cart():
    cart = session.get('cart')
    if not cart:
        cart = {}

    data = request.json
    product_id = str(data.get('id'))
    name = data.get('name')
    price = float(data.get('price'))
    added_qty = int(data.get('quantity', 1))

    def get_tier_limit(p):
        if p <= 30000: return 10 #10,20
        elif p <= 300000: return 5 #50 100 200
        else: return 3

    current_tier_limit = get_tier_limit(price)

    # 2. Đếm TỔNG số lượng thẻ ĐÃ CÓ TRONG GIỎ thuộc CÙNG nhóm giá này
    qty_in_same_tier = 0
    for item in cart.values():
        if get_tier_limit(item['price']) == current_tier_limit:
            # Không đếm sản phẩm đang được add (vì sẽ cộng riêng ở dưới)
            if item['id'] != product_id:
                qty_in_same_tier += item['quantity']

    # 3. Tính tổng số lượng nếu thêm thành công
    current_product_qty = cart[product_id]['quantity'] if product_id in cart else 0
    new_product_qty = current_product_qty + added_qty
    new_total_tier_qty = qty_in_same_tier + new_product_qty

    # --- KIỂM TRA 1: ĐỊNH MỨC THEO NHÓM GIÁ ---
    if new_total_tier_qty > current_tier_limit:
        return jsonify({
            "status": "error",
            "message": f"Hệ thống chỉ cho phép mua tối đa {current_tier_limit} thẻ thuộc mệnh giá {price:,.0f}đ/đơn. Giỏ hàng của bạn đang có {qty_in_same_tier + current_product_qty} thẻ nhóm này!"
        }), 400

    # --- KIỂM TRA 2: TỒN KHO THỰC TẾ TRONG DATABASE ---
    product = Product.query.get(product_id)
    if not product or new_product_qty > product.inventory:
        return jsonify({
            "status": "error",
            "message": f"Kho chỉ còn {product.inventory if product else 0} mã thẻ loại này!"
        }), 400

    # --- QUA ĐƯỢC KIỂM TRA -> THÊM VÀO GIỎ ---
    if product_id in cart:
        cart[product_id]["quantity"] += added_qty
    else:
        cart[product_id] = {
            "id": product_id,
            "name": name,
            "price": price,
            "quantity": added_qty
        }

    session['cart'] = cart

    stats = utils.stats_cart(cart)
    return jsonify({
        "status": "success",
        "message": f"Đã thêm vào giỏ! (Nhóm này đang có {new_total_tier_qty}/{current_tier_limit} thẻ)",
        "total_quantity": stats.get('total_quantity', 0)
    })

@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)

if __name__ == '__main__':
    app.run(debug=True)
from flask import render_template, request
from eapp import app, login, dao
from eapp.models import CardType


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

@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)

if __name__ == '__main__':
    app.run(debug=True)
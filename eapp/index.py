from flask import render_template
from eapp import app, login, dao

@app.route('/')
def index():
    return render_template('index.html')

@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)

if __name__ == '__main__':
    app.run(debug=True)
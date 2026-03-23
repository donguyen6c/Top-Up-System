from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect
from eapp.models import Category, Product, Card, User, Receipt, Discount, Banner, UserRole
from eapp import app, db
import eapp.dao as dao


class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class CardView(AdminModelView):
    column_list = ['product', 'serial_number', 'pin_code', 'expiry_date', 'is_sold']
    column_searchable_list = ['serial_number', 'pin_code']
    column_filters = ['is_sold', 'expiry_date']
    page_size = 50

    column_labels = {
        'product': 'Tên sản phẩm',
        'serial_number': 'Số Serial',
        'pin_code': 'Mã PIN',
        'expiry_date': 'Hạn sử dụng',
        'is_sold': 'Trạng thái bán'
    }

    column_formatters = {
        'is_sold': lambda v, c, m, p: "Đã bán" if m.is_sold else "Chưa bán"
    }

    def on_model_change(self, form, model, is_created):
        if is_created and not model.is_sold:
            model.product.inventory += 1

    def on_model_delete(self, model):
        if not model.is_sold:
            model.product.inventory -= 1

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html', cate_stats=dao.count_product_by_cate())

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

class StatsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/stats.html',
                           revenue_products=dao.revenue_by_product(),
                           revenue_times=dao.revenue_by_time("month"))

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/login')

    def is_accessible(self):
        return current_user.is_authenticated


# Khởi tạo Admin (dùng giao diện bootstrap4 cho hiện đại)
admin = Admin(app=app, name="Quản Trị Bán Thẻ", index_view=MyAdminIndexView())

# Thêm các bảng vào Menu
admin.add_view(AdminModelView(Category, db.session, name="Nhà mạng"))
admin.add_view(AdminModelView(Product, db.session, name="Mệnh giá thẻ"))
admin.add_view(CardView(Card, db.session, name="Kho thẻ"))
admin.add_view(AdminModelView(Discount, db.session, name="Khuyến mãi"))
admin.add_view(AdminModelView(Banner, db.session, name="Banner"))
admin.add_view(AdminModelView(Receipt, db.session, name="Lịch sử Hóa đơn"))
admin.add_view(AdminModelView(User, db.session, name="Tài khoản"))
admin.add_view(StatsView(name='Thống kê & Báo cáo'))
admin.add_view(LogoutView(name='Đăng xuất'))
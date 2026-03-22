import threading
from flask_mail import Message
from eapp import app, mail
from eapp.models import User


class PaymentSubject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def notify(self, user_id, cart, final_amount, payment_method):
        for observer in self._observers:
            observer.update(user_id, cart, final_amount, payment_method)


class Observer:
    def update(self, user_id, cart, final_amount, payment_method):
        pass


class EmailNotificationObserver(Observer):
    def update(self, user_id, cart, final_amount, payment_method):
        # Tạo luồng (thread) mới để gửi email chạy ngầm
        thread = threading.Thread(
            target=self.send_mail,
            kwargs={
                'user_id': user_id,
                'cart': cart,
                'final_amount': final_amount,
                'payment_method': payment_method
            }
        )
        thread.start()

    def send_mail(self, user_id, cart, final_amount, payment_method):
        # Bắt buộc phải có app_context() vì đang chạy ở Thread phụ
        with app.app_context():
            user = User.query.get(user_id)
            if not user or not user.email:
                return  # Tránh lỗi nếu user không có email

            msg = Message("Xác nhận thanh toán thành công - CaoThe Website", recipients=[user.email])

            # --- TẠO NỘI DUNG HTML CHO EMAIL ---
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
                <div style="background-color: #28a745; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0;">CẢM ƠN BẠN ĐÃ MUA HÀNG!</h2>
                </div>
                <div style="padding: 20px;">
                    <p>Chào <strong>{user.name}</strong>,</p>
                    <p>Đơn hàng của bạn đã được thanh toán thành công qua <strong>{'Ví MoMo' if payment_method == 'momo' else 'Ngân hàng'}</strong>.</p>

                    <h3 style="border-bottom: 2px solid #eee; padding-bottom: 10px;">Chi tiết thẻ đã mua:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Mệnh giá thẻ</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Số lượng</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Thành tiền</th>
                        </tr>
            """

            for item in cart.values():
                item_total = item['price'] * item['quantity']
                html_content += f"""
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;">{item['name']}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{item['quantity']}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{item_total:,.0f} đ</td>
                        </tr>
                """

            html_content += f"""
                    </table>
                    <h3 style="text-align: right; color: #dc3545; margin-top: 20px;">
                        Tổng thanh toán: {final_amount:,.0f} VNĐ
                    </h3>
                    <p style="color: #6c757d; font-size: 14px; margin-top: 30px;">
                        Mã thẻ (Số seri & Mã nạp) đã được cập nhật. Bạn có thể xem ngay trong mục Lịch sử mua hàng trên website.<br>
                        Nếu có thắc mắc, vui lòng liên hệ Zalo CSKH.
                    </p>
                </div>
            </div>
            """
            msg.html = html_content

            # Thực thi gửi email
            mail.send(msg)